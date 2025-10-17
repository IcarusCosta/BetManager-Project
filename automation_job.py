# automation_job.py (VERSÃO CORRIGIDA - Key Error 'status')

import random
import time
import pandas as pd
from db_manager import get_all_apostas, update_aposta_resultado, update_saldo, get_latest_saldo

def run_result_automation():
    # 1. Obter todas as apostas
    df_apostas = get_all_apostas()

    if df_apostas.empty:
        return 0

    # 2. Filtrar apenas as apostas 'AGUARDANDO'
    # CORREÇÃO AQUI: Usando 'Status' (com 'S' maiúsculo)
    apostas_abertas = df_apostas[df_apostas['Status'] == 'AGUARDANDO'] 

    if apostas_abertas.empty:
        return 0

    updated_count = 0

    # 3. Simular a verificação de resultados para cada aposta
    for index, aposta in apostas_abertas.iterrows():
        
        # Simulação de delay para a automação
        # time.sleep(0.01)

        # 4. Decidir o resultado (GREEN/RED/CASHOUT) de forma simulada
        resultados_possiveis = ['GREEN', 'RED'] 
        
        # A chance de GREEN é proporcional à ODD (quanto menor a ODD, maior a chance simulada de GREEN)
        # Odds menores que 2.0 têm chance maior de GREEN na simulação
        odd = aposta['Odd']
        
        if odd < 2.0:
            status_final = random.choices(resultados_possiveis, weights=[0.65, 0.35], k=1)[0]
        else:
            status_final = random.choices(resultados_possiveis, weights=[0.45, 0.55], k=1)[0]
            
        valor_apostado = aposta['Valor_Apostado']
        casa_aposta = aposta['Casa']
        
        # 5. Calcular Retorno e Lucro
        if status_final == 'GREEN':
            # Simula Retorno Total (Stake * Odd)
            valor_retorno = valor_apostado * odd
            lucro = valor_retorno - valor_apostado
        else: # RED
            valor_retorno = 0.00
            lucro = -valor_apostado

        # 6. Atualizar o banco de dados
        
        # Aposta
        update_aposta_resultado(aposta['ID_Aposta'], status_final, valor_retorno)
        
        # Saldo
        saldo_atual = get_latest_saldo(casa_aposta)
        novo_saldo_final = saldo_atual + valor_retorno
        update_saldo(casa_aposta, novo_saldo_final)

        updated_count += 1

    return updated_count
