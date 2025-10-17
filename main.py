# main.py (VERSÃO FINAL E FUNCIONAL COM FILTRO DE DATA)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Importamos os módulos
from bet_api import get_all_prematch_odds
from db_manager import setup_database, get_latest_saldo, update_saldo, insert_aposta, get_all_apostas, update_aposta_resultado
from data_processor import calculate_performance_metrics, create_profit_chart
from automation_job import run_result_automation # Reativado

# --- Configuração Inicial ---
st.set_page_config(layout="wide", page_title="Bet Manager | Projeto Ícaro & Gemini")

# Configura o banco de dados (cria o arquivo e as tabelas). DEVE SER O PRIMEIRO COMANDO DE DB.
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
    
# Tenta carregar apostas (com fallback para evitar erro 'no such table' na primeira execução)
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
    novo_saldo = st.number_input("Novo Saldo (R$)", min_value=0.00, value=st.session_state['saldos'].get(casa_saldo, 0.00), step=10.00, format="%.2f", key='sb_novo_saldo')
    
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
        with st.spinner("Buscando dados nas casas (API-Football)..."):
            st.session_state['odds_data'] = get_all_prematch_odds()
        st.success(f"Dados de Odds e Jogos de {len(st.session_state['odds_data'].drop_duplicates(subset=['ID_Evento']))} eventos atualizados com sucesso!")
        
    st.markdown("---")
    
    # Botão para Automação de Resultados (Reativado)
    st.subheader("🤖 Automação")
    if st.button("Executar Verificação de Resultados"):
        with st.spinner("Executando automação e verificando apostas pendentes..."):
            updated_count = run_result_automation()
        
        refresh_data() 
        st.success(f"Automação concluída! {updated_count} apostas resolvidas.")


# 2. MAIN PAGE: Tabs para Jogos e Performance
tab_jogos, tab_apostas, tab_performance = st.tabs(["🔥 Jogos do Dia & Odds", "📝 Minhas Apostas", "📊 Performance (Gráficos)"])

with tab_jogos:
    st.header("Odds Pré-Jogo das Casas (Busca Mensal)")
    
    if st.session_state['odds_data'].empty:
        st.info("Clique em 'Atualizar Jogos/Odds' na barra lateral para carregar os dados do mês.")
    else:
        # --- FILTRO DE DATA ---
        hoje = datetime.now().date()
        # Define o range de datas
        datas_disponiveis = pd.to_datetime(st.session_state['odds_data']['Data_Hora']).dt.date.unique()
        
        # Filtra a data selecionada
        data_selecionada = st.date_input(
            "Selecione a Data do Jogo", 
            value=hoje, 
            min_value=min(datas_disponiveis) if len(datas_disponiveis) > 0 else hoje,
            max_value=max(datas_disponiveis) if len(datas_disponiveis) > 0 else hoje + timedelta(days=30)
        )
        
        # Cria a coluna de filtro
        df_odds = st.session_state['odds_data'].copy()
        df_odds['Data_Apenas'] = pd.to_datetime(df_odds['Data_Hora']).dt.date
        df_filtrado = df_odds[df_odds['Data_Apenas'] == data_selecionada]
        
        # --- LÓGICA DE FILTRO POR CASA E LIGA (EXISTENTE) ---
        casas = df_filtrado['Casa'].unique()
        casas_selecionadas = st.multiselect("Filtrar por Casa", casas, default=casas, key='filtro_casa')
        
        # Usamos o df_filtrado (após a data) para obter as ligas daquele dia
        ligas = df_filtrado['Liga'].unique()
        ligas_selecionadas = st.multiselect("Filtrar por Liga", ligas, default=ligas[:5], key='filtro_liga') 

        df_final = df_filtrado[
            (df_filtrado['Casa'].isin(casas_selecionadas)) &
            (df_filtrado['Liga'].isin(ligas_selecionadas))
        ].copy()
        # --- FIM LÓGICA DE FILTRO ---
        
        
        if df_final.empty:
            st.warning(f"Nenhum jogo encontrado para a data {data_selecionada.strftime('%d/%m/%Y')} e filtros atuais.")
        else:
            # Formata a coluna de data para exibição
            df_final['Data_Hora'] = pd.to_datetime(df_final['Data_Hora']).dt.strftime('%d/%m %H:%M')
            
            # Colunas exibidas
            df_display = df_final[['Casa', 'Liga', 'Jogo', 'Data_Hora', 'Odd_1', 'Odd_X', 'Odd_2']]
            
            st.dataframe(df_display, use_container_width=True, height=400, hide_index=True)
            st.caption(f"Total de {len(df_final)} eventos exibidos.")

