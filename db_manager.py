# db_manager.py (VERSÃO FINAL 1.3 - CORREÇÃO DE KEYERROR)

import sqlite3
from datetime import datetime
import pandas as pd

DATABASE_NAME = 'bet_manager.db'

def setup_database():
    """
    Cria o banco de dados e as tabelas (saldos e apostas) se elas não existirem.
    Garante que a tabela 'apostas' tenha as colunas Status e Valor_Retorno.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Tabela saldos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saldos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            casa TEXT NOT NULL,
            saldo REAL NOT NULL,
            data_atualizacao TEXT NOT NULL
        )
    """)

    # Tabela apostas
    # Garante as colunas que o Pandas espera
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            casa TEXT NOT NULL,
            liga TEXT,
            jogo TEXT NOT NULL,
            mercado TEXT NOT NULL,
            odd REAL NOT NULL,
            valor_apostado REAL NOT NULL,
            valor_retorno REAL DEFAULT 0.00,  
            status TEXT DEFAULT 'AGUARDANDO', 
            data_registro TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def update_saldo(casa: str, novo_saldo: float):
    """Atualiza o saldo atual da casa de aposta."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Remove a entrada anterior e insere a nova
    cursor.execute("DELETE FROM saldos WHERE casa = ?", (casa,))
    cursor.execute("INSERT INTO saldos (casa, saldo, data_atualizacao) VALUES (?, ?, ?)",
                   (casa, novo_saldo, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def get_latest_saldo(casa: str) -> float:
    """Puxa o saldo mais recente de uma casa."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # Seleciona o último saldo registrado para a casa
    cursor.execute("SELECT saldo FROM saldos WHERE casa = ? ORDER BY data_atualizacao DESC LIMIT 1", (casa,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else 0.00

def insert_aposta(casa: str, liga: str, jogo: str, mercado: str, odd: float, valor_apostado: float) -> int:
    """Insere uma nova aposta no banco de dados."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO apostas (casa, liga, jogo, mercado, odd, valor_apostado, data_registro) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (casa, liga, jogo, mercado, odd, valor_apostado, datetime.now().isoformat()))
    
    aposta_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return aposta_id

def get_all_apostas() -> pd.DataFrame:
    """Puxa todas as apostas e retorna como um DataFrame do Pandas, garantindo o nome das colunas."""
    conn = sqlite3.connect(DATABASE_NAME)
    
    # Puxa todas as colunas
    df = pd.read_sql_query("SELECT id, casa, liga, jogo, mercado, odd, valor_apostado, valor_retorno, status, data_registro FROM apostas ORDER BY data_registro DESC", conn)
    
    conn.close()
    
    # Se o DataFrame não estiver vazio, renomeamos as colunas com a capitalização correta
    if not df.empty:
        df = df.rename(columns={
            'id': 'ID_Aposta',
            'casa': 'Casa',
            'liga': 'Liga',
            'jogo': 'Jogo',
            'mercado': 'Mercado',
            'odd': 'Odd',
            'valor_apostado': 'Valor_Apostado',
            'valor_retorno': 'Valor_Retorno',
            'status': 'Status',  # <--- CORREÇÃO AQUI! O Pandas está lendo 'status' minúsculo
            'data_registro': 'Data_Registro'
        })
        
        # Garante a tipagem correta para Data_Registro
        df['Data_Registro'] = pd.to_datetime(df['Data_Registro'])
        
        # Reordena as colunas para exibição
        df = df[['ID_Aposta', 'Casa', 'Liga', 'Jogo', 'Mercado', 'Odd', 'Valor_Apostado', 'Valor_Retorno', 'Status', 'Data_Registro']]
        
    return df

def update_aposta_resultado(aposta_id: int, status: str, valor_retorno: float):
    """Atualiza o status e o valor de retorno de uma aposta."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE apostas 
        SET status = ?, valor_retorno = ?
        WHERE id = ?
    """, (status, valor_retorno, aposta_id))
    
    conn.commit()
    conn.close()
