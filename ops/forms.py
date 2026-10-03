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
