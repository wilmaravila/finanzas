from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    KIND_CHOICES = (('IN', 'Ingreso'), ('EX', 'Gasto'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)  # null=user significa categoría global
    name = models.CharField(max_length=64)
    kind = models.CharField(max_length=2, choices=KIND_CHOICES, default='EX')

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPE = (
        ('IN', 'Ingreso'),
        ('EX', 'Gasto'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=2, choices=TRANSACTION_TYPE)
    date = models.DateField()

    def __str__(self):
        return f"{self.title} ({self.amount})"
