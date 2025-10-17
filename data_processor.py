# data_processor.py

import pandas as pd
import plotly.express as px

def calculate_performance_metrics(df_apostas: pd.DataFrame):
    """
    Calcula o Lucro Total e o ROI (Return on Investment)
    
    ROI = (Lucro Total / Valor Apostado Total) * 100
    """
    if df_apostas.empty:
        return 0.00, 0.00, pd.DataFrame() # Lucro, ROI, df_resumo
    
    # Filtra apenas apostas resolvidas (Green, Red, Cashout)
    df_resolvidas = df_apostas[df_apostas['status'] != 'AGUARDANDO'].copy()
    
    if df_resolvidas.empty:
        return 0.00, 0.00, pd.DataFrame()

    # Cálculo do Lucro/Prejuízo:
    # Lucro é preenchido na coluna 'lucro'
    lucro_total = df_resolvidas['lucro'].sum()
    
    # Valor Apostado Total (Stake total)
    valor_apostado_total = df_resolvidas['valor'].sum()
    
    # Cálculo do ROI
    if valor_apostado_total > 0:
        roi = (lucro_total / valor_apostado_total) * 100
    else:
        roi = 0.00
        
    # Agrupamento para o Resumo
    df_resumo = df_resolvidas.groupby('casa').agg(
        Total_Apostas=('id', 'size'),
        Lucro_Casa=('lucro', 'sum'),
        Stake_Casa=('valor', 'sum'),
        Greens=('status', lambda x: (x == 'GREEN').sum()),
        Reds=('status', lambda x: (x == 'RED').sum())
    ).reset_index()
    
    df_resumo['%_Acerto'] = (df_resumo['Greens'] / df_resumo['Total_Apostas']) * 100
    df_resumo['ROI_Casa'] = (df_resumo['Lucro_Casa'] / df_resumo['Stake_Casa']) * 100
    
    return lucro_total, roi, df_resumo

def create_profit_chart(df_apostas: pd.DataFrame, freq='D'):
    """
    Cria um gráfico Plotly de Lucro Acumulado Diário/Semanal/Mensal.
    freq: 'D' (Diário), 'W' (Semanal), 'M' (Mensal)
    """
    if df_apostas.empty:
        return px.scatter(title="Sem dados para gerar gráfico.")

    df_resolvidas = df_apostas[df_apostas['status'] != 'AGUARDANDO'].copy()
    if df_resolvidas.empty:
        return px.scatter(title="Sem apostas resolvidas para gerar gráfico.")
    
    # Converte a coluna de data para datetime e define como índice
    df_resolvidas['data_aposta'] = pd.to_datetime(df_resolvidas['data_aposta'])
    df_resolvidas.set_index('data_aposta', inplace=True)
    
    # Agrupa o lucro pela frequência (Dia, Semana, Mês)
    df_resampled = df_resolvidas['lucro'].resample(freq).sum().fillna(0)
    
    # Calcula o lucro acumulado
    df_acumulado = df_resampled.cumsum().reset_index()
    df_acumulado.columns = ['Data', 'Lucro Acumulado']
    
    # Cria o gráfico de linha interativo com Plotly
    fig = px.line(
        df_acumulado, 
        x='Data', 
        y='Lucro Acumulado', 
        title=f'Lucro Acumulado ({freq})',
        labels={'Lucro Acumulado': 'R$', 'Data': 'Período'},
        line_shape='spline'
    )
    
    # Adiciona linha em Y=0 para referência
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(hovermode="x unified") # Melhora a interatividade
    
    return fig