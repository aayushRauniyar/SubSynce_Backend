"""Work completion screens (brief 3.6).

Contractors clock in to a scheduled job, then clock out with notes and
optional photos. Staff see the completion log. Rules mirror the backend's
work API (work/api/views/user_views.py): only the assigned contractor, only
SCHEDULED jobs, one work record per job, times stamped by the server.
"""
from datetime import date

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ops import services
from ops.access import contractor_required, is_staff_user, role_required, staff_required, CONTRACTOR, STAFF_ROLES
from ops.forms import ClockOutForm
from schedule.model.cleaningschedule import ServiceSchedule
from work.model.workcomplete import CompleteWork, WorkCompleteImage


@contractor_required
def my_jobs_view(request):
    today = date.today()
    jobs = services.contractor_jobs(request.user).select_related("work_completion")
    to_do = jobs.filter(status="SCHEDULED", work_completion__isnull=True, scheduled_date__lte=today)
    upcoming = jobs.filter(status="SCHEDULED", work_completion__isnull=True, scheduled_date__gt=today)
    in_progress = CompleteWork.objects.filter(completed_by=request.user, status="IN_PROGRESS").select_related("schedule__site")
    history = Paginator(
        CompleteWork.objects.filter(completed_by=request.user)
        .exclude(status="IN_PROGRESS")
        .select_related("schedule__site")
        .order_by("-check_in_time"),
        10,
    ).get_page(request.GET.get("page"))
    return render(request, "ops/work/my_jobs.html", {
        "today": today,
        "to_do": to_do.order_by("scheduled_date", "scheduled_time"),
        "upcoming": upcoming.order_by("scheduled_date", "scheduled_time")[:20],
        "in_progress": in_progress,
        "history": history,
    })


@contractor_required
@require_POST
def clock_in_view(request, schedule_id):
    schedule = ServiceSchedule.objects.filter(
        id=schedule_id, site__assigned_contractor=request.user, status="SCHEDULED"
    ).first()
    if not schedule:
        messages.error(request, "That job isn't scheduled for you.")
        return redirect("ops:my_jobs")
    if schedule.scheduled_date > date.today():
        messages.error(request, "You can only clock in on or after the scheduled day.")
        return redirect("ops:my_jobs")
    if CompleteWork.objects.filter(schedule=schedule).exists():
        messages.error(request, "Work has already been started for this job.")
        return redirect("ops:my_jobs")

    work = CompleteWork.objects.create(
        schedule=schedule,
        completed_by=request.user,
        check_in_time=timezone.now(),
        status="IN_PROGRESS",
        location=request.POST.get("location", "").strip()[:255] or None,
    )
    messages.success(request, f"Clocked in at {schedule.site.name}.")
    return redirect("ops:clock_out", work_id=work.id)


@contractor_required
def clock_out_view(request, work_id):
    work = get_object_or_404(
        CompleteWork.objects.select_related("schedule__site"),
        id=work_id, completed_by=request.user,
    )
    if work.check_out_time:
        messages.info(request, "This job is already clocked out.")
        return redirect("ops:work_detail", work_id=work.id)

    if request.method == "POST":
        form = ClockOutForm(request.POST, photos=request.FILES.getlist("photos"))
        if form.is_valid():
            with transaction.atomic():
                work.completion_notes = form.cleaned_data["completion_notes"] or None
                if form.cleaned_data["location"]:
                    work.location = form.cleaned_data["location"]
                work.check_out_time = timezone.now()
                work.status = "COMPLETED"
                work.save()
                for photo in form.photos:
                    WorkCompleteImage.objects.create(work_completion=work, evidence_photo=photo)
            messages.success(request, f"Job at {work.schedule.site.name} marked complete.")
            return redirect("ops:work_detail", work_id=work.id)
    else:
        form = ClockOutForm(initial={"location": work.location})

    return render(request, "ops/work/clock_out.html", {"work": work, "form": form})


@role_required(CONTRACTOR, *STAFF_ROLES)
def work_detail_view(request, work_id):
    work = get_object_or_404(
        CompleteWork.objects.select_related("schedule__site__client_id", "completed_by")
        .prefetch_related("work_completion_images"),
        id=work_id,
    )
    if not is_staff_user(request.user) and work.completed_by_id != request.user.id:
        raise Http404
    duration = None
    if work.check_in_time and work.check_out_time:
        duration = work.check_out_time - work.check_in_time
    return render(request, "ops/work/detail.html", {"work": work, "duration": duration})


@staff_required
def completions_view(request):
    records = CompleteWork.objects.select_related("schedule__site", "completed_by").order_by("-check_in_time")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    start = services.parse_date(request.GET.get("start"))
    end = services.parse_date(request.GET.get("end"))
    if status in ("IN_PROGRESS", "COMPLETED", "MISSED"):
        records = records.filter(status=status)
    if query:
        records = records.filter(
            Q(schedule__site__name__icontains=query)
            | Q(completed_by__username__icontains=query)
            | Q(completion_notes__icontains=query)
        )
    if start:
        records = records.filter(schedule__scheduled_date__gte=start)
    if end:
        records = records.filter(schedule__scheduled_date__lte=end)

    page = Paginator(records, 15).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "ops/work/completions.html", {
        "page_obj": page,
        "status": status,
        "query": query,
        "start": start,
        "end": end,
        "querystring": params.urlencode(),
    })
