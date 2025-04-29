from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from celery.result import AsyncResult
from .tasks import gerar_relatorio
from .tasks import test_task
from .models import Relatorio
import json

def disparar_relatorio(request):
    task = gerar_relatorio.delay()  # dispara a task de forma assíncrona
    return JsonResponse({'task_id': task.id})


def verificar_status(request, task_id):
    task = AsyncResult(task_id)
    if task.state == 'SUCCESS':
        result = task.result
        return JsonResponse({'status': 'Concluído', 'relatorio': result})
    elif task.state == 'PENDING':
        return JsonResponse({'status': 'Pendente'})
    elif task.state == 'FAILURE':
        return JsonResponse({'status': 'Falhou', 'erro': str(task.result)})
    else:
        return JsonResponse({'status': task.state})

# Create your views here.
def test_task_view(request):
    task = test_task.delay()
    return JsonResponse({'task_id': task.id})

def home_view(request):
    return HttpResponse("Bem-vindo ao sistema de relatórios!")


def exibir_relatorio(request):
    relatorio = Relatorio.objects.last()

    if relatorio:
        # Carrega o conteúdo do JSON para uma lista de dicionários
        dados_relatorio = json.loads(relatorio.conteudo)
    else:
        dados_relatorio = None

    return render(request, 'relatorios/exibir_template.html', {'dados_relatorio': dados_relatorio})
