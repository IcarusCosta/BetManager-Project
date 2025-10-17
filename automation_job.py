# automation_job.py

import pandas as pd
from db_manager import get_all_apostas, update_aposta_resultado, get_latest_saldo, update_saldo
# A falha acontecia aqui. Garantimos que bet_api.py tem esta função.
from bet_api import check_event_result_simulated 
import time

def run_result_automation():
    """
    Verifica todas as apostas em AGUARDANDO e tenta resolvê-las (simulado).
    """
    print("Iniciando rotina de automação de resultados...")
    
    # 1. Puxa todas as apostas em aberto
    df_apostas = get_all_apostas()
    apostas_abertas = df_apostas[df_apostas['status'] == 'AGUARDANDO']
    
    if apostas_abertas.empty:
        print("Nenhuma aposta pendente para verificar.")
        return 0

    count_updated = 0
    
    for index, aposta in apostas_abertas.iterrows():
        aposta_id = aposta['id']
        casa = aposta['casa']
        valor = aposta['valor']
        odd = aposta['odd']
        jogo = aposta['jogo']
        
        # 2. Verifica o resultado (Simulado usando o ID da aposta)
        simulated_event_id = str(aposta_id) 
        
        novo_status, multiplicador_lucro_liquido = check_event_result_simulated(simulated_event_id)
        
        if novo_status != "AGUARDANDO":
            
            if novo_status == "GREEN":
                lucro_liquido = (valor * odd) - valor
            elif novo_status == "RED":
                lucro_liquido = -valor
            elif novo_status == "CASHOUT":
                lucro_liquido = valor * 0.2 
            else:
                lucro_liquido = 0.00 

            # 3. Atualiza a aposta no DB
            update_aposta_resultado(aposta_id, novo_status, lucro_liquido)
            
            # 4. Atualiza o saldo
            saldo_casa_atual = get_latest_saldo(casa)
            novo_saldo_casa = saldo_casa_atual + lucro_liquido
            update_saldo(casa, novo_saldo_casa)
            
            print(f"-> Aposta {aposta_id} ({jogo}): Resolvida como {novo_status}. Lucro R${lucro_liquido:.2f}")
            count_updated += 1
        
        time.sleep(0.1)

    print(f"Rotina de automação finalizada. {count_updated} apostas atualizadas.")
    return count_updated

if __name__ == '__main__':
    run_result_automation()