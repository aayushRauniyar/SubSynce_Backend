"""Frontend-owned data that the backend has no place for yet.

The backend's ContractorInvoice stores one total amount. The invoice builder
keeps its line items, notes and payment terms here, linked to that invoice,
and always writes the sum of the line items back into ContractorInvoice.amount
so the backend's reports and API stay correct.
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from invoice.model.invoicemanagement import ContractorInvoice


class InvoiceExtra(models.Model):
    invoice = models.OneToOneField(ContractorInvoice, on_delete=models.CASCADE, related_name="builder")
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Builder data for {self.invoice.invoice_number}"


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(ContractorInvoice, on_delete=models.CASCADE, related_name="line_items")
    position = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        ordering = ["position", "id"]

    @property
    def total(self):
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"


class CompanyProfile(models.Model):
    """Single row: business details printed on invoices. The logo is the fixed SubSync logo."""

    name = models.CharField(max_length=120, default="SubSync")
    abn = models.CharField("ABN", max_length=30, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    default_terms = models.TextField(blank=True, default="Payment within 14 days.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def load(cls):
        profile, _ = cls.objects.get_or_create(pk=1)
        return profile

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
