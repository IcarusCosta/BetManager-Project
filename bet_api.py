# bet_api.py (VERSÃO FINAL COM DADOS TOTALMENTE SIMULADOS PARA GARANTIR FUNCIONALIDADE E HOSPEDAGEM)

import requests
import pandas as pd
from datetime import datetime, timedelta
import time 

# --- Configurações de Dados Simulados ---

# Cria um DataFrame de jogos simulados para 30 dias
def generate_simulated_odds_data():
    data_hoje = datetime.now().date()
    
    dados = []
    
    # Gerar 5 jogos por dia para 30 dias
    for i in range(30):
        data_jogo = data_hoje + timedelta(days=i)
        
        ligas = ["Premier League (Sim.)", "Brasileirão Série A (Sim.)", "La Liga (Sim.)"]
        jogos_simulados = [
            ("Time A", "Time B", ligas[0]),
            ("Time X", "Time Y", ligas[1]),
            ("Time do Ícaro", "Time Gênesis", ligas[2]),
            ("Flamengo", "Vasco", ligas[1]),
            ("Manchester Utd", "Liverpool", ligas[0])
        ]
        
        for j, (time_casa, time_fora, liga) in enumerate(jogos_simulados):
            # IDs de Evento únicos (Simulados)
            event_id = f"SIM_{data_jogo.strftime('%Y%m%d')}_{j}" 
            
            # Odds Simuladas
            odd_1_sb = round(1.80 + (i * 0.01) + (j * 0.05), 2)
            odd_x_sb = round(3.20 - (i * 0.01), 2)
            odd_2_sb = round(4.00 - (j * 0.05), 2)
            
            # Superbet (Casa 1)
            dados.append({
                'Casa': 'Superbet', 
                'ID_Evento': event_id,
                'Liga': liga,
                'Jogo': f"{time_casa} vs {time_fora}",
                'Data_Hora': datetime.combine(data_jogo, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S'),
                'Odd_1': odd_1_sb,
                'Odd_X': odd_x_sb,
                'Odd_2': odd_2_sb
            })
            
            # Sportingbet (Casa 2 - Odds Ligeiramente Diferentes)
            dados.append({
                'Casa': 'Sportingbet', 
                'ID_Evento': event_id,
                'Liga': liga,
                'Jogo': f"{time_casa} vs {time_fora}",
                'Data_Hora': datetime.combine(data_jogo, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S'),
                'Odd_1': odd_1_sb + 0.05,
                'Odd_X': odd_x_sb - 0.05,
                'Odd_2': odd_2_sb + 0.10
            })
            
    return pd.DataFrame(dados)


# --- Funções de Coleta de Dados (Simuladas) ---

def get_all_prematch_odds():
    """Puxa dados SIMULADOS para garantir a funcionalidade do app."""
    
    print("Gerando dados de odds simulados para 30 dias.")
    df_all = generate_simulated_odds_data()
    return df_all


# Função de Simulação de Resultado (para o automation_job.py)
def check_event_result_simulated(event_id: str):
    """Simula a checagem do resultado de um evento."""
    # Como os IDs são SIM_AAAA-MM-DD_J (J=0 a 4), usamos o último dígito para simular resultado
    if event_id.endswith('1'): # Simula aposta perdida
        return "RED", -1.00 
    elif event_id.endswith('2'): # Simula cashout parcial
        return "CASHOUT", 0.50 
    elif event_id.endswith('3'): # Simula aposta ganha
        return "GREEN", 1.55 
    else:
        return "AGUARDANDO", 0.00