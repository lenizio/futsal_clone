import psycopg2
from psycopg2 import sql
import streamlit as st

class DBManager:
    """
    Gerencia a conexão e as operações com o banco de dados PostgreSQL.
    """
    
    def __init__(self):
        """
        Inicializa a conexão com o banco de dados PostgreSQL usando as
        variáveis de ambiente do Streamlit.

        Raises:
            psycopg2.OperationalError: Se a conexão com o banco de dados falhar.
        """
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
        """
        Cria as tabelas `equipes_1`, `jogadores_1`, `jogos_1`, `jogadas_1` e `gols_1`
        se elas ainda não existirem.
        Caso ocorra algum erro, a transação será revertida.
        """
        comandos = [
            """
            CREATE TABLE IF NOT EXISTS equipes_1 (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                categoria VARCHAR(50) NOT NULL,
                logo_id VARCHAR(255) DEFAULT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogadores_1 (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                numero_camisa INT NOT NULL,
                equipe_id INT NOT NULL REFERENCES equipes_1(id) ON DELETE CASCADE,
                equipe VARCHAR(100) NOT NULL,
                posicao VARCHAR(50) NOT NULL,
                image_id VARCHAR(255) DEFAULT NULL,
                CONSTRAINT unique_numero_camisa_por_equipe_1 UNIQUE (equipe_id, numero_camisa)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogos_1 (
                id SERIAL PRIMARY KEY,
                equipe_mandante_id INT NOT NULL REFERENCES equipes_1(id) ON DELETE CASCADE,
                equipe_mandante_nome VARCHAR(100) NOT NULL,
                equipe_visitante_id INT NOT NULL REFERENCES equipes_1(id) ON DELETE CASCADE,
                equipe_visitante_nome VARCHAR(100) NOT NULL,
                data DATE NOT NULL,
                fase VARCHAR(50),
                rodada VARCHAR(50),
                competicao VARCHAR(100),
                inicio_partida TIME
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jogadas_1 (
                id SERIAL PRIMARY KEY,
                jogador_id BIGINT NOT NULL REFERENCES jogadores_1(id) ON DELETE CASCADE,
                jogador_nome VARCHAR(100) NOT NULL,
                jogo_id INT NOT NULL REFERENCES jogos_1(id) ON DELETE CASCADE,
                jogada VARCHAR(255) NOT NULL,
                tempo VARCHAR(10) NOT NULL,
                x_loc FLOAT NOT NULL,
                y_loc FLOAT NOT NULL,
                hora_jogada TIME NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS gols_1 (
                id SERIAL PRIMARY KEY,
                -- Informações do Jogo
                jogo_id INT NOT NULL REFERENCES jogos_1(id) ON DELETE CASCADE,
                
                -- Contexto do Gol
                equipe_analisada_id INT NOT NULL REFERENCES equipes_1(id) ON DELETE CASCADE,
                tipo_gol VARCHAR(7) NOT NULL,
                tempo VARCHAR(10) NOT NULL,
                caracteristica VARCHAR(255) NOT NULL,
                x_loc FLOAT NOT NULL,
                y_loc FLOAT NOT NULL,
                
                -- Detalhes específicos para gols da própria equipe
                autor_gol_id INT REFERENCES jogadores_1(id) ON DELETE SET NULL,
                assistente_id INT REFERENCES jogadores_1(id) ON DELETE SET NULL,
                jogadores_em_quadra INT[] NOT NULL DEFAULT ARRAY[]::INT[]
            )
            """
        ]

        try:
            for comando in comandos:
                self.cursor.execute(comando)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()

        
    def rollback(self):
        """
        Desfaz a última transação do banco de dados.
        """
        self.conn.rollback()

    def verificar_equipe_existente(self, nome, categoria):
        """
        Verifica se uma equipe com o nome e categoria fornecidos já existe no banco de dados.

        Args:
            nome (str): O nome da equipe.
            categoria (str): A categoria da equipe.

        Returns:
            tuple or None: Uma tupla com o ID da equipe se ela for encontrada, caso contrário, retorna None.
        """
        nome=nome.strip()
        
        self.cursor.execute(
            """
            SELECT id FROM equipes_1
            WHERE nome = %s AND categoria = %s
            """,
            (nome, categoria)
        )
        return self.cursor.fetchone()  # Retorna None se não encontrar
    
    def verificar_jogador_por_nome(self, nome, equipe_id, jogador_id=None):
        """
        Verifica se já existe um jogador com o mesmo nome em uma equipe, excluindo opcionalmente
        o próprio jogador que está sendo editado.

        Args:
            nome (str): O nome do jogador a ser verificado.
            equipe_id (int): O ID da equipe.
            jogador_id (int, optional): O ID do jogador a ser excluído da verificação (para edições). Defaults to None.

        Returns:
            str or None: Uma string de erro se um jogador com o mesmo nome for encontrado, caso contrário, None.
        """
        self.cursor.execute(
            """
            SELECT 1 FROM jogadores_1 WHERE nome = %s AND equipe_id = %s AND id != %s
            """,
            (nome, equipe_id, jogador_id)
        )
        resultado = self.cursor.fetchone()
        if resultado:
            return "Jogador já cadastrado com este nome."

    def verificar_jogador_por_numero_camisa(self, numero_camisa, equipe_id, jogador_id=None):
        """
        Verifica se já existe um jogador com o mesmo número de camisa em uma equipe, 
        excluindo opcionalmente o próprio jogador que está sendo editado.

        Args:
            numero_camisa (int): O número da camisa do jogador.
            equipe_id (int): O ID da equipe.
            jogador_id (int, optional): O ID do jogador a ser excluído da verificação (para edições). Defaults to None.

        Returns:
            str or None: Uma string de erro se um jogador com o mesmo número de camisa for encontrado, caso contrário, None.
        """
        self.cursor.execute(
            """
            SELECT 1 FROM jogadores_1 WHERE numero_camisa = %s AND equipe_id = %s AND id != %s
            """,
            (numero_camisa, equipe_id, jogador_id)
        )
        resultado = self.cursor.fetchone()
        if resultado:
            return "Já existe um jogador com este número de camisa no equipe."

    
    def adicionar_equipe(self, nome, categoria, logo_id):
        """
        Adiciona uma nova equipe ao banco de dados.

        Args:
            nome (str): O nome da equipe.
            categoria (str): A categoria da equipe.
            logo_id (str): O ID da imagem do logo da equipe.

        Returns:
            int or None: O ID da nova equipe se a inserção for bem-sucedida, caso contrário, None 
                         se a equipe já existir.
        """
        # Verificar se o equipe já existe
        if self.verificar_equipe_existente(nome, categoria):
            return None

        # Inserir o novo equipe
        self.cursor.execute(
            """
            INSERT INTO equipes_1 (nome, categoria, logo_id)
            VALUES (%s, %s,%s)
            RETURNING id
            """,
            (nome, categoria, logo_id)
        )
        self.conn.commit()
        novo_id = self.cursor.fetchone()[0]
        return novo_id


    def adicionar_jogador(self, nome, equipe_id, equipe_nome, posicao, numero_camisa, image_id=None):
        """
        Adiciona um novo jogador ao banco de dados, verificando se o nome e o número da camisa 
        já existem na mesma equipe.

        Args:
            nome (str): O nome do jogador.
            equipe_id (int): O ID da equipe.
            equipe_nome (str): O nome da equipe.
            posicao (str): A posição do jogador.
            numero_camisa (int): O número da camisa do jogador.
            image_id (str, optional): O ID da imagem do jogador. Defaults to None.

        Returns:
            int or str: O ID do novo jogador se a inserção for bem-sucedida, ou uma string 
                        com a mensagem de erro se o jogador já existir.
        """
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
            INSERT INTO jogadores_1 (nome, equipe_id, equipe, posicao, numero_camisa, image_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (nome, equipe_id, equipe_nome, posicao, numero_camisa, image_id)
        )
        self.conn.commit()
        novo_id = self.cursor.lastrowid
        return novo_id
    
    def editar_jogador(self, equipe_id, jogador_id, nome=None, numero_camisa=None, posicao=None, image_id=None):
        """
        Edita os dados de um jogador existente.

        Args:
            equipe_id (int): O ID da equipe do jogador.
            jogador_id (int): O ID do jogador a ser editado.
            nome (str, optional): O novo nome do jogador. Defaults to None.
            numero_camisa (int, optional): O novo número da camisa. Defaults to None.
            posicao (str, optional): A nova posição. Defaults to None.
            image_id (str, optional): O novo ID da imagem. Defaults to None.
            
        Returns:
            str or None: Uma string de erro se o nome ou número da camisa já existir em outro jogador 
                         da equipe, caso contrário, retorna None.
        """
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
        
        erro_nome = self.verificar_jogador_por_nome(nome, equipe_id, jogador_id)
        if erro_nome:
            return erro_nome
        
        erro_numero_camisa = self.verificar_jogador_por_numero_camisa(numero_camisa, equipe_id, jogador_id)
        if erro_numero_camisa:
            return erro_numero_camisa    

        valores.append(jogador_id)

        comando = f"UPDATE jogadores_1 SET {', '.join(campos)} WHERE id = %s"
        self.cursor.execute(comando, tuple(valores))
        self.conn.commit()


    def adicionar_jogo(self, equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, fase, rodada, competicao):
        """
        Adiciona um novo jogo ao banco de dados.

        Args:
            equipe_mandante_id (int): O ID da equipe mandante.
            equipe_mandante_nome (str): O nome da equipe mandante.
            equipe_visitante_id (int): O ID da equipe visitante.
            equipe_visitante_nome (str): O nome da equipe visitante.
            data (date): A data do jogo.
            fase (str): A fase da competição.
            rodada (str): A rodada da competição.
            competicao (str): O nome da competição.

        Returns:
            int: O ID do novo jogo.
        """
        self.cursor.execute(
            """
            INSERT INTO jogos_1 (equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, fase, rodada, competicao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, fase, rodada, competicao)
        )
        self.conn.commit()
        return self.cursor.fetchone()[0]

    def adicionar_jogada(self, jogador_id, jogador_nome, jogo_id, jogada, tempo, x_loc, y_loc):
        """
        Adiciona uma nova jogada ao banco de dados.

        Args:
            jogador_id (int): O ID do jogador que fez a jogada.
            jogador_nome (str): O nome do jogador.
            jogo_id (int): O ID do jogo em que a jogada ocorreu.
            jogada (str): O tipo de jogada (ex: "gol", "passe").
            tempo (str): O tempo em que a jogada ocorreu durante o jogo.
            x_loc (float): A coordenada X da localização da jogada.
            y_loc (float): A coordenada Y da localização da jogada.

        Returns:
            int: O ID da jogada recém-adicionada.
        """
        self.cursor.execute(
            """
            INSERT INTO jogadas_1 (jogador_id, jogador_nome, jogo_id, jogada, tempo, x_loc, y_loc, hora_jogada)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIME)
            """,
            (jogador_id, jogador_nome, jogo_id, jogada, tempo, x_loc, y_loc)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def listar_equipes(self):
        """
        Lista todas as equipes cadastradas no banco de dados.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (id, nome, categoria)
        """
        self.cursor.execute("SELECT id, nome, categoria FROM equipes_1")
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    def listar_dados_equipe(self, id):
        """
        Lista os dados de uma equipe específica.

        Args:
            id (int): O ID da equipe.

        Returns:
            tuple or None: Uma tupla com os dados da equipe se encontrada, caso contrário, None. A tupla contém:
                           (nome, categoria, logo_id)
        """
        self.cursor.execute("""
            SELECT nome, categoria, logo_id
            FROM equipes_1
            WHERE id = %s""", (id,))
        return self.cursor.fetchone()
    
    def atualizar_equipe(self, id, nome=None, categoria=None, logo=None):
        """
        Atualiza os dados de uma equipe existente.

        Args:
            id (int): O ID da equipe a ser atualizada.
            nome (str, optional): O novo nome da equipe. Defaults to None.
            categoria (str, optional): A nova categoria da equipe. Defaults to None.
            logo (str, optional): O novo ID do logo da equipe. Defaults to None.
        
        Raises:
            ValueError: Se nenhum campo para atualizar for fornecido.
        """
        campos = []
        valores = []

        if nome is not None:
            campos.append("nome = %s")
            valores.append(nome)
        
        if categoria is not None:
            campos.append("categoria = %s")
            valores.append(categoria)
        
        if logo is not None:
            campos.append("logo_id = %s")
            valores.append(logo)

        if not campos:
            raise ValueError("Nenhum campo para atualizar foi fornecido.")

        # Adiciona o ID ao final dos valores
        valores.append(id)

        sql = f"""
            UPDATE equipes_1
            SET {', '.join(campos)}
            WHERE id = %s
        """

        self.cursor.execute(sql, tuple(valores))
        self.conn.commit()
    
    def listar_jogadores(self):
        """
        Lista todos os jogadores cadastrados no banco de dados.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (id, nome, equipe, posicao)
        """
        self.cursor.execute("SELECT id, nome, equipe, posicao FROM jogadores_1")
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    def listar_jogos(self):
        """
        Lista todos os jogos cadastrados no banco de dados, ordenados por data decrescente.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (id, equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, competicao, fase, rodada)
        """
        self.cursor.execute("SELECT id, equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, competicao, fase, rodada FROM jogos_1 ORDER BY data DESC")
        return self.cursor.fetchall()
    
    def listar_jogadas(self):
        """
        Lista todas as jogadas cadastradas no banco de dados.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (id, jogador_id, jogador_nome, jogo_id, jogada, tempo, x_loc, y_loc)
        """
        self.cursor.execute("SELECT * FROM jogadas_1")
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    def listar_jogadas_por_partida_com_tempo(self, jogo_id):
        """
        Recupera uma lista de todas as jogadas para uma partida específica,
        incluindo detalhes do jogo e do jogador.

        Args:
            jogo_id (int): O ID da partida.

        Returns:
            list of tuples: Uma lista de jogadas com os seguintes detalhes:
                - equipe_mandante_nome (str)
                - equipe_visitante_nome (str)
                - fase (str)
                - rodada (int)
                - competicao (str)
                - jogador_nome (str)
                - jogada (str)
                - tempo (str): tempo da jogada (ex: '1ºT', '2ºT', etc.)
                - x_loc (float)
                - y_loc (float)
                - tempo_relativo_jogada (timedelta): diferença entre o horário da jogada e o início da partida
        """
        self.cursor.execute("""
            SELECT
                jogos_1.equipe_mandante_nome,
                jogos_1.equipe_visitante_nome,
                jogos_1.fase,
                jogos_1.rodada,
                jogos_1.competicao,
                jogadas_1.jogador_nome, 
                jogadas_1.jogada,
                jogadas_1.tempo,
                jogadas_1.x_loc,
                jogadas_1.y_loc,
                jogadas_1.hora_jogada,
                EXTRACT(EPOCH from jogadas_1.hora_jogada - jogos_1.inicio_partida) as tempo_relativo_jogada
            FROM
                jogos_1
            INNER JOIN
                jogadas_1
            ON
                jogos_1.id = jogadas_1.jogo_id
            WHERE
                jogos_1.id = %s
            ORDER BY
                jogadas_1.id ASC
        """, (jogo_id,))
        return self.cursor.fetchall()
    
    
    def listar_jogadores_por_equipe(self, equipe_id):
        """
        Lista todos os jogadores de uma equipe específica.

        Args:
            equipe_id (int): O ID da equipe.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (id, nome, posicao, numero_camisa, image_id)
        """
        self.cursor.execute("SELECT id, nome, posicao, numero_camisa, image_id FROM jogadores_1 WHERE equipe_id = %s", (equipe_id,))
        return self.cursor.fetchall()  # Retorna uma lista de tuplas
    
    def listar_nome_id_jogadores_por_equipe(self, equipe_id):
        """
        Lista o ID e o nome de todos os jogadores de uma equipe específica.

        Args:
            equipe_id (int): O ID da equipe.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (id, nome)
        """
        self.cursor.execute("SELECT id, nome FROM jogadores_1 WHERE equipe_id = %s", (equipe_id,))
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    def listar_jogos_por_equipe_e_competicao(self, equipe_id, competicao):
        """
        Lista todos os jogos de uma equipe em uma competição específica.

        Args:
            equipe_id (int): O ID da equipe.
            competicao (str): O nome da competição.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém os dados do jogo.
        """
        self.cursor.execute(
            """
            SELECT * FROM jogos_1
            WHERE (equipe_mandante_id = %s OR equipe_visitante_id = %s) AND competicao = %s
            """,
            (equipe_id, equipe_id, competicao)
        )
        return self.cursor.fetchall()  # Retorna uma lista de tuplas

    def listar_detalhes_jogo(self, jogo_id):
        """
        Lista os detalhes de um jogo específico.

        Args:
            jogo_id (int): O ID do jogo.

        Returns:
            tuple or None: Uma tupla com os detalhes do jogo se encontrado, caso contrário, None. A tupla contém:
                           (equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, fase, rodada, competicao)
        """
        self.cursor.execute("SELECT equipe_mandante_id, equipe_mandante_nome, equipe_visitante_id, equipe_visitante_nome, data, fase, rodada, competicao FROM jogos_1 WHERE id = %s", (jogo_id,))
        return self.cursor.fetchone()
    
    def listar_jogadas_por_jogo(self, jogo_id):
        """
        Lista todas as jogadas de um jogo específico, com detalhes do jogo.

        Args:
            jogo_id (int): O ID do jogo.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (equipe_mandante_nome, equipe_visitante_nome, fase_jogo, rodada_jogo, competicao_jogo, 
                           nome_jogador, tipo_jogada, tempo_jogada, x_loc_jogada, y_loc_jogada)
        """
        self.cursor.execute("""
            SELECT
                jogos_1.equipe_mandante_nome,
                jogos_1.equipe_visitante_nome,
                jogos_1.fase,
                jogos_1.rodada,
                jogos_1.competicao,
                jogadas_1.jogador_nome, 
                jogadas_1.jogada,
                jogadas_1.tempo,
                jogadas_1.x_loc,
                jogadas_1.y_loc
            FROM
                jogos_1
            INNER JOIN
                jogadas_1
            ON
                jogos_1.id = jogadas_1.jogo_id
            WHERE
                jogos_1.id = %s""", 
                (jogo_id,))
        return self.cursor.fetchall() 
    
    
    def listar_dados_analise_individual(self):
        """
        Retorna uma lista completa de dados para análise individual, unindo informações de jogos, jogadas e jogadores.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (id_jogo, equipe_mandante_nome, equipe_visitante_nome, fase_jogo, rodada_jogo, 
                           competicao_jogo, equipe_id_jogador, equipe_nome_jogador, nome_jogador, 
                           tipo_jogada, tempo_jogada, x_loc_jogada, y_loc_jogada)
        """
        self.cursor.execute("""
            SELECT
                jogos_1.id,
                jogos_1.equipe_mandante_nome,
                jogos_1.equipe_visitante_nome,
                jogos_1.fase,
                jogos_1.rodada,
                jogos_1.competicao,
                jogadores_1.equipe_id,
                jogadores_1.equipe,
                jogadas_1.jogador_nome, 
                jogadas_1.jogada,
                jogadas_1.tempo,
                jogadas_1.x_loc,
                jogadas_1.y_loc
            FROM
                jogos_1
            LEFT JOIN
                jogadas_1
            ON
                jogos_1.id = jogadas_1.jogo_id
            INNER JOIN 
                jogadores_1 
            ON
                jogadas_1.jogador_id = jogadores_1.id
            """)
        return self.cursor.fetchall()
    
    
    def deletar_equipe(self, equipe_id):
        """
        Deleta uma equipe do banco de dados.

        Args:
            equipe_id (int): O ID da equipe a ser deletada.

        Returns:
            bool: True se a equipe foi deletada com sucesso, False caso contrário.
        """
        self.cursor.execute("DELETE FROM equipes_1 WHERE id = %s", (equipe_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def deletar_jogador(self, jogador_id):
        """
        Deleta um jogador do banco de dados.

        Args:
            jogador_id (int): O ID do jogador a ser deletado.

        Returns:
            bool: True se o jogador foi deletado com sucesso, False caso contrário.
        """
        self.cursor.execute("DELETE FROM jogadores_1 WHERE id = %s", (jogador_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def deletar_jogo(self, jogo_id):
        """
        Deleta um jogo do banco de dados.

        Args:
            jogo_id (int): O ID do jogo a ser deletado.

        Returns:
            bool: True se o jogo foi deletado com sucesso, False caso contrário.
        """
        self.cursor.execute("DELETE FROM jogos_1 WHERE id = %s", (jogo_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def deletar_jogada(self, jogada_id):
        """
        Deleta uma jogada do banco de dados.

        Args:
            jogada_id (int): O ID da jogada a ser deletada.

        Returns:
            bool: True se a jogada foi deletada com sucesso, False caso contrário.
        """
        self.cursor.execute("DELETE FROM jogadas_1 WHERE id = %s", (jogada_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False

    def listar_gols(self):
        """
        Lista todos os gols com informações detalhadas de jogos, equipes, jogadores e assistentes.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (id_gol, jogo_id, equipe_mandante_nome, equipe_visitante_nome, competicao, fase, 
                           rodada, data, equipe_analisada, tipo_gol, caracteristica, tempo, nome_autor_gol, 
                           nome_assistente, nomes_jogadores_em_quadra, x_loc, y_loc)
        """
        self.cursor.execute("""
            SELECT
                g.id,
                jogos_1.id as jogo_id, 
                jogos_1.equipe_mandante_nome,
                jogos_1.equipe_visitante_nome,
                jogos_1.competicao ,
                jogos_1.fase,
                jogos_1.rodada,
                jogos_1.data,
                e.nome as equipe_analisada,
                g.tipo_gol,
                g.caracteristica,
                g.tempo,
                j.nome AS gol_nome,
                a.nome as assistente_nome,
                agg.jogadores_em_quadra_nomes,
                g.x_loc,
                g.y_loc
            FROM gols_1 g
            LEFT JOIN jogos_1 ON jogos_1.id = g.jogo_id
            LEFT JOIN equipes_1 e ON e.id = g.equipe_analisada_id
            LEFT JOIN jogadores_1 j ON j.id = g.autor_gol_id
            LEFT JOIN jogadores_1 a ON a.id = g.assistente_id
            LEFT JOIN (
                SELECT 
                    g2.id AS gol_id,
                    array_agg(j2.nome) AS jogadores_em_quadra_nomes
                FROM gols_1 g2
                LEFT JOIN jogadores_1 j2 ON j2.id = ANY(g2.jogadores_em_quadra)
                GROUP BY g2.id
            ) agg ON agg.gol_id = g.id""")
        
        return self.cursor.fetchall()
    
    def listar_gols_por_equipe(self, equipe_id):
        """
        Lista todos os gols de uma equipe específica, com informações detalhadas.

        Args:
            equipe_id (int): O ID da equipe.

        Returns:
            list of tuple: Uma lista de tuplas, onde cada tupla contém:
                           (equipe_mandante_nome, equipe_visitante_nome, competicao, fase, rodada, 
                           equipe_analisada, tipo_gol, caracteristica, tempo, nome_autor_gol, 
                           nome_assistente, nomes_jogadores_em_quadra, x_loc, y_loc)
        """
        self.cursor.execute("""
            SELECT 
                jogos_1.equipe_mandante_nome,
                jogos_1.equipe_visitante_nome,
                jogos_1.competicao ,
                jogos_1.fase,
                jogos_1.rodada,
                e.nome as equipe_analisada,
                g.tipo_gol,
                g.caracteristica,
                g.tempo,
                j.nome AS gol_nome,
                a.nome as assistente_nome,
                agg.jogadores_em_quadra_nomes,
                g.x_loc,
                g.y_loc
            FROM gols_1 g
            LEFT JOIN jogos_1 ON jogos_1.id = g.jogo_id
            LEFT JOIN equipes_1 e ON e.id = g.equipe_analisada_id
            LEFT JOIN jogadores_1 j ON j.id = g.autor_gol_id
            LEFT JOIN jogadores_1 a ON a.id = g.assistente_id
            LEFT JOIN (
                SELECT 
                    g2.id AS gol_id,
                    array_agg(j2.nome) AS jogadores_em_quadra_nomes
                FROM gols_1 g2
                LEFT JOIN jogadores_1 j2 ON j2.id = ANY(g2.jogadores_em_quadra)
                GROUP BY g2.id
            ) agg ON agg.gol_id = g.id
            WHERE
                g.equipe_analisada_id = %s""" ,
                (equipe_id,))
        
        return self.cursor.fetchall()
    
    def adicionar_gol(self, jogo_id, equipe_analisada_id, tipo_gol, tempo, caracteristica, x_loc, y_loc, jogadores_em_quadra=None, autor_gol_id=None, assistente_id=None):
        """
        Adiciona um novo gol ao banco de dados.

        Args:
            jogo_id (int): O ID do jogo em que o gol ocorreu.
            equipe_analisada_id (int): O ID da equipe que está sendo analisada no gol.
            tipo_gol (str): O tipo de gol ('Feito' ou 'Sofrido').
            tempo (str): O tempo em que o gol ocorreu.
            caracteristica (str): A característica do gol (ex: "Chute de fora da área").
            x_loc (float): A coordenada X do gol.
            y_loc (float): A coordenada Y do gol.
            jogadores_em_quadra (list of int, optional): Uma lista de IDs dos jogadores em quadra no momento do gol. Defaults to None.
            autor_gol_id (int, optional): O ID do jogador que fez o gol. Defaults to None.
            assistente_id (int, optional): O ID do jogador que deu a assistência. Defaults to None.

        Returns:
            int: O ID do novo gol.
        """
        # Define a lista de jogadores em quadra como vazia se não for fornecida
        if jogadores_em_quadra is None:
            jogadores_em_quadra = []
        
        self.cursor.execute(
            """
            INSERT INTO gols_1 (
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
        """
        Deleta um gol do banco de dados.

        Args:
            gol_id (int): O ID do gol a ser deletado.

        Returns:
            bool: True se o gol foi deletado com sucesso, False caso contrário.
        """
        self.cursor.execute("DELETE FROM gols_1 WHERE id = %s", (gol_id,))
        self.conn.commit()
        
        if self.cursor.rowcount > 0:
            return True
        else:
            return False
    
    def fechar_conexao(self):
        """
        Fecha o cursor e a conexão com o banco de dados.
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


@st.cache_resource
def get_db_manager():
    """
    Retorna uma instância de `DBManager` usando o cache do Streamlit.
    Isso garante que apenas uma única conexão com o banco de dados seja 
    criada e reutilizada em toda a execução do aplicativo.

    Returns:
        DBManager: Uma instância de DBManager.
    """
    return DBManager()
