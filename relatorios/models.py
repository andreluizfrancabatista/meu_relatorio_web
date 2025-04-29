from django.db import models
from django.contrib.postgres.fields import ArrayField  # Se usar PostgreSQL, facilita a manipulação de listas.

class Relatorio(models.Model):
    data_geracao = models.DateTimeField()  # Data e hora da geração do relatório
    conteudo = models.TextField()  # Dados em formato JSON como string

    def __str__(self):
        return f"Relatório gerado em {self.data_geracao}"
