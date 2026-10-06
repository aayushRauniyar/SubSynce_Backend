"""Read-only figures for the web frontend.

These mirror the backend's own calculations (dashboard/api/views) so the web
screens and the API agree. Nothing here writes to the database.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

from authuser.model.user import User
from client.model.clientmanage import Client, Site
from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from schedule.model.cleaningschedule import ServiceSchedule
from work.model.workcomplete import CompleteWork

ZERO = Decimal("0.00")


def _total(queryset):
    return queryset.aggregate(total=Sum("amount"))["total"] or ZERO


def parse_date(value):
    """ISO date string -> date, or None when blank/invalid."""
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def admin_summary(start=None, end=None):
    """Counts and money for the staff dashboard, optionally within a date range."""
    schedules = ServiceSchedule.objects.all()
    work = CompleteWork.objects.all()
    contractor_invoices = ContractorInvoice.objects.all()
    client_invoices = ClientInvoice.objects.all()

    if start:
        schedules = schedules.filter(scheduled_date__gte=start)
        work = work.filter(schedule__scheduled_date__gte=start)
        contractor_invoices = contractor_invoices.filter(invoice_date__gte=start)
        client_invoices = client_invoices.filter(invoice_date__gte=start)
    if end:
        schedules = schedules.filter(scheduled_date__lte=end)
        work = work.filter(schedule__scheduled_date__lte=end)
        contractor_invoices = contractor_invoices.filter(invoice_date__lte=end)
        client_invoices = client_invoices.filter(invoice_date__lte=end)

    revenue = _total(client_invoices.filter(status="PAID"))
    cost = _total(contractor_invoices.filter(status="APPROVED"))
    services_total = schedules.count()
    completed = work.filter(status="COMPLETED").count()

    return {
        "clients": Client.objects.count(),
        "sites": Site.objects.count(),
        "contractors": User.objects.filter(role="CONTRACTOR").count(),
        "services": {
            "total": services_total,
            # Clock-out doesn't change the schedule's own status, so a job
            # counts as "scheduled" only while it has no work record yet.
            "scheduled": schedules.filter(status="SCHEDULED", work_completion__isnull=True).count(),
            "completed": completed,
            "in_progress": work.filter(status="IN_PROGRESS").count(),
            "missed": schedules.filter(status="MISSED").count() + work.filter(status="MISSED").exclude(schedule__status="MISSED").count(),
            "cancelled": schedules.filter(status="CANCELLED").count(),
            "completion_rate": (completed / services_total) if services_total else None,
        },
        "contractor_invoices": {
            "pending": contractor_invoices.filter(status="PENDING").count(),
            "approved": contractor_invoices.filter(status="APPROVED").count(),
            "rejected": contractor_invoices.filter(status="REJECTED").count(),
        },
        "client_invoices": {
            "issued": client_invoices.filter(status="ISSUED").count(),
            "paid": client_invoices.filter(status="PAID").count(),
            "overdue": client_invoices.filter(status="OVERDUE").count(),
        },
        "revenue": revenue,
        "cost": cost,
        "profit": revenue - cost,
        "margin": ((revenue - cost) / revenue) if revenue else None,
    }


def job_status(schedule):
    """What a job's status really is: its work record wins over the schedule's own status."""
    work = getattr(schedule, "work_completion", None)
    if schedule.status in ("MISSED", "CANCELLED"):
        return schedule.status
    return work.status if work else schedule.status


def todays_schedule(day=None):
    day = day or date.today()
    return (
        ServiceSchedule.objects.filter(scheduled_date=day)
        .select_related("site", "site__assigned_contractor", "work_completion")
        .order_by("scheduled_time")
    )


def contractor_jobs(user):
    """Schedules on sites assigned to this contractor."""
    return ServiceSchedule.objects.filter(site__assigned_contractor=user).select_related("site")


def contractor_summary(user, today=None):
    today = today or date.today()
    jobs = contractor_jobs(user)
    work = CompleteWork.objects.filter(completed_by=user)
    invoices = ContractorInvoice.objects.filter(created_by=user)
    return {
        "today": jobs.filter(scheduled_date=today).select_related("work_completion").order_by("scheduled_time"),
        "upcoming": jobs.filter(
            scheduled_date__gt=today,
            scheduled_date__lte=today + timedelta(days=14),
            status="SCHEDULED",
        ).order_by("scheduled_date", "scheduled_time")[:10],
        "in_progress": work.filter(status="IN_PROGRESS").select_related("schedule__site"),
        "completed_count": work.filter(status="COMPLETED").count(),
        "sites": Site.objects.filter(assigned_contractor=user).count(),
        "invoices": {
            "pending": invoices.filter(status="PENDING").count(),
            "approved": invoices.filter(status="APPROVED").count(),
            "rejected": invoices.filter(status="REJECTED").count(),
        },
        "earnings": _total(invoices.filter(status="APPROVED")),
    }
