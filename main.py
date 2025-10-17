# main.py (VERSÃO FINAL 1.6.1 - CORRIGINDO O TYPERROR)

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Importamos os módulos (certifique-se de que os outros arquivos estão atualizados também!)
from bet_api import get_all_prematch_odds
from db_manager import setup_database, get_latest_saldo, update_saldo, insert_aposta, get_all_apostas, update_aposta_resultado
from data_processor import calculate_performance_metrics, create_profit_chart
from automation_job import run_result_automation 

# --- Configuração Inicial ---
st.set_page_config(layout="wide", page_title="Bet Manager | Projeto Ícaro & Gemini")

# Configura o banco de dados (cria o arquivo e as tabelas, incluindo a nova coluna Prognostico).
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
        # Garante que seja um DataFrame vazio se houver erro
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
        
        if len(datas_disponiveis) == 0:
            st.error("Não há datas disponíveis no dataset simulado.")
            data_selecionada = hoje
        else:
            min_date = min(datas_disponiveis)
            max_date = max(datas_disponiveis)
            data_selecionada = st.date_input(
                "Selecione a Data do Jogo", 
                value=hoje if hoje in datas_disponiveis else min_date, 
                min_value=min_date,
                max_value=max_date
            )
        
        df_filtrado = df_odds[df_odds['Data_Apenas'] == data_selecionada]
        
        # --- LÓGICA DE FILTRO POR CASA E LIGA ---
        casas = df_filtrado['Casa'].unique()
        casas_selecionadas = st.multiselect("Filtrar por Casa", casas, default=casas, key='filtro_casa')
        
        ligas = df_filtrado['Liga'].unique()
        ligas_selecionadas = st.multiselect("Filtrar por Liga", ligas, default=ligas[:5], key='filtro_liga') 

        df_final = df_filtrado[
            (df_filtrado['Casa'].isin(casas_selecionadas)) &
            (df_filtrado['Liga'].isin(ligas_selecionadas))
        ].copy()
        
        
        if df_final.empty:
            st.warning(f"Nenhum jogo encontrado para a data {data_selecionada.strftime('%d/%m/%Y')} e filtros atuais.")
        else:
            # Formata a coluna de data para exibição
            df_final['Data_Hora'] = pd.to_datetime(df_final['Data_Hora']).dt.strftime('%d/%m %H:%M')
            
            # Colunas exibidas
            df_display = df_final[['Casa', 'ID_Evento', 'Liga', 'Jogo', 'Data_Hora', 'Odd_1', 'Odd_X', 'Odd_2']].rename(columns={'ID_Evento': 'ID'})
            
            st.subheader(f"Selecione um evento para Aposta Rápida:")
            
            # --- CAPTURA DA SELEÇÃO: st.dataframe ---
            event = st.dataframe(
                df_display, 
                use_container_width=True, 
                hide_index=True,
                column_config={"ID": st.column_config.Column(disabled=True, width="small")},
                selection_mode="single-row",
                on_select="rerun", 
                key='tabela_odds_selecao' 
            )
            
            selected_indices = event.selection.get('rows', []) 

            if not selected_indices:
                st.info("Clique em uma linha da tabela acima para preencher o formulário de Aposta Rápida.")
            else:
                st.markdown("---")
                st.markdown("### ⚡ Aposta Rápida (Evento Selecionado)")
                
                selected_index_in_df_final = df_final.index[selected_indices[0]] 
                row = df_final.loc[selected_index_in_df_final]
                
                # --- FORMULÁRIO DE APOSTA RÁPIDA ---
                col_rapida1, col_rapida2, col_rapida3 = st.columns(3)
                
                with col_rapida1:
                    st.text_input("Casa", value=row['Casa'], disabled=True, key='rap_casa_disp')
                    
                    st.selectbox("Mercado", 
                        ['Vencedor da Partida (1X2)', 'Acima de 2.5 Gols', 'Ambas Marcam', 'Handicap Asiático'], 
                        key='rap_mercado'
                    )
                    
                with col_rapida2:
                    st.text_input("Jogo", value=row['Jogo'], disabled=True, key='rap_jogo_disp')
                    odd_selecionada = st.number_input("Odd", min_value=1.01, step=0.01, format="%.2f", value=row['Odd_1'], key='rap_odd') 
                    
                with col_rapida3:
                    valor_rapido = st.number_input("Valor Apostado (R$)", min_value=0.01, step=5.00, format="%.2f", key='rap_valor')
                    
                # NOVO CAMPO: PROGNÓSTICO
                rap_prognostico = st.text_input("Prognóstico/Seleção (Ex: Time A, 1, Over 2.5)", key='rap_prognostico')

                saldo_disp = st.session_state['saldos'].get(row['Casa'], 0.00)
                st.caption(f"Saldo Disponível em {row['Casa']}: R$ {saldo_disp:.2f}")

                if st.button(f"✅ Registrar Aposta de R$ {valor_rapido:.2f}", key='btn_rapida'):
                    if valor_rapido > 0 and valor_rapido <= saldo_disp and rap_prognostico:
                        
                        # CORREÇÃO AQUI: Garantindo que todos os 7 argumentos sejam passados na ordem correta.
                        aposta_id = insert_aposta(
                            row['Casa'], 
                            row['Liga'], 
                            row['Jogo'], 
                            st.session_state['rap_mercado'],
                            rap_prognostico,  # <-- Prognostico (5º arg)
                            st.session_state['rap_odd'], # <-- Odd (6º arg)
                            valor_rapido # <-- Valor (7º arg)
                        )
                        
                        if aposta_id:
                            novo_saldo = saldo_disp - valor_rapido
                            update_saldo(row['Casa'], novo_saldo)
                            refresh_data()
                            st.success(f"Aposta ID {aposta_id} registrada para {row['Jogo']}!")
                    else:
                        st.error("Preencha o Prognóstico e verifique o saldo/valor.")


