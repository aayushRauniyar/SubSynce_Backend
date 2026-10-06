from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from ops.tests.helpers import login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork

# 1x1 PNG
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


class WorkCompletionTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR")
        self.priya = make_user("CONTRACTOR")
        self.site = make_site(contractor=self.alex)
        self.job = make_schedule(self.site, self.admin)

    def test_contractor_clocks_in_and_out_with_notes_and_photo(self):
        login(self.client, self.alex)
        resp = self.client.post(reverse("ops:clock_in", args=[self.job.id]))
        work = CompleteWork.objects.get(schedule=self.job)
        self.assertRedirects(resp, reverse("ops:clock_out", args=[work.id]))
        self.assertEqual(work.status, "IN_PROGRESS")
        self.assertIsNotNone(work.check_in_time)

        with self.settings(MEDIA_ROOT=self._tmp_media()):
            photo = SimpleUploadedFile("lobby.png", PNG, content_type="image/png")
            resp = self.client.post(
                reverse("ops:clock_out", args=[work.id]),
                {"completion_notes": "Lobby detailed", "photos": [photo]},
            )
        self.assertRedirects(resp, reverse("ops:work_detail", args=[work.id]))
        work.refresh_from_db()
        self.assertEqual(work.status, "COMPLETED")
        self.assertEqual(work.completion_notes, "Lobby detailed")
        self.assertGreater(work.check_out_time, work.check_in_time)
        self.assertEqual(work.work_completion_images.count(), 1)

    def test_clock_out_rejects_non_image_upload(self):
        work = CompleteWork.objects.create(schedule=self.job, completed_by=self.alex, status="IN_PROGRESS")
        login(self.client, self.alex)
        bad = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
        resp = self.client.post(reverse("ops:clock_out", args=[work.id]), {"photos": [bad]})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "photos must be JPG or PNG")
        work.refresh_from_db()
        self.assertEqual(work.status, "IN_PROGRESS")

    def test_cannot_clock_in_to_another_contractors_job(self):
        login(self.client, self.priya)
        self.client.post(reverse("ops:clock_in", args=[self.job.id]))
        self.assertFalse(CompleteWork.objects.exists())

    def test_cannot_clock_in_to_future_job(self):
        future = make_schedule(self.site, self.admin, day=date.today() + timedelta(days=3))
        login(self.client, self.alex)
        self.client.post(reverse("ops:clock_in", args=[future.id]))
        self.assertFalse(CompleteWork.objects.filter(schedule=future).exists())

    def test_cannot_clock_in_twice(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:clock_in", args=[self.job.id]))
        self.client.post(reverse("ops:clock_in", args=[self.job.id]))
        self.assertEqual(CompleteWork.objects.filter(schedule=self.job).count(), 1)

    def test_clock_in_requires_post(self):
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:clock_in", args=[self.job.id]))
        self.assertEqual(resp.status_code, 405)

    def test_contractor_cannot_open_other_contractors_record(self):
        work = CompleteWork.objects.create(schedule=self.job, completed_by=self.alex, status="IN_PROGRESS")
        login(self.client, self.priya)
        self.assertEqual(self.client.get(reverse("ops:work_detail", args=[work.id])).status_code, 404)
        self.assertEqual(self.client.get(reverse("ops:clock_out", args=[work.id])).status_code, 404)

    def test_staff_completion_log_and_filters(self):
        CompleteWork.objects.create(schedule=self.job, completed_by=self.alex, status="COMPLETED")
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:completions"))
        self.assertContains(resp, self.site.name)
        resp = self.client.get(reverse("ops:completions"), {"status": "IN_PROGRESS"})
        self.assertNotContains(resp, self.site.name)

    def test_contractor_cannot_see_completion_log(self):
        login(self.client, self.alex)
        self.assertEqual(self.client.get(reverse("ops:completions")).status_code, 403)

    def test_my_jobs_lists_todays_job_with_clock_in(self):
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:my_jobs"))
        self.assertContains(resp, self.site.name)
        self.assertContains(resp, reverse("ops:clock_in", args=[self.job.id]))

    def _tmp_media(self):
        import tempfile
        path = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, path, True)
        return path
