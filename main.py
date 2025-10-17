# main.py (VERSÃO FINAL 1.3 - COM RESOLUÇÃO MANUAL E APOSTA RÁPIDA)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Importamos os módulos
from bet_api import get_all_prematch_odds
from db_manager import setup_database, get_latest_saldo, update_saldo, insert_aposta, get_all_apostas, update_aposta_resultado
from data_processor import calculate_performance_metrics, create_profit_chart
from automation_job import run_result_automation 

# --- Configuração Inicial ---
st.set_page_config(layout="wide", page_title="Bet Manager | Projeto Ícaro & Gemini")

# Configura o banco de dados (cria o arquivo e as tabelas).
setup_database()

# Função para carregar os saldos
def load_saldos():
    return {
        'Sportingbet': get_latest_saldo('Sportingbet'),
        'Superbet': get_latest_saldo('Superbet')
    }
    
# Função para recarregar dados (usada após salvar aposta/saldo/automação)
def refresh_data():
    st.session_state['saldos'] = load_saldos()
    st.session_state['apostas_data'] = get_all_apostas()


# Carrega os saldos e armazena no estado da sessão
if 'saldos' not in st.session_state:
    st.session_state['saldos'] = load_saldos()
    
# Inicializa o estado da sessão para as odds e apostas
if 'odds_data' not in st.session_state:
    st.session_state['odds_data'] = pd.DataFrame()
    
# Tenta carregar apostas (com fallback)
if 'apostas_data' not in st.session_state:
    try:
        st.session_state['apostas_data'] = get_all_apostas()
    except Exception:
        st.session_state['apostas_data'] = pd.DataFrame()
# ----------------------------

st.title("⚽ Bet Manager Pro - V1.0")
st.markdown("---")

# 1. SIDEBAR: Configurações e Saldo
with st.sidebar:
    st.header("⚙️ Controle Financeiro")
    
    # Campo para atualização de saldo
    st.subheader("Atualizar Saldo")
    casa_saldo = st.selectbox("Casa", ['Sportingbet', 'Superbet'], key='sb_casa')
    # Preenche com o saldo atual
    saldo_atual_sb = st.session_state['saldos'].get(casa_saldo, 0.00)
    novo_saldo = st.number_input("Novo Saldo (R$)", min_value=0.00, value=saldo_atual_sb, step=10.00, format="%.2f", key='sb_novo_saldo')
    
    if st.button("Salvar Saldo"):
        update_saldo(casa_saldo, novo_saldo)
        refresh_data() # Recarrega o saldo
        st.success(f"Saldo da {casa_saldo} atualizado para R$ {novo_saldo:.2f}")

    st.markdown("---")
    
    # Exibição do Saldo Atual (puxado do DB)
    st.subheader("Resumo Atual")
    saldo_sb = st.session_state['saldos'].get('Sportingbet', 0.00)
    saldo_superbet = st.session_state['saldos'].get('Superbet', 0.00)

    st.info(f"💰 Sportingbet: R$ {saldo_sb:.2f}")
    st.info(f"💰 Superbet: R$ {saldo_superbet:.2f}")
    st.success(f"**Total em Caixa:** R$ {saldo_sb + saldo_superbet:.2f}")

    st.markdown("---")
    
    # Botão para atualizar dados de Odds
    if st.button("🔄 Atualizar Jogos/Odds (Busca Mensal)"):
        with st.spinner("Buscando dados (Simulação)..."):
            st.session_state['odds_data'] = get_all_prematch_odds()
        st.success(f"Dados de Odds e Jogos simulados atualizados!")
        
    st.markdown("---")
    
    # Botão para Automação de Resultados (Reativado)
    st.subheader("🤖 Automação")
    if st.button("Executar Verificação de Resultados (Simulado)"):
        with st.spinner("Executando automação e verificando apostas pendentes..."):
            updated_count = run_result_automation()
        
        refresh_data() 
        st.success(f"Automação concluída! {updated_count} apostas resolvidas.")


# 2. MAIN PAGE: Tabs para Jogos e Performance
tab_jogos, tab_apostas, tab_performance = st.tabs(["🔥 Jogos do Mês & Odds", "📝 Minhas Apostas", "📊 Performance (Gráficos)"])

with tab_jogos:
    st.header("Odds Pré-Jogo das Casas (Busca Mensal)")
    
    if st.session_state['odds_data'].empty:
        st.info("Clique em 'Atualizar Jogos/Odds' na barra lateral para carregar os dados do mês.")
    else:
        # --- FILTRO DE DATA ---
        hoje = datetime.now().date()
        df_odds = st.session_state['odds_data'].copy()
        
        # Cria a coluna de filtro
        df_odds['Data_Apenas'] = pd.to_datetime(df_odds['Data_Hora']).dt.date
        
        # Filtra a data selecionada
        datas_disponiveis = df_odds['Data_Apenas'].unique()
