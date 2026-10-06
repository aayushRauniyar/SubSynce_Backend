"""Company settings: business details and default invoice terms (Owner only)."""
from django.contrib import messages
from django.shortcuts import redirect, render

from ops.access import OWNER, role_required
from ops.forms import CompanyProfileForm
from ops.models import CompanyProfile


@role_required(OWNER)
def company_settings_view(request):
    profile = CompanyProfile.load()
    form = CompanyProfileForm(request.POST or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Company settings saved.")
        return redirect("ops:company_settings")
    return render(request, "ops/settings/company.html", {"form": form, "profile": profile})