with tab_apostas:
    st.header("📝 Registro Manual de Aposta")
    
    col_reg1, col_reg2, col_reg3 = st.columns(3)
    
    with col_reg1:
        reg_casa = st.selectbox("Casa de Aposta", ['Sportingbet', 'Superbet'], key='reg_casa')
        reg_mercado = st.text_input("Mercado (Ex: Acima de 2.5 gols)", key='reg_mercado')
    
    with col_reg2:
        reg_liga = st.text_input("Liga/Campeonato", key='reg_liga')
        reg_odd = st.number_input("Odd", min_value=1.01, step=0.01, format="%.2f", key='reg_odd')

    with col_reg3:
        reg_jogo = st.text_input("Evento/Jogo", key='reg_jogo')
        reg_valor = st.number_input("Valor Apostado (Stake R$)", min_value=0.01, step=5.00, format="%.2f", key='reg_valor')

    saldo_disp = st.session_state['saldos'].get(reg_casa, 0.00)
    st.markdown(f"**Saldo Disponível em {reg_casa}: R$ {saldo_disp:.2f}**")
    
    if st.button("✅ Registrar Aposta e Deduzir Saldo", use_container_width=True):
        if reg_valor > 0 and reg_valor <= saldo_disp:
            
            aposta_id = insert_aposta(reg_casa, reg_liga, reg_jogo, reg_mercado, reg_odd, reg_valor)
            
            if aposta_id:
                # 1. Deduz o valor do saldo e salva o novo saldo no DB
                novo_saldo = saldo_disp - reg_valor
                update_saldo(reg_casa, novo_saldo)
                
                # 2. Atualiza a lista de apostas e a sidebar
                refresh_data()
                
                st.success(f"Aposta ID {aposta_id} registrada! R$ {reg_valor:.2f} deduzidos do saldo da {reg_casa}.")
            else:
                st.error("Falha ao registrar a aposta no banco de dados.")
        else:
            st.error("Valor inválido! Certifique-se de que o valor é maior que zero e menor ou igual ao saldo disponível.")

    st.markdown("---")
    st.subheader("Histórico de Apostas Registradas")
    
    # Tabela com histórico de apostas
    if st.session_state['apostas_data'].empty:
        st.info("Nenhuma aposta registrada ainda.")
    else:
        st.dataframe(st.session_state['apostas_data'], use_container_width=True)


with tab_performance:
    st.header("📊 Dashboard de Performance")
    
    df_apostas = st.session_state['apostas_data']
    
    if df_apostas.empty:
        st.info("Registre algumas apostas resolvidas (GREEN/RED) para visualizar o desempenho.")
    else:
        # Calcular métricas de performance
        total_apostas, total_stake, total_lucro, roi = calculate_performance_metrics(df_apostas)
        
        col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
        col_perf1.metric("Total de Apostas", total_apostas)
        col_perf2.metric("Total de Stake", f"R$ {total_stake:.2f}")
        col_perf3.metric("Lucro Líquido", f"R$ {total_lucro:.2f}", delta_color="normal")
        col_perf4.metric("ROI (Retorno)", f"{roi:.2f}%", delta_color="normal")
        
        st.markdown("---")
        st.subheader("Evolução do Lucro ao Longo do Tempo")
        
        # Gerar o gráfico
        fig = create_profit_chart(df_apostas)
        st.plotly_chart(fig, use_container_width=True)