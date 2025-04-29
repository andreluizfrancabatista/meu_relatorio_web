"""
URL configuration for django_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from relatorios.views import disparar_relatorio  # importe aqui!
from relatorios.tasks import teste_celery
from django.http import JsonResponse
from relatorios import views

def testar_task(request):
    teste_celery.delay()
    return JsonResponse({'status': 'task enviada'})

urlpatterns = [
    path('', views.home_view, name='home'),
    path('', include('relatorios.urls')),  # Inclui as URLs do app relatorios
    path('admin/', admin.site.urls),
    path('testar-task/', testar_task),
    path('test-task/', views.test_task_view, name='test-task'),
    path('disparar-relatorio/', views.disparar_relatorio, name='disparar_relatorio'),
    path('verificar-status/<task_id>/', views.verificar_status, name='verificar_status'),
    path('exibir-relatorio/', views.exibir_relatorio, name='exibir_relatorio'),
]
