from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

app = Celery('django_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configuração do Result Backend
app.conf.update(
    result_backend='redis://localhost:6379/0',  # Usando Redis como backend
    broker_url='redis://localhost:6379/0',      # Usando Redis como broker
)

# Carregar tasks do Django
app.autodiscover_tasks()