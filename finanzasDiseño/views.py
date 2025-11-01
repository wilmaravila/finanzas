from django.shortcuts import render, redirect
from django.contrib import auth
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Value, DecimalField, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
import json
from .models import Calificaciones, Transaction, Category
from .forms import CalificacionForm, TransactionForm, CategoryForm
from . import models
from datetime import date
import calendar
import io, base64
import matplotlib.pyplot as plt
from django.contrib.auth import get_user_model

# añadir never_cache a las vistas relevantes
@never_cache
def inicioSesion(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("resumenFinanciero")
        else:
            error = "Usuario o contraseña incorrectos."

    return render(request, "inicioSesion.html", {"error": error})

@never_cache
def registrarse(request):
    UserModel = get_user_model()
    error = None
    values = {"fullname": "", "email": ""}
    if request.method == "POST":
        fullname = request.POST.get("fullname", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")

        values["fullname"] = fullname
        values["email"] = email

        if not fullname or not email or not password or not password2:
            error = "Todos los campos son obligatorios."
        elif password != password2:
            error = "Las contraseñas no coinciden."
        elif len(password) < 6:
            error = "La contraseña debe tener al menos 6 caracteres."
        elif UserModel.objects.filter(username=email).exists() or UserModel.objects.filter(email=email).exists():
            error = "Ya existe una cuenta con ese correo."
        else:
            # dividir nombre y apellido (si hay)
            parts = fullname.split(None, 1)
            first_name = parts[0] if parts else ""
            last_name = parts[1] if len(parts) > 1 else ""
            user = UserModel.objects.create_user(username=email, email=email, password=password,
                                            first_name=first_name, last_name=last_name)
            user.save()
            print(user)
            auth.login(request, user)
            return redirect("resumenFinanciero")

    return render(request, "registrarse.html", {"error": error, "values": values})

@never_cache
@login_required(login_url='/')
def resumenFinanciero(request):
    user = request.user

    # --- calcular series mensuales (últimos 6 meses) ---
    today = timezone.localdate()
    month_labels = []
    series_ing = []
    series_ex = []
    for i in range(5, -1, -1):
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        month_labels.append(start.strftime("%b %Y"))
        ing = Transaction.objects.filter(user=user, type='IN', date__gte=start, date__lte=end) \
            .aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField()))['total']
        ex = Transaction.objects.filter(user=user, type='EX', date__gte=start, date__lte=end) \
            .aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField()))['total']
        series_ing.append(float(ing))
        series_ex.append(float(ex))

    # --- generar gráfico de barras (matplotlib) ---
    if any(series_ing) or any(series_ex):
        fig, ax = plt.subplots(figsize=(8,4))
        n = len(month_labels)
        x = list(range(n))
        width = 0.35
        ax.bar([xi - width/2 for xi in x], series_ing, width, label='Ingresos', color='#28a745')
        ax.bar([xi + width/2 for xi in x], series_ex, width, label='Gastos', color='#dc3545')
        ax.set_xticks(x)
        ax.set_xticklabels(month_labels, rotation=45, ha='right')
        ax.set_ylabel('Monto')
        ax.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode('ascii')
        bar_chart_uri = f"data:image/png;base64,{img_b64}"
    else:
        bar_chart_uri = None

    # calcular gastos por categoría (igual que antes)
    gastos_por_cat_qs = (
        Transaction.objects.filter(user=user, type='EX')
        .values('category__name')
        .annotate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField()))
        .order_by('-total')
    )
    labels = [row['category__name'] or 'Sin categoría' for row in gastos_por_cat_qs]
    values = [float(row['total']) for row in gastos_por_cat_qs]

    # si no hay datos, puedes renderizar un placeholder
    if not values:
        chart_data_uri = None
    else:
        # generar gráfico de torta (pie)
        fig, ax = plt.subplots(figsize=(5,5))
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode('ascii')
        chart_data_uri = f"data:image/png;base64,{img_b64}"

    # otros datos (totales) opcionales...
    total_ingresos = Transaction.objects.filter(user=user, type='IN') \
        .aggregate(total=Coalesce(Sum('amount'), Value(0), output_field=DecimalField()))['total']
    total_gastos = sum(values) if values else 0
    balance = float(total_ingresos) - float(total_gastos)

    context = {
        "total_ingresos": float(total_ingresos),
        "total_gastos": float(total_gastos),
        "balance": float(balance),
        "pie_chart_uri": chart_data_uri,   # si ya generaste pie
        "bar_chart_uri": bar_chart_uri,
        "top_cats": gastos_por_cat_qs[:5],
    }
    return render(request, "resumenFinanciero.html", context)

@never_cache
@login_required(login_url='/')
def agregar_ingreso(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user, kind='IN')
        if form.is_valid():
            t = form.save(commit=False)
            t.user = request.user
            t.type = 'IN'
            t.save()
            return redirect("resumenFinanciero")
    else:
        form = TransactionForm(user=request.user, kind='IN')
    return render(request, "agregar_ingreso.html", {"form": form})

@never_cache
@login_required(login_url='/')
def agregar_gasto(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user, kind='EX')
        if form.is_valid():
            t = form.save(commit=False)
            t.user = request.user
            t.type = 'EX'
            t.save()
            return redirect("resumenFinanciero")
    else:
        form = TransactionForm(user=request.user, kind='EX')
    return render(request, "agregar_gasto.html", {"form": form})



@login_required(login_url='/')
def agregar_categoria(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.user = request.user  # si quieres que sea global, cambia a None
            c.save()
            return render(request, "resumenFinanciero.html")
    else:
        form = CategoryForm()
    return render(request, "nueva_categoria.html", {"form": form})


    

def registrar_calificacion(request):
    if request.method == 'POST':
        form = CalificacionForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'exito.html')  # Página de éxito
    else:
        form = CalificacionForm()
    
    return render(request, 'crear_calificaciones.html', {'form': form})


def lista_calificaciones(request):
    calificaciones = Calificaciones.objects.all()  # 👈 obtiene todos los registros
    if calificaciones:
        return render(request, 'calificaciones.html', {'calificaciones': calificaciones})
    else:
        return render(request, 'calificaciones.html', {'calificaciones': 0})







def cerrar_sesion(request):
    auth.logout(request)
    return redirect("inicioSesion")

