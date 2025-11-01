from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicioSesion, name="inicioSesion"),
    path("resumen/", views.resumenFinanciero, name="resumenFinanciero"),
    path("registrarse/", views.registrarse, name="registrarse"),
    path("gasto/agregar/", views.agregar_gasto, name="agregar_gasto"),
    path("ingreso/agregar/", views.agregar_ingreso, name="agregar_ingreso"),
    
    path("agrrgar_categoria/", views.agregar_categoria, name="agregar_categoria"),

    path('calificar/', views.registrar_calificacion, name="calificar"),
    path('verCalificaciones/',views.lista_calificaciones, name="calificaciones")

    
    
]
