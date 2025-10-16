from django import forms
from django.db.models import Q
from .models import Transaction, Category
from django.core.exceptions import ValidationError
from datetime import date

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "category", "title", "date"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
            "title": forms.Textarea(attrs={"class": "form-control", "placeholder": "Descripción (opcional)"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, user=None, kind=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Category.objects.none()
        if kind:
            qs = Category.objects.filter(kind=kind)
            if user is not None:
                qs = qs.filter(Q(user=user) | Q(user__isnull=True))
        self.fields["category"].queryset = qs
        self.fields["category"].required = False

        # establecer max en el input date al día de hoy (cliente)
        self.fields['date'].widget.attrs['max'] = date.today().isoformat()

    def clean_date(self):
        d = self.cleaned_data.get('date')
        if d and d > date.today():
            raise ValidationError("La fecha no puede ser en el futuro.")
        return d

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "kind"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "kind": forms.Select(attrs={"class": "form-select"}),
        }