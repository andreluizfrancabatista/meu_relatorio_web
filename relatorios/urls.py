# relatorios/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('exibir-relatorio/', views.exibir_relatorio, name='exibir_relatorio'),
]
