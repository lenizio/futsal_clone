import psycopg2
from psycopg2 import sql
import streamlit as st
import pandas as pd


class DBManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=st.secrets["connections.postgresql"]["host"],
                port=st.secrets["connections.postgresql"]["port"],
                database=st.secrets["connections.postgresql"]["database"],
                user=st.secrets["connections.postgresql"]["username"],
                password=st.secrets["connections.postgresql"]["password"],
            )
            self.cursor = self.conn.cursor()
        except psycopg2.OperationalError as e:
            print(f"Erro de conexão: {e}")
            raise
    
    def criar_tabelas(self):
        comandos = [
            """
            CREATE TABLE IF NOT EXISTS times (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                categoria VARCHAR(50) NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogadores (
                id BIGINT PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                time_id INT NOT NULL REFERENCES times(id) ON DELETE CASCADE,
                time VARCHAR(100) NOT NULL,
                posicao VARCHAR(50) NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogos (
                id SERIAL PRIMARY KEY,
                time_mandante_id INT NOT NULL REFERENCES times(id),
                time_mandante_nome VARCHAR(100) NOT NULL,
                time_visitante_id INT NOT NULL REFERENCES times(id),
                time_visitante_nome VARCHAR(100) NOT NULL,
                data DATE NOT NULL,
                fase VARCHAR(50),
                rodada VARCHAR(50),
                competicao VARCHAR(100)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogadas (
                id SERIAL PRIMARY KEY,
                jogador_id BIGINT NOT NULL REFERENCES jogadores(id),
                jogador_nome VARCHAR(100) NOT NULL,
                jogo_id INT NOT NULL REFERENCES jogos(id) ON DELETE CASCADE,
                jogada VARCHAR(255) NOT NULL,
                localizacao VARCHAR(100)
            )
            """
        ]
        for comando in comandos:
            self.cursor.execute(comando)
        self.conn.commit()
