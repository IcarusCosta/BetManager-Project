# data_processor.py (VERSÃO CORRIGIDA)

import pandas as pd
import plotly.express as px
from datetime import datetime # <--- ESSA LINHA RESOLVE O NAMERROR

def calculate_performance_metrics(df_apostas: pd.DataFrame):
    """
    Calcula métricas de desempenho (Total de Apostas, Stake, Lucro e ROI).
    """
    # 1. TRATAMENTO DE DATAFRAME VAZIO OU SEM COLUNAS ESSENCIAIS
    if df_apostas.empty or 'Status' not in df_apostas.columns or 'Valor_Apostado' not in df_apostas.columns:
        return 0, 0.00, 0.00, 0.00

    # 2. GARANTIR TIPAGEM CORRETA
    # Converte colunas financeiras para float (pode ser o causador do ValueError)
    try:
        df_apostas['Valor_Apostado'] = pd.to_numeric(df_apostas['Valor_Apostado'], errors='coerce')
        df_apostas['Valor_Retorno'] = pd.to_numeric(df_apostas['Valor_Retorno'], errors='coerce').fillna(0)
        df_apostas['Lucro'] = df_apostas['Valor_Retorno'] - df_apostas['Valor_Apostado']
    except Exception as e:
        print(f"Erro de tipagem no cálculo de métricas: {e}")
        return 0, 0.00, 0.00, 0.00


    # 3. FILTRAR APENAS APOSTAS RESOLVIDAS (GREEN, RED, CASHOUT)
    df_resolvidas = df_apostas[df_apostas['Status'].isin(['GREEN', 'RED', 'CASHOUT'])]
    
    if df_resolvidas.empty:
        return len(df_apostas), df_apostas['Valor_Apostado'].sum(), 0.00, 0.00


    # 4. CÁLCULO DAS MÉTRICAS
    total_apostas = len(df_resolvidas)
    total_stake = df_resolvidas['Valor_Apostado'].sum()
    total_lucro = df_resolvidas['Lucro'].sum()

    # Cálculo do ROI: (Lucro / Stake) * 100
    if total_stake > 0:
        roi = (total_lucro / total_stake) * 100
    else:
        roi = 0.00
        
    return total_apostas, total_stake, total_lucro, roi

def create_profit_chart(df_apostas: pd.DataFrame):
    """
    Cria um gráfico de linha da evolução do lucro.
    """
    if df_apostas.empty or 'Data_Registro' not in df_apostas.columns:
        # Garante que, se for vazio, crie um DataFrame com a data importada
        df_apostas = pd.DataFrame({'Data_Registro': [datetime.now()], 'Lucro_Acumulado': [0.0]})
    else:
        # Garantir tipagem e coluna Lucro
        df_apostas['Valor_Apostado'] = pd.to_numeric(df_apostas['Valor_Apostado'], errors='coerce').fillna(0)
        df_apostas['Valor_Retorno'] = pd.to_numeric(df_apostas['Valor_Retorno'], errors='coerce').fillna(0)
        df_apostas['Lucro'] = df_apostas['Valor_Retorno'] - df_apostas['Valor_Apostado']
        
        # Filtrar e calcular lucro acumulado
        df_resolvidas = df_apostas[df_apostas['Status'].isin(['GREEN', 'RED', 'CASHOUT'])].copy()
        
        if df_resolvidas.empty:
             df_apostas = pd.DataFrame({'Data_Registro': [datetime.now()], 'Lucro_Acumulado': [0.0]})
        else:
            df_resolvidas['Lucro_Acumulado'] = df_resolvidas['Lucro'].cumsum()
            df_apostas = df_resolvidas

    fig = px.line(
        df_apostas, 
        x='Data_Registro', 
        y='Lucro_Acumulado', 
        title='Evolução do Lucro Líquido Acumulado',
        labels={'Lucro_Acumulado': 'Lucro Acumulado (R$)', 'Data_Registro': 'Data da Aposta'},
        markers=True
    )
    
    # Estilização básica
    fig.update_layout(xaxis_title="Data", yaxis_title="Lucro Acumulado (R$)", hovermode="x unified")
    fig.update_traces(line=dict(color='green', width=2))
    
    # Adicionar linha horizontal em zero
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    return fig
