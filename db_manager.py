# db_manager.py (VERSÃO FINAL E CORRIGIDA)

import sqlite3
from datetime import datetime
import pandas as pd
import os # Necessário para criar a pasta 'data'

# Nome do arquivo do banco de dados.
DB_NAME = 'data/bet_data.db'

def setup_database():
    """
    Cria a pasta 'data/' e as tabelas do banco de dados se elas não existirem.
    """
    
    # 1. GARANTE QUE A PASTA DATA EXISTA
    if not os.path.exists('data'):
        os.makedirs('data')
        
    conn = None # Inicializa conn para ser usado no 'finally'
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 1. Tabela de Saldo (Para histórico financeiro)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saldo (
                casa TEXT NOT NULL,
                saldo REAL NOT NULL,
                data_atualizacao TEXT NOT NULL,
                PRIMARY KEY (casa, data_atualizacao)
            );
        """)

        # 2. Tabela de Apostas (Sem chave estrangeira para evitar falha na criação)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apostas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                casa TEXT NOT NULL,
                liga TEXT,
                jogo TEXT,
                mercado TEXT NOT NULL,
                odd REAL NOT NULL,
                valor REAL NOT NULL,
                data_aposta TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'AGUARDANDO',
                lucro REAL DEFAULT 0.00
            );
        """)
        
        # ESTE COMMIT É CRÍTICO!
        conn.commit() 
        print("Estrutura do banco de dados verificada/criada com sucesso.")
        
    except sqlite3.Error as e:
        print(f"Erro ao configurar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()

# --- Funções de Saldo ---

def update_saldo(casa: str, novo_saldo: float):
    """Atualiza o saldo atual de uma casa de aposta."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        cursor.execute("""
            INSERT INTO saldo (casa, saldo, data_atualizacao) 
            VALUES (?, ?, ?);
        """, (casa, novo_saldo, data_hora))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao atualizar saldo: {e}")
        return False
    finally:
        conn.close()

def get_latest_saldo(casa: str):
    """Busca o saldo mais recente de uma casa de aposta."""
    conn = sqlite3.connect(DB_NAME)
    
    # Buscamos a entrada mais recente para a casa específica
    cursor = conn.cursor()
    cursor.execute("""
        SELECT saldo FROM saldo 
        WHERE casa = ? 
        ORDER BY data_atualizacao DESC 
        LIMIT 1;
    """, (casa,))
    
    result = cursor.fetchone()
    conn.close()
    
    # Retorna o saldo ou 0.0 se não houver registros
    return result[0] if result else 0.0

# --- Funções de Aposta ---

def insert_aposta(casa: str, liga: str, jogo: str, mercado: str, odd: float, valor: float):
    """Registra uma nova aposta no sistema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        cursor.execute("""
            INSERT INTO apostas (casa, liga, jogo, mercado, odd, valor, data_aposta) 
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (casa, liga, jogo, mercado, odd, valor, data_hora))
        
        conn.commit()
        return cursor.lastrowid # Retorna o ID da aposta criada
    except sqlite3.Error as e:
        print(f"Erro ao inserir aposta: {e}")
        return None
    finally:
        conn.close()

def get_all_apostas():
    """Busca todas as apostas feitas (para o dashboard e a aba de apostas)."""
    conn = sqlite3.connect(DB_NAME)
    # Retorna os dados como um DataFrame do Pandas para facilitar a análise
    try:
        df = pd.read_sql_query("SELECT * FROM apostas ORDER BY data_aposta DESC;", conn)
    except pd.io.sql.DatabaseError:
        # Se a tabela não existir, retorna um DataFrame vazio para não quebrar o Streamlit
        df = pd.DataFrame()
        
    conn.close()
    return df

def update_aposta_resultado(aposta_id: int, status: str, lucro: float):
    """Atualiza o resultado (GREEN/RED/CASHOUT) e o lucro de uma aposta."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE apostas 
            SET status = ?, lucro = ? 
            WHERE id = ?;
        """, (status, lucro, aposta_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Erro ao atualizar resultado: {e}")
        return False
    finally:
        conn.close()