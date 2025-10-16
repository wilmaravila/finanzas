from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Category

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if not created:
        return
    defaults_in = ['Salario', 'Ventas', 'Inversión', 'Otros']
    defaults_ex = ['Comida', 'Transporte', 'Compras', 'Facturas']
    for name in defaults_in:
        Category.objects.create(user=instance, name=name, kind='IN')
    for name in defaults_ex:
        Category.objects.create(user=instance, name=name, kind='EX')