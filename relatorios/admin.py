# Register your models here.
from django.contrib import admin
from .models import Relatorio
import json

@admin.register(Relatorio)
class RelatorioAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_geracao', 'exibir_conteudo')
    ordering = ('-data_geracao',)

    def exibir_conteudo(self, obj):
        try:
            conteudo_json = json.loads(obj.conteudo)
            return f"{len(conteudo_json)} itens"
        except json.JSONDecodeError:
            return "Erro no conteúdo"
    exibir_conteudo.short_description = 'Conteúdo'

    # Adiciona um link para ver o conteúdo completo no detalhe
    def view_conteudo_link(self, obj):
        return f'<a href="/admin/relatorios/relatorio/{obj.id}/">Ver Conteúdo</a>'
    view_conteudo_link.allow_tags = True
    view_conteudo_link.short_description = 'Ver Conteúdo Completo'

