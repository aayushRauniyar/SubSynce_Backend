from datetime import date as _date
from decimal import Decimal

from django import forms

from client.model.clientmanage import Client, Site
from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from ops.models import CompanyProfile

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



# --- Invoice builder ---------------------------------------------------------

class BaseInvoiceHeaderForm(forms.Form):
    """Number, site, dates, notes and terms shared by both invoice builders."""

    model = None  # the backend invoice model whose numbers must stay unique

    invoice_number = forms.CharField(max_length=40)
    site = forms.ModelChoiceField(queryset=Site.objects.none(), empty_label="Choose a site…")
    invoice_date = forms.DateField(initial=_date.today)
    service_period_start = forms.DateField()
    service_period_end = forms.DateField()
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)
    terms = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance

    def clean_invoice_number(self):
        number = self.cleaned_data["invoice_number"].strip()
        taken = self.model.global_objects.filter(invoice_number__iexact=number)
        if self.instance is not None:
            taken = taken.exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError("This invoice number is already used.")
        return number

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("service_period_start"), cleaned.get("service_period_end")
        if start and end and start > end:
            self.add_error("service_period_end", "The period must end on or after its start date.")
        return cleaned

    @classmethod
    def initial_for_new(cls, number):
        today = _date.today()
        return {
            "invoice_number": number,
            "invoice_date": today,
            "service_period_start": today.replace(day=1),
            "service_period_end": today,
            "terms": CompanyProfile.load().default_terms,
        }


class InvoiceHeaderForm(BaseInvoiceHeaderForm):
    model = ContractorInvoice

    def __init__(self, *args, contractor, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["site"].queryset = Site.objects.filter(assigned_contractor=contractor).order_by("name")
        self.fields["site"].label_from_instance = lambda site: f"{site.name} · {site.address}"


class ClientInvoiceForm(BaseInvoiceHeaderForm):
    """Invoice the company sends to a client. The client always comes from the chosen site."""

    model = ClientInvoice

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["site"].queryset = Site.objects.select_related("client_id").order_by("name")
        self.fields["site"].label_from_instance = lambda site: f"{site.name} · {client_name(site.client_id)}"


def client_name(client):
    return " ".join(part for part in (client.first_name, client.last_name) if part)


class LineItemForm(forms.Form):
    description = forms.CharField(max_length=200)
    quantity = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"), initial=1)
    unit_price = forms.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"))


class BaseLineItemFormSet(forms.BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        rows = [f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if not rows:
            raise forms.ValidationError("Add at least one line item.")
        total = sum(f.cleaned_data["quantity"] * f.cleaned_data["unit_price"] for f in rows)
        if total <= 0:
            raise forms.ValidationError("The invoice total must be more than $0.00.")
        if total >= Decimal("100000000"):
            raise forms.ValidationError("The invoice total is too large.")


LineItemFormSet = forms.formset_factory(
    LineItemForm, formset=BaseLineItemFormSet, extra=0, min_num=1, can_delete=True, max_num=50
)


class DecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=[("APPROVED", "Approve"), ("REJECTED", "Reject")])
    verification_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision") == "REJECTED" and not cleaned.get("verification_notes", "").strip():
            self.add_error("verification_notes", "Give a reason so the contractor knows what to fix.")
        return cleaned


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = ["name", "abn", "phone", "email", "address", "default_terms"]
        widgets = {"default_terms": forms.Textarea(attrs={"rows": 3})}
