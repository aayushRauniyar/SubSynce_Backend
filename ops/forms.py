from django import forms
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password

from authuser.model.user import User, UserDetail
from client.model.clientmanage import Client, Site
from schedule.model.cleaningschedule import ServiceSchedule

MAX_PHOTO_SIZE_BYTES = 5 * 1024 * 1024  # 5MB, matches the "JPG, PNG up to 5MB" hint
ALLOWED_PHOTO_CONTENT_TYPES = {"image/jpeg", "image/png"}


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "first_name",
            "last_name",
            "phone",
            "email",
            "photo",
            "role",
            "status",
            "assigned_sites",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_sites"].queryset = Site.objects.select_related("client_id").order_by("name")

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo or not hasattr(photo, "content_type"):
            return photo

        if photo.content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
            raise forms.ValidationError("Photo must be a JPG or PNG image.")
        if photo.size > MAX_PHOTO_SIZE_BYTES:
            raise forms.ValidationError("Photo must be 5MB or smaller.")

        return photo



class ClientCreateForm(ClientForm):
    """
    Add Client page form: one "Full name" input instead of first/last name,
    assigned sites, and no visible role (new clients keep the ADMINISTRATOR
    role the old page created them with, so the Edit Client modal still validates).
    """

    full_name = forms.CharField(max_length=511)

    class Meta(ClientForm.Meta):
        fields = ["phone", "email", "photo", "status", "assigned_sites"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["phone"].required = True

    def clean_phone(self):
        # Also catch soft-deleted clients, which still hold the unique phone in the DB.
        phone = self.cleaned_data.get("phone")
        if phone and Client.global_objects.filter(phone=phone).exists():
            raise forms.ValidationError("A client with this phone number already exists.")
        return phone

    def clean(self):
        cleaned = super().clean()
        # First word -> first_name, the rest -> last_name (empty for a single word).
        first, _, last = " ".join(cleaned.get("full_name", "").split()).partition(" ")
        if len(first) > 255 or len(last) > 255:
            self.add_error("full_name", "Name is too long.")
        self.instance.first_name = first
        self.instance.last_name = last or None
        self.instance.role = "ADMINISTRATOR"
        return cleaned

class SiteForm(forms.ModelForm):
    """Same fields the admin Site API accepts (minus images)."""

    class Meta:
        model = Site
        fields = [
            "client_id",
            "name",
            "address",
            "cleaning_frequency",
            "price",
            "assigned_contractor",
            "cleaning_instructions",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_contractor"].queryset = User.objects.filter(role="CONTRACTOR", deleted_at__isnull=True)


class OpsPasswordResetForm(PasswordResetForm):
    """
    Django's reset form filters on `is_active`, which this custom User model
    doesn't have as a field. Same lookup without it (soft-deleted users are
    already excluded by the default manager).
    """

    def get_users(self, email):
        users = User._default_manager.filter(email__iexact=email)
        return (u for u in users if u.has_usable_password())


class ScheduleForm(forms.ModelForm):
    """
    Same rules as the admin Schedule API: the site needs an assigned contractor,
    new schedules start as SCHEDULED. Client/subcontractor come from the site.
    Status changes go through ScheduleStatusForm.
    """

    class Meta:
        model = ServiceSchedule
        fields = ["site", "scheduled_date", "scheduled_time", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["site"].queryset = Site.objects.select_related(
            "client_id", "assigned_contractor__user_detail"
        ).order_by("name")

    def clean_site(self):
        site = self.cleaned_data["site"]
        if not site.assigned_contractor_id:
            raise forms.ValidationError("Site does not have an assigned contractor.")
        return site


class ScheduleStatusForm(forms.ModelForm):
    """Status-only change, like the API's ChangeStatusView (the view enforces SCHEDULED-only)."""

    class Meta:
        model = ServiceSchedule
        fields = ["status"]


# Which roles each role may create/edit/delete - same rules as the register APIs
# (OWNER creates ADMINISTRATOR/CONTRACTOR, ADMINISTRATOR creates CONTRACTOR).
MANAGEABLE_ROLES = {"OWNER": ("ADMINISTRATOR", "CONTRACTOR"), "ADMINISTRATOR": ("CONTRACTOR",)}


class UserForm(forms.ModelForm):
    """Auth User plus its UserDetail name. Passwords are only set on create (edits use password reset)."""

    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255, required=False)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "role"]

    def __init__(self, *args, actor, **kwargs):
        super().__init__(*args, **kwargs)
        self.creating = self.instance._state.adding
        self.fields["email"].required = True
        allowed = MANAGEABLE_ROLES.get(actor.role, ())
        self.fields["role"].choices = [(v, l) for v, l in User._meta.get_field("role").choices if v in allowed]
        if not self.creating:
            del self.fields["password1"], self.fields["password2"]
            detail = getattr(self.instance, "user_detail", None)
            if detail:
                self.initial.update(first_name=detail.first_name, last_name=detail.last_name)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("User with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        if self.creating and cleaned.get("password1"):
            if cleaned["password1"] != cleaned.get("password2"):
                self.add_error("password2", "Passwords do not match.")
            else:
                try:
                    validate_password(cleaned["password1"], User(username=cleaned.get("username", ""), email=cleaned.get("email", "")))
                except forms.ValidationError as e:
                    self.add_error("password1", e)
        # A contractor still assigned to sites must stay a contractor.
        if (not self.creating and self.instance.role == "CONTRACTOR" and cleaned.get("role") != "CONTRACTOR"
                and self.instance.contractors.exists()):
            self.add_error("role", "This contractor is assigned to sites. Unassign them before changing the role.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        if self.creating:
            user = User.objects.create_user(data["username"], data["email"], data["password1"], role=data["role"])
        else:
            user = super().save()
        UserDetail.objects.update_or_create(
            user=user, defaults={"first_name": data["first_name"], "last_name": data["last_name"] or None}
        )
        return user


def clean_evidence_photos(files):
    """Validate work evidence photos: real images, 5MB max each."""
    field = forms.ImageField()
    for f in files:
        field.clean(f)
        if f.size > MAX_PHOTO_SIZE_BYTES:
            raise forms.ValidationError("Each photo must be 5MB or smaller.")
    return files
