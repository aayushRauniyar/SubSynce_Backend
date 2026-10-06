from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from ops.tests.helpers import PASSWORD, login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork


class LoginTests(TestCase):
    def test_next_param_cannot_redirect_off_site(self):
        user = make_user("ADMINISTRATOR")
        resp = self.client.post("/?next=https://evil.example/", {"username": user.username, "password": PASSWORD})
        self.assertRedirects(resp, reverse("ops:dashboard"))

    def test_next_param_keeps_local_paths(self):
        user = make_user("ADMINISTRATOR")
        resp = self.client.post("/?next=/completions/", {"username": user.username, "password": PASSWORD})
        self.assertRedirects(resp, "/completions/")


class DashboardTests(TestCase):
    def setUp(self):
        self.owner = make_user("OWNER")
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR")
        self.site = make_site(contractor=self.alex)
        done = make_schedule(self.site, self.admin, day=date.today() - timedelta(days=1))
        CompleteWork.objects.create(schedule=done, completed_by=self.alex, status="COMPLETED")
        make_schedule(self.site, self.admin)
        ClientInvoice.objects.create(
            invoice_number="C-1", site=self.site, client=self.site.client_id, invoice_date=date.today(),
            service_period_start=date.today(), service_period_end=date.today(),
            amount=Decimal("1800.00"), status="PAID", created_by=self.admin,
        )
        ContractorInvoice.objects.create(
            invoice_number="INV-1", site=self.site, invoice_date=date.today(),
            service_period_start=date.today(), service_period_end=date.today(),
            amount=Decimal("1280.00"), status="APPROVED", created_by=self.alex,
        )

    def test_staff_dashboard_shows_real_figures(self):
        for user in (self.admin, self.owner):
            login(self.client, user)
            resp = self.client.get(reverse("ops:dashboard"))
            self.assertEqual(resp.status_code, 200)
            s = resp.context["summary"]
            self.assertEqual(s["revenue"], Decimal("1800.00"))
            self.assertEqual(s["cost"], Decimal("1280.00"))
            self.assertEqual(s["profit"], Decimal("520.00"))
            self.assertEqual(s["services"]["completed"], 1)
            self.assertEqual(s["services"]["scheduled"], 1)
            self.assertContains(resp, "$520.00")

    def test_date_range_filters_money(self):
        login(self.client, self.admin)
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = self.client.get(reverse("ops:dashboard"), {"start": future})
        self.assertEqual(resp.context["summary"]["revenue"], Decimal("0.00"))

    def test_bad_range_is_reported(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:dashboard"), {"start": "2026-10-10", "end": "2026-10-01"})
        self.assertContains(resp, "Start date must be on or before the end date.")

    def test_contractor_gets_own_dashboard(self):
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:dashboard"))
        self.assertTemplateUsed(resp, "ops/dashboard_contractor.html")
        self.assertEqual(resp.context["summary"]["earnings"], Decimal("1280.00"))
        self.assertNotIn("revenue", resp.context["summary"])

    def test_anonymous_redirects_to_login(self):
        resp = self.client.get(reverse("ops:dashboard"))
        self.assertEqual(resp.status_code, 302)


class ClientAccessTests(TestCase):
    def test_owner_can_open_clients(self):
        login(self.client, make_user("OWNER"))
        self.assertEqual(self.client.get(reverse("ops:clients")).status_code, 200)

    def test_client_pages_use_shared_app_shell(self):
        login(self.client, make_user("OWNER"))
        for name in ("ops:clients", "ops:client_create"):
            resp = self.client.get(reverse(name))
            self.assertTemplateUsed(resp, "ops/layouts/app.html")
            self.assertContains(resp, "Work Completions")
            self.assertNotContains(resp, "<span>Help</span>", html=False)

    def test_reusing_deleted_clients_phone_shows_error_not_500(self):
        login(self.client, make_user("ADMINISTRATOR"))
        data = {"first_name": "Tech", "phone": "0400111222", "email": "a@x.com", "role": "ADMINISTRATOR", "status": "ACTIVE"}
        self.client.post(reverse("ops:client_create"), data)
        from client.model.clientmanage import Client
        Client.objects.get(phone="0400111222").delete()
        resp = self.client.post(reverse("ops:client_create"), {**data, "email": "b@x.com"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "removed client")