with tab_apostas:
    st.header("📝 Registro Manual de Aposta")
    
    col_reg1, col_reg2, col_reg3 = st.columns(3)
    
    with col_reg1:
        reg_casa = st.selectbox("Casa de Aposta", ['Sportingbet', 'Superbet'], key='reg_casa')
        
        reg_mercado = st.selectbox("Mercado", 
            ['Vencedor da Partida (1X2)', 'Acima de 2.5 Gols', 'Ambas Marcam', 'Handicap Asiático', 'Outro'], 
            key='reg_mercado'
        )
        
        # NOVO CAMPO NO REGISTRO MANUAL
        reg_prognostico = st.text_input("Prognóstico/Seleção (Ex: Time A, X, Under 1.5)", key='reg_prognostico')


    with col_reg2:
        reg_liga = st.text_input("Liga/Campeonato", key='reg_liga')
        reg_odd = st.number_input("Odd", min_value=1.01, step=0.01, format="%.2f", key='reg_odd')

    with col_reg3:
        reg_jogo = st.text_input("Evento/Jogo", key='reg_jogo')
        reg_valor = st.number_input("Valor Apostado (Stake R$)", min_value=0.01, step=5.00, format="%.2f", key='reg_valor')

    saldo_disp = st.session_state['saldos'].get(reg_casa, 0.00)
    st.markdown(f"**Saldo Disponível em {reg_casa}: R$ {saldo_disp:.2f}**")
    
    if st.button("✅ Registrar Aposta e Deduzir Saldo", use_container_width=True, key='btn_manual'):
        if reg_valor > 0 and reg_valor <= saldo_disp and reg_prognostico:
            
            # CORREÇÃO AQUI: Garantindo que todos os 7 argumentos sejam passados na ordem correta.
            aposta_id = insert_aposta(
                reg_casa, 
                reg_liga, 
                reg_jogo, 
                reg_mercado, 
                reg_prognostico, # <-- Prognostico (5º arg)
                reg_odd, # <-- Odd (6º arg)
                reg_valor # <-- Valor (7º arg)
            )
            
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
            st.error("Valor inválido! Preencha o Prognóstico e verifique o saldo/valor.")

    st.markdown("---")
    st.subheader("🛠️ Resolver Aposta Pendente")

    # Tratamento de segurança para df_apostas
    df_apostas = st.session_state.get('apostas_data', pd.DataFrame())
    
    if df_apostas.empty or 'Status' not in df_apostas.columns:
        df_pendentes = pd.DataFrame()
        st.info("Nenhuma aposta registrada. Registre uma aposta primeiro.")
    else:
        df_pendentes = df_apostas[df_apostas['Status'] == 'AGUARDANDO']
        
        if df_pendentes.empty:
            st.info("Nenhuma aposta pendente para resolver.")
        else:
            # Puxa os IDs das apostas pendentes
            opcoes_id = df_pendentes['ID_Aposta'].tolist()
            
            col_res1, col_res2, col_res3 = st.columns(3)

            with col_res1:
                id_selecionado = st.selectbox("Selecione o ID da Aposta", opcoes_id, key='res_id')
                
                aposta_selecionada_df = df_pendentes[df_pendentes['ID_Aposta'] == id_selecionado]
                if not aposta_selecionada_df.empty:
                    aposta_selecionada = aposta_selecionada_df.iloc[0]
                    st.caption(f"Jogo: {aposta_selecionada['Jogo']}")
                    st.caption(f"Stake: R$ {aposta_selecionada['Valor_Apostado']:.2f}")
                else:
                    aposta_selecionada = None

            with col_res2:
                novo_status = st.selectbox("Status Final", ['GREEN', 'RED', 'CASHOUT'], key='res_status')
                
            # --- LÓGICA DE PRÉ-PREENCHIMENTO DO VALOR DE RETORNO ---
            default_return_value = 0.00
            if aposta_selecionada is not None:
                stake = aposta_selecionada['Valor_Apostado']
                odd = aposta_selecionada['Odd']

                if st.session_state['res_status'] == 'GREEN':
                    default_return_value = stake * odd
                elif st.session_state['res_status'] == 'RED':
                    default_return_value = 0.00
                else: 
                    default_return_value = stake 
            # --- FIM DA LÓGICA DE PRÉ-PREENCHIMENTO ---

            with col_res3:
                valor_retorno = st.number_input(
                    "Valor TOTAL Recebido (R$, Incluindo Stake)", 
                    min_value=0.00, 
                    value=default_return_value, 
                    step=1.00, 
                    format="%.2f", 
                    key='res_retorno'
                )

            if st.button("✅ Atualizar Resultado e Saldo", use_container_width=True, key='btn_resolver') and aposta_selecionada is not None:
                valor_apostado = aposta_selecionada['Valor_Apostado']
                casa_aposta = aposta_selecionada['Casa']
                
                # Lógica para Lucro/Prejuízo:
                if novo_status == 'RED':
                    valor_retorno_final = 0.00
                    lucro = -valor_apostado 
                else:
                    valor_retorno_final = valor_retorno
                    lucro = valor_retorno - valor_apostado

                # 1. Atualiza o status e o retorno no DB
                update_aposta_resultado(id_selecionado, novo_status, valor_retorno_final)

                # 2. Atualiza o saldo:
                saldo_atual = st.session_state['saldos'].get(casa_aposta, 0.00)
                novo_saldo_final = saldo_atual + valor_retorno_final 
                
                update_saldo(casa_aposta, novo_saldo_final)
                
                refresh_data() 
                st.success(f"Aposta ID {id_selecionado} resolvida como {novo_status}! Lucro: R$ {lucro:.2f}.")


    st.markdown("---")
    st.subheader("Histórico de Apostas Registradas")
    
    # Tabela com histórico de apostas
    if df_apostas.empty:
        st.info("Nenhuma aposta registrada ainda.")
    else:
        st.dataframe(df_apostas, use_container_width=True)


with tab_performance:
    st.header("📊 Dashboard de Performance")
    
    df_apostas = st.session_state['apostas_data']
    
    if df_apostas.empty or 'Status' not in df_apostas.columns:
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
