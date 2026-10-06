from django import forms

from client.model.clientmanage import Client

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
        ]

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo or not hasattr(photo, "content_type"):
            return photo

        if photo.content_type not in ALLOWED_PHOTO_CONTENT_TYPES:
            raise forms.ValidationError("Photo must be a JPG or PNG image.")
        if photo.size > MAX_PHOTO_SIZE_BYTES:
            raise forms.ValidationError("Photo must be 5MB or smaller.")

        return photo


MAX_EVIDENCE_PHOTOS = 5


class ClockOutForm(forms.Form):
    """Finish a job: notes, where it was done, and optional photo evidence."""

    completion_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 4}), max_length=2000
    )
    location = forms.CharField(required=False, max_length=255)

    def __init__(self, *args, photos=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.photos = photos or []

    def clean(self):
        cleaned = super().clean()
        if len(self.photos) > MAX_EVIDENCE_PHOTOS:
            raise forms.ValidationError(f"Upload up to {MAX_EVIDENCE_PHOTOS} photos.")
        for photo in self.photos:
            if getattr(photo, "content_type", None) not in ALLOWED_PHOTO_CONTENT_TYPES:
                raise forms.ValidationError(f"{photo.name}: photos must be JPG or PNG.")
            if photo.size > MAX_PHOTO_SIZE_BYTES:
                raise forms.ValidationError(f"{photo.name}: photos must be 5MB or smaller.")
        return cleaned
