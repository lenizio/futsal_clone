import psycopg2
from psycopg2 import sql
import streamlit as st

class DBManager:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                host=st.secrets.DB_HOST,
                port=st.secrets.DB_PORT,
                database=st.secrets.DB_NAME,
                user=st.secrets.DB_USER,
                password=st.secrets.DB_PASSWORD,
                sslmode="require"
            )
            self.cursor = self.conn.cursor()
        except psycopg2.OperationalError as e:
            print(f"Erro de conexão: {e}")
            raise
    
    def criar_tabelas(self):
        comandos = [
            """
            CREATE TABLE IF NOT EXISTS equipes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                categoria VARCHAR(50) NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogadores (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                numero_camisa INT NOT NULL,
                equipe_id INT NOT NULL REFERENCES equipes(id) ON DELETE CASCADE,
                equipe VARCHAR(100) NOT NULL,
                posicao VARCHAR(50) NOT NULL,
                CONSTRAINT unique_numero_camisa_por_equipe UNIQUE (equipe_id, numero_camisa)

            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogos (
                id SERIAL PRIMARY KEY,
                equipe_mandante_id INT NOT NULL REFERENCES equipes(id) ON DELETE CASCADE,
                equipe_mandante_nome VARCHAR(100) NOT NULL,
                equipe_visitante_id INT NOT NULL REFERENCES equipes(id)ON DELETE CASCADE,
                equipe_visitante_nome VARCHAR(100) NOT NULL,
                data DATE NOT NULL,
                fase VARCHAR(50),
                rodada VARCHAR(50),
                competicao VARCHAR(100)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogadas (
                id SERIAL PRIMARY KEY,
                jogador_id BIGINT NOT NULL REFERENCES jogadores(id) ON DELETE CASCADE,
                jogador_nome VARCHAR(100) NOT NULL,
                jogo_id INT NOT NULL REFERENCES jogos(id) ON DELETE CASCADE,
                jogada VARCHAR(255) NOT NULL,
                x_loc FLOAT NOT NULL,
                y_loc FLOAT NOT NULL
            )
            """
        ]
        for comando in comandos:
            self.cursor.execute(comando)
        self.conn.commit()

    def verificar_equipe_existente(self, nome, categoria):
        nome=nome.strip()
        
        self.cursor.execute(
            """
            SELECT id FROM equipes
            WHERE nome = %s AND categoria = %s
            """,
            (nome, categoria)
        )
        return self.cursor.fetchone()  # Retorna None se não encontrar
    
    def verificar_jogador_por_nome(self, nome, equipe_id):
        self.cursor.execute(
            """
            SELECT 1 FROM jogadores WHERE nome = %s AND equipe_id = %s
            """,
            (nome, equipe_id)
        )
        resultado = self.cursor.fetchone()
        if resultado:
            return "Jogador já cadastrado com este nome."

    def verificar_jogador_por_numero_camisa(self, numero_camisa, equipe_id):
        self.cursor.execute(
            """
            SELECT 1 FROM jogadores WHERE numero_camisa = %s AND equipe_id = %s
            """,
            (numero_camisa, equipe_id)
        )
        resultado = self.cursor.fetchone()
        if resultado:
            return "Já existe um jogador com este número de camisa no equipe."

    
    def adicionar_equipe(self, nome, categoria):
    # Verificar se o equipe já existe
        if self.verificar_equipe_existente(nome, categoria):
            return None

        # Inserir o novo equipe
        self.cursor.execute(
            """
            INSERT INTO equipes (nome, categoria)
            VALUES (%s, %s)
            RETURNING id
            """,
            (nome, categoria)
        )
        self.conn.commit()
        novo_id = self.cursor.fetchone()[0]
        return novo_id


    def adicionar_jogador(self, nome, equipe_id, equipe_nome, posicao, numero_camisa):
    # Verificar se o jogador já existe pelo nome
        erro_nome = self.verificar_jogador_por_nome(nome, equipe_id)
        if erro_nome:
            return erro_nome  # Retorna a mensagem de erro se o nome já existir

        # Verificar se já existe um jogador com o mesmo número de camisa no equipe
        erro_numero_camisa = self.verificar_jogador_por_numero_camisa(numero_camisa, equipe_id)
        if erro_numero_camisa:
            return erro_numero_camisa  # Retorna a mensagem de erro se o número da camisa já estiver em uso


        # Inserir o novo jogador
        self.cursor.execute(
            """
            INSERT INTO jogadores (nome, equipe_id, equipe, posicao, numero_camisa)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nome, equipe_id, equipe_nome, posicao, numero_camisa)
        )
        self.conn.commit()
        novo_id = self.cursor.lastrowid
        return novo_id


    def adicionar_jogo(self, equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, fase, rodada, competicao):
        self.cursor.execute(
            """
            INSERT INTO jogos (equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, fase, rodada, competicao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, fase, rodada, competicao)
        )
        self.conn.commit()
        return self.cursor.fetchone()[0]

    def adicionar_jogada(self, jogador_id, jogador_nome, jogo_id, jogada, x_loc, y_loc):
        self.cursor.execute(
            """
            INSERT INTO jogadas (jogador_id, jogador_nome, jogo_id, jogada, x_loc, y_loc)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (jogador_id, jogador_nome, jogo_id, jogada, x_loc, y_loc)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    # Listar todos os equipes
    def listar_equipes(self):
        self.cursor.execute("SELECT id, nome, categoria FROM equipes")
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    # Listar todos os jogadores
    def listar_jogadores(self):
        self.cursor.execute("SELECT id, nome, equipe, posicao FROM jogadores")
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    # Listar todos os jogos
    def listar_jogos(self):
        self.cursor.execute("SELECT id,equipe_mandante_id,equipe_mandante_nome,equipe_visitante_id, equipe_visitante_nome,data,  competicao, fase, rodada FROM jogos ORDER BY data DESC")
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    # Listar todas as jogadas
    def listar_jogadas(self):
        self.cursor.execute("SELECT * FROM jogadas")
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    # Listar jogadores por equipe
    def listar_jogadores_por_equipe(self, equipe_id):
        self.cursor.execute("SELECT id, nome, posicao, numero_camisa FROM jogadores WHERE equipe_id = %s", (equipe_id,))
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    # Listar jogos por equipe e competição
    def listar_jogos_por_equipe_e_competicao(self, equipe_id, competicao):
        self.cursor.execute(
            """
            SELECT * FROM jogos
            WHERE (equipe_mandante_id = %s OR equipe_visitante_id = %s) AND competicao = %s
            """,
            (equipe_id, equipe_id, competicao)
        )
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    # Listar jogadas por jogo
    def listar_jogadas_por_jogo(self, jogo_id):
        self.cursor.execute("SELECT * FROM jogadas WHERE jogo_id = %s", (jogo_id,))
        return self.cursor.fetchall()  # Retorna uma lista de tuplas
    
    def listar_detalhes_jogo(self, jogo_id):
        self.cursor.execute("SELECT equipe_mandante_id, equipe_mandante_nome,equipe_visitante_id ,equipe_visitante_nome,data,fase,rodada,competicao FROM jogos WHERE id = %s",(jogo_id,))
        self.conn.commit()
        return self.cursor.fetchone()
        
    def deletar_equipe(self, equipe_id):
        self.cursor.execute("DELETE FROM equipes WHERE id = %s", (equipe_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def deletar_jogador(self, jogador_id):
        self.cursor.execute("DELETE FROM jogadores WHERE id = %s", (jogador_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def deletar_jogo(self, jogo_id):
        self.cursor.execute("DELETE FROM jogos WHERE id = %s", (jogo_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def deletar_jogada(self, jogada_id):
        self.cursor.execute("DELETE FROM jogadas WHERE id = %s", (jogada_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def fechar_conexao(self):
        self.cursor.close()
        self.conn.close()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False
