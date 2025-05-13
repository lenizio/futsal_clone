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
                image_id VARCHAR(255) DEFAULT NULL,
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
                tempo VARCHAR(10) NOT NULL,
                x_loc FLOAT NOT NULL,
                y_loc FLOAT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS gols (
                id SERIAL PRIMARY KEY,
                -- Informações do Jogo
                jogo_id INT NOT NULL REFERENCES jogos(id) ON DELETE CASCADE,
                
                -- Contexto do Gol
                equipe_analisada_id INT NOT NULL REFERENCES equipes(id) ON DELETE CASCADE,
                tipo_gol VARCHAR(7) NOT NULL ,
                tempo VARCHAR(10) NOT NULL,
                caracteristica VARCHAR(255) NOT NULL,
                x_loc FLOAT NOT NULL,
                y_loc FLOAT NOT NULL,
                
                -- Detalhes específicos para gols da própria equipe
                autor_gol_id INT REFERENCES jogadores(id) ON DELETE SET NULL,
                assistente_id INT REFERENCES jogadores(id) ON DELETE SET NULL,
                jogadores_em_quadra INT[] NOT NULL DEFAULT ARRAY[]::INT[]
    
)
            
            """,
            # """
            # CREATE TABLE IF NOT EXISTS gols (
            #     id SERIAL PRIMARY KEY,
            #     equipe_mandante_id INT NOT NULL REFERENCES equipes(id) ON DELETE CASCADE,
            #     equipe_mandante_nome VARCHAR(100) NOT NULL,
            #     nome VARCHAR(100) NOT NULL,
            #     numero_camisa INT NOT NULL,
            #     equipe_id INT NOT NULL REFERENCES equipes(id) ON DELETE CASCADE,
            #     equipe VARCHAR(100) NOT NULL,
            #     posicao VARCHAR(50) NOT NULL,
            #     image_id VARCHAR(255) DEFAULT NULL,
            #     CONSTRAINT unique_numero_camisa_por_equipe UNIQUE (equipe_id, numero_camisa)

            # )
            # """
        ]
        for comando in comandos:
            self.cursor.execute(comando)
        self.conn.commit()
        
    def rollback(self):
        self.conn.rollback()

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
    
    def verificar_jogador_por_nome(self, nome, equipe_id,jogador_id=None):
        self.cursor.execute(
                    """
                    SELECT 1 FROM jogadores WHERE nome = %s AND equipe_id = %s AND id != %s
                    """,
                    (nome, equipe_id, jogador_id)
                )
        resultado = self.cursor.fetchone()
        if resultado:
            return "Jogador já cadastrado com este nome."

    def verificar_jogador_por_numero_camisa(self, numero_camisa, equipe_id,jogador_id=None):
        self.cursor.execute(
            """
            SELECT 1 FROM jogadores WHERE numero_camisa = %s AND equipe_id = %s AND id != %s
                    """,
                (numero_camisa, equipe_id, jogador_id)
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


    def adicionar_jogador(self, nome, equipe_id, equipe_nome, posicao, numero_camisa, image_id=None):
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
            INSERT INTO jogadores (nome, equipe_id, equipe, posicao, numero_camisa, image_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (nome, equipe_id, equipe_nome, posicao, numero_camisa, image_id)
        )
        self.conn.commit()
        novo_id = self.cursor.lastrowid
        return novo_id
    
    def editar_jogador(self,equipe_id, jogador_id, nome=None, numero_camisa=None, posicao=None, image_id=None):
        campos = []
        valores = []

        if nome:
            campos.append("nome = %s")
            valores.append(nome)
        if numero_camisa:
            campos.append("numero_camisa = %s")
            valores.append(numero_camisa)
        if posicao:
            campos.append("posicao = %s")
            valores.append(posicao)
        if image_id:
            campos.append("image_id = %s")
            valores.append(image_id)
        
        erro_nome = self.verificar_jogador_por_nome(nome, equipe_id,jogador_id)
        if erro_nome:
            return erro_nome
        
        erro_numero_camisa = self.verificar_jogador_por_numero_camisa(numero_camisa, equipe_id,jogador_id)
        if erro_numero_camisa:
            return erro_numero_camisa    

        valores.append(jogador_id)

        comando = f"UPDATE jogadores SET {', '.join(campos)} WHERE id = %s"
        self.cursor.execute(comando, tuple(valores))
        self.conn.commit()



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

    def adicionar_jogada(self, jogador_id, jogador_nome, jogo_id, jogada, tempo, x_loc, y_loc):
        self.cursor.execute(
            """
            INSERT INTO jogadas (jogador_id, jogador_nome, jogo_id, jogada, tempo, x_loc, y_loc)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (jogador_id, jogador_nome, jogo_id, jogada, tempo, x_loc, y_loc)
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
        return self.cursor.fetchall()
    
    def listar_jogos_minas(self):
        self.cursor.execute("""SELECT id,equipe_mandante_id,equipe_mandante_nome,equipe_visitante_id, equipe_visitante_nome,data,  competicao, fase, rodada 
                            FROM jogos
                            WHERE equipe_mandante_nome LIKE 'Minas Tênis%'
                                OR equipe_visitante_nome LIKE 'Minas Tênis%' 
                            ORDER BY data DESC""")
        return self.cursor.fetchall()
    # Listar todas as jogadas
    def listar_jogadas(self):
        self.cursor.execute("SELECT * FROM jogadas")
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    # Listar jogadores por equipe
    def listar_jogadores_por_equipe(self, equipe_id):
        self.cursor.execute("SELECT id, nome, posicao, numero_camisa,image_id FROM jogadores WHERE equipe_id = %s", (equipe_id,))
        return self.cursor.fetchall()  # Retorna uma lista de tuplas
    
     # Listar jogadores por equipe
    def listar_nome_id_jogadores_por_equipe(self, equipe_id):
        self.cursor.execute("SELECT id, nome FROM jogadores WHERE equipe_id = %s", (equipe_id,))
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    # Listar jogos por equipe e competição
    def listar_jogos_por_equipe_e_competicao(self, equipe_id, competicao):
        self.cursor.execute(
            """
            SELECT * FROM jogos
            WHERE (equipe_mandante_id = %s OR equipe_visitante_id = %s) AND competicao = %s lksdjfkldsfj
            """,
            (equipe_id, equipe_id, competicao)
        )
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

   
    
    def listar_detalhes_jogo(self, jogo_id):
        self.cursor.execute("SELECT equipe_mandante_id, equipe_mandante_nome,equipe_visitante_id ,equipe_visitante_nome,data,fase,rodada,competicao FROM jogos WHERE id = %s",(jogo_id,))
        return self.cursor.fetchone()
    
    def listar_jogadas_por_jogo(self, jogo_id):
        self.cursor.execute("SELECT * FROM jogadas WHERE jogo_id = %s", (jogo_id,))
        return self.cursor.fetchall()  # Retorna uma lista de tuplas
   


    def listar_dados_analise_individual(self):
        self.cursor.execute("""
            SELECT
                    jogos.id,
                    jogos.equipe_mandante_nome,
                    jogos.equipe_visitante_nome,
                    jogos.fase,
                    jogos.rodada,
                    jogos.competicao,
                    jogadas.jogador_nome, 
                    jogadas.jogada,
                    jogadas.tempo,
                    jogadas.x_loc,
                    jogadas.y_loc
                FROM
                    jogos
                LEFT JOIN
                    jogadas
                ON
                    jogos.id = jogadas.jogo_id 
                    """ )
        return self.cursor.fetchall() 
    
    def listar_jogadas_por_partida(self,jogo_id):
        self.cursor.execute("""
            SELECT
                    jogos.equipe_mandante_nome,
                    jogos.equipe_visitante_nome,
                    jogos.fase,
                    jogos.rodada,
                    jogos.competicao,
                    jogadas.jogador_nome, 
                    jogadas.jogada,
                    jogadas.tempo,
                    jogadas.x_loc,
                    jogadas.y_loc
                FROM
                    jogos
                INNER JOIN
                    jogadas
                ON
                    jogos.id = jogadas.jogo_id
                WHERE
                    jogos.id = %s""", 
                    (jogo_id,)
                    )
        return self.cursor.fetchall() 
    
    
        
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

    def listar_gols(self):
        self.cursor.execute("""
            SELECT
                g.id, 
                jogos.equipe_mandante_nome,
                jogos.equipe_visitante_nome,
                jogos.competicao ,
                jogos.fase,
                jogos.rodada,
                e.nome  as equipe_analisada,
                g.tipo_gol,
                g.caracteristica,
                g.tempo ,
                j.nome AS gol_nome,
                a.nome  as assistente_nome,
                agg.jogadores_em_quadra_nomes,
                g.x_loc,
                g.y_loc
            FROM gols g
            LEFT JOIN jogos ON jogos.id = g.jogo_id
            LEFT JOIN equipes e ON e.id = g.equipe_analisada_id
            LEFT JOIN jogadores j ON j.id = g.autor_gol_id
            LEFT JOIN jogadores a ON a.id = g.assistente_id
            LEFT JOIN (
                SELECT 
                    g2.id AS gol_id,
                    array_agg(j2.nome) AS jogadores_em_quadra_nomes
                FROM gols g2
                LEFT JOIN jogadores j2 ON j2.id = ANY(g2.jogadores_em_quadra)
                GROUP BY g2.id
            ) agg ON agg.gol_id = g.id""")
        
        return self.cursor.fetchall()
    
    def listar_gols_por_equipe(self,equipe_id):
        self.cursor.execute("""
            SELECT 
                jogos.equipe_mandante_nome,
                jogos.equipe_visitante_nome,
                jogos.competicao ,
                jogos.fase,
                jogos.rodada,
                e.nome  as equipe_analisada,
                g.tipo_gol,
                g.caracteristica,
                g.tempo ,
                j.nome AS gol_nome,
                a.nome  as assistente_nome,
                agg.jogadores_em_quadra_nomes,
                g.x_loc,
                g.y_loc
            FROM gols g
            LEFT JOIN jogos ON jogos.id = g.jogo_id
            LEFT JOIN equipes e ON e.id = g.equipe_analisada_id
            LEFT JOIN jogadores j ON j.id = g.autor_gol_id
            LEFT JOIN jogadores a ON a.id = g.assistente_id
            LEFT JOIN (
                SELECT 
                    g2.id AS gol_id,
                    array_agg(j2.nome) AS jogadores_em_quadra_nomes
                FROM gols g2
                LEFT JOIN jogadores j2 ON j2.id = ANY(g2.jogadores_em_quadra)
                GROUP BY g2.id
            ) agg ON agg.gol_id = g.id
            WHERE
                g.equipe_analisada_id = %s""" ,
                (equipe_id,))
        
        return self.cursor.fetchall()
    
    def adicionar_gol(self, jogo_id, equipe_analisada_id, tipo_gol, tempo, caracteristica, x_loc, y_loc, jogadores_em_quadra=None, autor_gol_id=None, assistente_id=None):
    # Define a lista de jogadores em quadra como vazia se não for fornecida
        if jogadores_em_quadra is None:
            jogadores_em_quadra = []
    
        self.cursor.execute(
            """
            INSERT INTO gols (
                jogo_id, 
                equipe_analisada_id, 
                tipo_gol, 
                tempo, 
                caracteristica, 
                x_loc, 
                y_loc, 
                autor_gol_id, 
                assistente_id, 
                jogadores_em_quadra
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                jogo_id,
                equipe_analisada_id,
                tipo_gol,
                tempo,
                caracteristica,
                x_loc,
                y_loc,
                autor_gol_id,
                assistente_id,
                jogadores_em_quadra
            )
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def deletar_gol(self, gol_id):
        self.cursor.execute("DELETE FROM gols WHERE id = %s", (gol_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False
    
    def fechar_conexao(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    


@st.cache_resource
def get_db_manager():
    return DBManager()   
