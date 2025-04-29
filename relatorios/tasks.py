from celery import shared_task
import pandas as pd
from datetime import datetime
from .models import Relatorio  # Importa o modelo que vamos usar para armazenar os relatórios.
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
from django.template.loader import render_to_string
from django.conf import settings

# B-Bélgica, D-Alemanha, E-Inglaterra, F-França, G-Grécia, I-Itália, N-Holanda, P-Portugal, SC-Escócia, SP-Espanha, T-Turquia
cp_list = ['B1', 'D1', 'D2', 'E0', 'E1', 'E2', 'E3', 'EC', 'F1', 'F2','G1', 'I1', 'I2', 'N1', 'P1', 'SC0', 'SC1', 'SC2', 'SC3', 'SP1', 'SP2', 'T1']

# Jogos futuros (fixtures)
def build_df_new(cp):
  df = pd.read_csv('https://www.football-data.co.uk/fixtures.csv')
  df = df[df['Div']==cp][['Date', 'Time', 'HomeTeam', 'AwayTeam']]
  df.rename(columns={'HomeTeam' : 'HOME', 'AwayTeam' : 'AWAY'}, inplace=True)
  df.reset_index(inplace=True, drop=True)
  return df

# Resultados anteriores
def build_df(cp):
  try:
    if cp == 'D2':
      df = pd.read_csv(f'https://www.football-data.co.uk/mmz4281/2425/{cp}.csv', encoding='latin1')
    else:
      df = pd.read_csv(f'https://www.football-data.co.uk/mmz4281/2425/{cp}.csv')
    df = df[['Date', 'Time', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']]
    df.rename(columns={'HomeTeam' : 'HOME', 'AwayTeam' : 'AWAY'}, inplace=True)
    df['DIFF'] = [fthg - ftag for fthg, ftag in zip(df['FTHG'], df['FTAG'])]
    df.dropna(inplace=True)
    return df
  except Exception as error:
    print(f'Error: {error}')
    print(f'CP: {cp}')
    pass

def build_system_from_df(df):
    # Extrair as colunas necessárias
    home_teams = df['HOME'].values
    away_teams = df['AWAY'].values
    diffs = df['DIFF'].values
    # Coletar todas as variáveis (times)
    variables = set(home_teams).union(set(away_teams))
    variables = sorted(variables)
    num_vars = len(variables)
    var_index = {var: idx for idx, var in enumerate(variables)}
    # Construir a matriz A e o vetor b
    A = np.zeros((len(df), num_vars))
    b = np.zeros(len(df))
    for i in range(len(df)):
        home_team = home_teams[i]
        away_team = away_teams[i]
        diff = diffs[i]
        A[i, var_index[home_team]] = 1
        A[i, var_index[away_team]] = -1
        b[i] = diff
    return A, b, variables

def solve_system_from_df(df):
    try:
      A, b, variables = build_system_from_df(df)
      x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
      solution = {variables[i]: x[i] for i in range(len(variables))}
      return solution
    except Exception as error:
      print(f'Error: {error}')
      print(f'DF: {df}')
      pass

def add_scores_to_df_new(solution, df_new):
    # Adicionar colunas com as pontuações dos times e a diff
    df_new['HOME_SCORE'] = df_new['HOME'].map(solution)
    df_new['AWAY_SCORE'] = df_new['AWAY'].map(solution)
    df_new['DIFF'] = (df_new['HOME_SCORE'] - df_new['AWAY_SCORE']).map('{:.2f}'.format)
    return df_new

def calcular_max_jogos(df):
    home_counts = df['HOME'].value_counts()
    away_counts = df['AWAY'].value_counts()
    total_games = home_counts.add(away_counts, fill_value=0).astype(int)
    return total_games.max()


# Função para gerar o relatório
@shared_task
def gerar_relatorio_completo():
    try:
        dfs = []
        for cp in cp_list:
            df = build_df(cp)
            solution = solve_system_from_df(df)
            solution_sorted = {k: v for k, v in sorted(solution.items(), key=lambda item: item[1], reverse=True)}
            df_new = build_df_new(cp)
            df_with_scores = add_scores_to_df_new(solution, df_new)
            df_with_scores['DIFF'] = pd.to_numeric(df_with_scores['DIFF'], errors="coerce")
            df_with_scores['CP'] = cp
            df_with_scores['MATCHES'] = calcular_max_jogos(df)
            if not df_with_scores.empty:
                dfs.append(df_with_scores)
        try:
            df_final = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
            # Cria coluna de datetime ciente de fuso (timezone-aware) com horário de Londres
            df_final['Datetime'] = pd.to_datetime(df_final['Date'] + ' ' + df_final['Time'], format='%d/%m/%Y %H:%M')
            df_final['Datetime'] = df_final['Datetime'].dt.tz_localize(ZoneInfo('Europe/London'))
            # Converte para horário de Brasília
            df_final['Datetime'] = df_final['Datetime'].dt.tz_convert(ZoneInfo('America/Sao_Paulo'))
            # Atualiza 'Date' e 'Time' com os valores já convertidos
            df_final['Date'] = df_final['Datetime'].dt.strftime('%d/%m/%Y')
            df_final['Time'] = df_final['Datetime'].dt.strftime('%H:%M')
            # Remove coluna auxiliar
            df_final.drop(columns=['Datetime'], inplace=True)
            df_final.drop_duplicates(inplace=True, ignore_index=True)
            # Ordena os jogos por data e hora
            df_final_sorted = df_final.sort_values(by=['Date', 'Time'], ignore_index=True)
            # Arredonda as colunas numéricas para 2 casas decimais
            df_final_sorted['HOME_SCORE'] = df_final_sorted['HOME_SCORE'].round(2)
            df_final_sorted['AWAY_SCORE'] = df_final_sorted['AWAY_SCORE'].round(2)

        except Exception as error:
            print(f'Erro: {error}')
            pass

        # Criação do relatório final
        relatorio_dict = df_final_sorted.to_dict(orient='records')
        print(json.dumps(df_final_sorted.to_dict(orient='records')))

        # Salva o relatório no banco
        relatorio = Relatorio.objects.create(
            data_geracao=datetime.now(tz=ZoneInfo('America/Sao_Paulo')),
            conteudo=json.dumps(df_final_sorted.to_dict(orient='records'))  # salva como string JSON
        )
        
        # Gerando a página HTML usando o template
        gerar_pagina_html_com_template(relatorio)

        
        print("Relatório gerado e salvo com sucesso!")
        return f"Relatório {relatorio.id} gerado com sucesso!"
    except Exception as error:
        print(f'Erro ao gerar relatório: {error}')
    return None



def gerar_pagina_html_com_template(relatorio):
    # Carregar os dados do JSON do campo 'conteudo'
    relatorio_data = json.loads(relatorio.conteudo)
    
    # Usar o template 'exibir_template.html' para renderizar o relatório
    html_content = render_to_string('relatorios/exibir_template.html', {
        'relatorio': relatorio_data,
        'data_geracao': relatorio.data_geracao
    })
    
    # Caminho onde o HTML será armazenado
    static_dir = os.path.join(settings.BASE_DIR, 'static')
    os.makedirs(static_dir, exist_ok=True)
    html_file_path = os.path.join(static_dir, 'relatorio.html')
    
    # Salvando o arquivo HTML
    with open(html_file_path, 'w') as f:
        f.write(html_content)
    
    print(f'Página HTML gerada em: {html_file_path}')

# Função para gerar a página HTML estática
def gerar_pagina_html(df):
    # Código para gerar e salvar uma página HTML estática do relatório.
    html_content = df.to_html()  # Converte o DataFrame para HTML
    
    # Caminho onde o HTML será armazenado. Pode ser uma pasta específica no projeto.
    with open('/app/static/relatorio.html', 'w') as f:
        f.write(html_content)

# Task do Celery que chama a função de gerar o relatório.
@shared_task
def gerar_relatorio():
    return gerar_relatorio_completo()



@shared_task
def teste_celery():
    print("Celery está funcionando!")
    return "OK"


@shared_task
def test_task():
    print("Executando task de teste...")
    return "Task executada com sucesso!"
