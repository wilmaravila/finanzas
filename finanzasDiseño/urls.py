from django.urls import path
from . import views

urlpatterns = [
    path("", views.inicioSesion, name="inicioSesion"),
    path("resumen/", views.resumenFinanciero, name="resumenFinanciero"),
    path("registrarse/", views.registrarse, name="registrarse"),
    path("gasto/agregar/", views.agregar_gasto, name="agregar_gasto"),
    path("ingreso/agregar/", views.agregar_ingreso, name="agregar_ingreso"),
    path("categorias/", views.categorias_list, name="categorias_list"),
    path("categorias/agregar/", views.agregar_categoria, name="agregar_categoria"),
]