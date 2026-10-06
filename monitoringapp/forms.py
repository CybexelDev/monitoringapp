from pathlib import Path
from django import forms
from .models import AccountsIncome

class AccountsIncomeForm(forms.ModelForm):
    class Meta:
        model = AccountsIncome
        fields = [
            "date",
            "category",
            "amount",
            "payment_method",
            "description",
            "reference",
            "receipt",
        ]
        labels = {
            "receipt": "Receipt / Proof (PDF, JPG or PNG, up to 5 MB)",
            "date": "Income Date",
            "category": "Category",
            "amount": "Amount (₹)",
            "payment_method": "Payment Method",
            "description": "Description",
            "reference": "Reference (optional)",
        }
        widgets = {
            "receipt": forms.FileInput(attrs={"class": "accounts-input", "accept": ".pdf,.jpg,.jpeg,.png"}),
            "date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "accounts-input"},
            ),
            "category": forms.TextInput(attrs={
                "class": "accounts-input",
                "placeholder": "e.g. Service payment",
                "maxlength": "100",
            }),
            "amount": forms.NumberInput(attrs={
                "class": "accounts-input",
                "placeholder": "0.00",
                "min": "0.01",
                "step": "0.01",
                "inputmode": "decimal",
            }),
            "payment_method": forms.Select(attrs={"class": "accounts-input"}),
            "description": forms.Textarea(attrs={
                "class": "accounts-input",
                "placeholder": "Describe this income entry",
                "rows": 3,
            }),
            "reference": forms.TextInput(attrs={
                "class": "accounts-input",
                "placeholder": "Transaction ID or receipt reference",
                "maxlength": "150",
            }),
        }

    def clean_category(self):
        category = self.cleaned_data.get("category", "").strip()
        if not category:
            raise forms.ValidationError("Enter an income category.")
        return category

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        if not description:
            raise forms.ValidationError("Enter a description for this income.")
        return description

    def clean_reference(self):
        return self.cleaned_data.get("reference", "").strip()

    def clean_receipt(self):
        receipt = self.cleaned_data.get("receipt")
        if not receipt or not hasattr(receipt, "content_type"):
            return receipt
        if receipt.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Receipt must be 5 MB or smaller.")
        suffix = Path(receipt.name).suffix.lower()
        header = receipt.read(8)
        receipt.seek(0)
        valid = ((suffix == ".pdf" and header.startswith(b"%PDF-")) or
                 (suffix in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff")) or
                 (suffix == ".png" and header == b"\x89PNG\r\n\x1a\n"))
        if not valid:
            raise forms.ValidationError("Upload a valid PDF, JPG or PNG receipt.")
        return receipt


from pathlib import Path
from .models import AccountsExpense

class AccountsExpenseForm(forms.ModelForm):
    class Meta:
        model = AccountsExpense
        fields = [
            "date",
            "category",
            "amount",
            "paid_amount",
            "payment_method",
            "paid_to",
            "description",
            "reference",
            "receipt",
        ]
        labels = {
            "date": "Expense Date",
            "category": "Category",
            "amount": "Total Amount (₹)",
            "paid_amount": "Paid Amount (₹) — blank means fully paid",
            "receipt": "Bill / Receipt (PDF, JPG or PNG, up to 5 MB)",
            "payment_method": "Payment Method",
            "paid_to": "Paid To (optional)",
            "description": "Description",
            "reference": "Reference (optional)",
        }
        widgets = {
            "paid_amount": forms.NumberInput(attrs={"class": "accounts-input", "min": "0", "step": "0.01", "inputmode": "decimal"}),
            "receipt": forms.FileInput(attrs={"class": "accounts-input", "accept": ".pdf,.jpg,.jpeg,.png"}),
            "date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "accounts-input"},
            ),
            "category": forms.TextInput(attrs={
                "class": "accounts-input",
                "placeholder": "e.g. Office supplies",
                "maxlength": "100",
            }),
            "amount": forms.NumberInput(attrs={
                "class": "accounts-input",
                "placeholder": "0.00",
                "min": "0.01",
                "step": "0.01",
                "inputmode": "decimal",
            }),
            "payment_method": forms.Select(attrs={"class": "accounts-input"}),
            "paid_to": forms.TextInput(attrs={
                "class": "accounts-input",
                "placeholder": "Person, vendor or company name",
                "maxlength": "150",
            }),
            "description": forms.Textarea(attrs={
                "class": "accounts-input",
                "placeholder": "Describe this expense entry",
                "rows": 3,
            }),
            "reference": forms.TextInput(attrs={
                "class": "accounts-input",
                "placeholder": "Transaction ID or receipt reference",
                "maxlength": "150",
            }),
        }

    def clean_category(self):
        category = self.cleaned_data.get("category", "").strip()
        if not category:
            raise forms.ValidationError("Enter an expense category.")
        return category

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        if not description:
            raise forms.ValidationError("Enter a description for this expense.")
        return description

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.paid_amount is None:
            self.initial["paid_amount"] = self.instance.amount

    def clean(self):
        cleaned = super().clean()
        amount, paid = cleaned.get("amount"), cleaned.get("paid_amount")
        if amount is not None:
            if paid is None:
                cleaned["paid_amount"] = amount
            elif paid > amount:
                self.add_error("paid_amount", "Paid amount cannot exceed the total amount.")
        return cleaned

    def clean_reference(self):
        return self.cleaned_data.get("reference", "").strip()

    def clean_paid_to(self):
        return self.cleaned_data.get("paid_to", "").strip()

    def clean_receipt(self):
        receipt = self.cleaned_data.get("receipt")
        if not receipt or not hasattr(receipt, "content_type"):
            return receipt
        if receipt.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Receipt must be 5 MB or smaller.")
        suffix = Path(receipt.name).suffix.lower()
        header = receipt.read(8)
        receipt.seek(0)
        valid = ((suffix == ".pdf" and header.startswith(b"%PDF-")) or
                 (suffix in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff")) or
                 (suffix == ".png" and header == b"\x89PNG\r\n\x1a\n"))
        if not valid:
            raise forms.ValidationError("Upload a valid PDF, JPG or PNG receipt.")
        return receipt

from django import forms
from .models import AccountsSale, AccountsSalePayment
from pathlib import Path
class AccountsSaleForm(forms.ModelForm):
    class Meta:
        model = AccountsSale
        fields = [
            "date",
            "due_date",
            "invoice_file",
            "customer_name",
            "invoice_number",
            "amount",
            "received_amount",
            "description",
        ]
        labels = {
            "due_date": "Payment Due Date (optional)",
            "invoice_file": "Invoice (PDF, JPG or PNG, up to 5 MB)",
            "date": "Sale Date",
            "customer_name": "Customer Name",
            "invoice_number": "Invoice Number (optional)",
            "amount": "Sale Amount (₹)",
            "received_amount": "Received Amount (₹)",
            "description": "Description",
        }
        widgets = {
            "due_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "accounts-input"}),
            "invoice_file": forms.FileInput(attrs={"class": "accounts-input", "accept": ".pdf,.jpg,.jpeg,.png"}),
            "date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "accounts-input"},
            ),
            "customer_name": forms.TextInput(attrs={
                "class": "accounts-input",
                "placeholder": "Customer or company name",
                "maxlength": "150",
            }),
            "invoice_number": forms.TextInput(attrs={
                "class": "accounts-input",
                "placeholder": "e.g. INV-2026-001",
                "maxlength": "100",
            }),
            "amount": forms.NumberInput(attrs={
                "class": "accounts-input",
                "placeholder": "0.00",
                "min": "0.01",
                "step": "0.01",
                "inputmode": "decimal",
            }),
            "received_amount": forms.NumberInput(attrs={
                "class": "accounts-input",
                "placeholder": "0.00",
                "min": "0.00",
                "step": "0.01",
                "inputmode": "decimal",
            }),
            "description": forms.Textarea(attrs={
                "class": "accounts-input",
                "placeholder": "Describe the service or product sold",
                "rows": 3,
            }),
        }

    def clean_customer_name(self):
        customer_name = self.cleaned_data.get("customer_name", "").strip()
        if not customer_name:
            raise forms.ValidationError("Enter a customer name.")
        return customer_name

    def clean_invoice_number(self):
        return self.cleaned_data.get("invoice_number", "").strip()

    def clean_description(self):
        description = self.cleaned_data.get("description", "").strip()
        if not description:
            raise forms.ValidationError("Enter a description for this sale.")
        return description

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Payments are recorded separately; sale edits cannot rewrite payment totals.
            self.fields.pop("received_amount", None)

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        received_amount = self.instance.received_amount if self.instance.pk else cleaned_data.get("received_amount")
        if (
            amount is not None
            and received_amount is not None
            and received_amount > amount
        ):
            self.add_error(
                "amount" if self.instance.pk else "received_amount",
                "Received amount cannot be more than the sale amount.",
            )
        sale_date, due = cleaned_data.get("date"), cleaned_data.get("due_date")
        if due and sale_date and due < sale_date:
            self.add_error("due_date", "Due date cannot be before the sale date.")
        if self.instance.pk and sale_date:
            first_payment = self.instance.payments.order_by("date").first()
            if first_payment and sale_date > first_payment.date:
                self.add_error("date", "Sale date cannot be later than a recorded payment date.")
        return cleaned_data

    def clean_invoice_file(self):
        invoice_file = self.cleaned_data.get("invoice_file")
        if not invoice_file or not hasattr(invoice_file, "content_type"):
            return invoice_file
        if invoice_file.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Invoice must be 5 MB or smaller.")
        suffix = Path(invoice_file.name).suffix.lower()
        header = invoice_file.read(8)
        invoice_file.seek(0)
        valid = ((suffix == ".pdf" and header.startswith(b"%PDF-")) or
                 (suffix in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff")) or
                 (suffix == ".png" and header == b"\x89PNG\r\n\x1a\n"))
        if not valid:
            raise forms.ValidationError("Upload a valid PDF, JPG or PNG invoice_file.")
        return invoice_file


class AccountsSalePaymentForm(forms.ModelForm):
    request_token = forms.UUIDField(widget=forms.HiddenInput)
    class Meta:
        model = AccountsSalePayment
        fields = ["date", "amount", "payment_method", "reference", "note"]
    def clean_reference(self):
        return self.cleaned_data.get("reference", "").strip()
    def clean_note(self):
        return self.cleaned_data.get("note", "").strip()
