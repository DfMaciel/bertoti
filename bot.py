!pip install telebot
import telebot

API_TOKEN = '7445994394:AAEUkcb7dJxDofhTZ6bbwlzP9g6IOTUJ-yY'
bot = telebot.TeleBot(API_TOKEN)

import sqlite3

# Conectar ao banco (será criado no diretório atual se não existir)
conexao = sqlite3.connect("favoritos.db")

# Criar um cursor para executar comandos SQL
cursor = conexao.cursor()

# Criar a tabela de favoritos (com dados adicionais do produto)

cursor.execute("""

CREATE TABLE IF NOT EXISTS favoritos (
    usuario_id INTEGER NOT NULL,
    titulo TEXT,
    preco TEXT,
    link TEXT
);
""")

# Salvar as alterações e fechar a conexão
conexao.commit()

def salvar_favorito_db(usuario_id, titulo, preco, link):
    """
    Salva o produto como favorito no banco de dados com os dados adicionais.
    """
    # Conectar ao banco
    conexao = sqlite3.connect("favoritos.db")
    cursor = conexao.cursor()

    # Inserir dados na tabela de favoritos
    cursor.execute("""
    INSERT INTO favoritos (usuario_id, titulo, preco, link)
    VALUES (?, ?, ?, ?)
    """, (usuario_id, titulo, preco, link))

    # Salvar as alterações e fechar a conexão
    conexao.commit()
    conexao.close()

def listar_favoritos(usuario_id):
    """
    Retorna os produtos favoritos de um usuário.
    """
    conexao = sqlite3.connect("favoritos.db")
    cursor = conexao.cursor()

    # Buscar os favoritos do usuário
    cursor.execute("""
    SELECT titulo, preco, link FROM favoritos WHERE usuario_id = ?
    """, (usuario_id,))
    favoritos = cursor.fetchall()

    conexao.close()

    if favoritos:
        # Formatar a resposta para o usuário
        resposta = "Seus produtos favoritos:\n"
        for favorito in favoritos:
            titulo, preco, link = favorito
            resposta += f"\n{titulo}\nPreço: {preco}\nLink: {link}\n"
        return resposta
    else:
        return "Você ainda não tem favoritos."

# !pip install transformers
# !pip install torch

# from transformers import AutoModelForMaskedLM, AutoTokenizer, pipeline
# import torch

# # # Carregue o modelo e o tokenizador para português (BERTimbau)
# # model_name = "neuralmind/bert-base-portuguese-cased"
# # tokenizer = AutoTokenizer.from_pretrained(model_name)
# # model = AutoModelForMaskedLM.from_pretrained(model_name)

# # Carregar os pipelines
# device = 0
# nlp_intent = pipeline("zero-shot-classification", device=device)
# nlp_ner = pipeline("ner", device=device)


!pip install aiohttp
!pip install fuzzywuzzy
import requests
import re
from fuzzywuzzy import process
from io import BytesIO
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import urllib.parse

marcas = [
    "Honda", "Toyota", "Nissan", "BMW", "Chevrolet", "Ford", "Volkswagen", "Fiat", "Hyundai",
    "Kia", "Peugeot", "Renault", "Mercedes-Benz", "Audi", "Mazda", "Jeep", "Chrysler",
    "Land Rover", "Porsche", "Lexus", "Subaru", "Mitsubishi", "Citroën", "Ferrari", "Lamborghini",
    "Aston Martin", "McLaren", "Jaguar", "Bugatti", "Bentley", "Rolls-Royce", "Volvo", "Alfa Romeo",
    "Dodge", "Cadillac", "Buick", "Chery", "Great Wall", "Tesla", "Mini", "Maserati", "Suzuki", "Saab"
]

def buscar_no_mercadolivre(termo, categoria="carros", message=None, offset=0):
    """
    Realiza a busca no Mercado Livre, com limite de 5 resultados por vez e suporte à paginação.
    """
    base_url = "https://api.mercadolibre.com/sites/MLB/search"
    categorias = {"carros": "MLB1743", "pecas": "MLB1747"}
    filtro_categoria = categorias.get(categoria)

    params = {
        "q": termo,
        "category": filtro_categoria,
        "limit": 5,  # Limita para 5 resultados por vez
        "offset": offset  # Offset para buscar resultados subsequentes
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        dados = response.json()
        resultados = dados.get("results", [])

        if not resultados:
            bot.send_message(message.chat.id, f"⚠️ Nenhum resultado encontrado para '{termo}'.")
            return

        enviar_resultados_com_botao(message.chat.id, resultados, offset, termo)

    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, f"❌ Erro ao acessar a API do Mercado Livre: {str(e)}")

import urllib.parse

def enviar_resultados_com_botao(chat_id, resultados, offset, termo):
    """
    Envia os resultados com botões para salvar como favorito e navegação de 'ver mais'.
    """
    for item in resultados:
        titulo = item.get("title", "Título não disponível")
        preco = item.get("price", "Preço não disponível")
        link = item.get("permalink", "Link não disponível")
        imagem = item.get("thumbnail_id", None)
        produto_id = item.get('id')  # Garantir que você está extraindo o ID corretamente
        print(f"ID do produto: {produto_id}")  # Imprime o ID do produto para depuração

        if imagem:
            imagem_url = f"https://http2.mlstatic.com/D_NQ_NP_2X_{imagem}-O.jpg"
            imagem_resposta = requests.get(imagem_url)
            if imagem_resposta.status_code == 200:
                img_data = BytesIO(imagem_resposta.content)
                legenda = f"{titulo}\nPreço: R$ {preco}\n{link}"

                # Criar a callback_data de forma mais simples e segura
                callback_data = f"salvar_favorito_{produto_id}"

                # Criar o teclado com o botão para salvar
                teclado = InlineKeyboardMarkup()
                botao_favorito = InlineKeyboardButton(
                    text="Salvar como Favorito",
                    callback_data=callback_data
                )
                teclado.add(botao_favorito)

                # Enviar a imagem e o texto
                bot.send_photo(
                    chat_id=chat_id,
                    photo=img_data,
                    caption=legenda,
                    reply_markup=teclado
                )

    # Criar o botão de "Ver mais resultados"
    teclado_mais = InlineKeyboardMarkup()
    botao_mais = InlineKeyboardButton(
        text="Ver mais resultados",
        callback_data=f"{offset + 5}_{termo}"  # Garantir que a estrutura seja simples
    )
    teclado_mais.add(botao_mais)

    # Enviar o botão de navegação
    bot.send_message(chat_id=chat_id, text="Quer ver mais resultados?", reply_markup=teclado_mais)

def criar_callback_data(titulo, preco, link):
    """
    Cria uma string de callback segura para os botões.
    Evita caracteres especiais e separadores inválidos.
    """
    # Garantir que os dados estejam escapados e formatados de maneira simples
    titulo_escapado = urllib.parse.quote(titulo)
    preco_escapado = urllib.parse.quote(str(preco))
    link_escapado = urllib.parse.quote(link)

    # Criar uma callback_data sem caracteres especiais inválidos
    return f"salvar_favorito_{titulo_escapado}_{preco_escapado}_{link_escapado}"

@bot.callback_query_handler(func=lambda call: call.data.startswith("salvar_favorito"))
def salvar_favorito_callback(call):
    """
    Processa o clique no botão 'Salvar como Favorito' para salvar o produto.
    """
    usuario_id = call.from_user.id
    dados = call.data.split("_")

     # Verificar se o ID foi extraído corretamente
    if len(dados) >= 3:
        produto_id = dados[2]  # ID do produto
        print(f"ID do produto extraído da callback_data: {produto_id}")  # Verificação


    # Buscar informações do produto usando a API do Mercado Livre
    produto = buscar_produto_por_id(produto_id)
    print(produto)

    # Agora você pode salvar o produto ou enviar mais informações para o usuário
    if produto:
        titulo = produto["title"]
        preco = produto["price"]
        link = produto["permalink"]
        print(f"Título do produto: {titulo}")  # Verificação
        print(f"Preço do produto: {preco}")  # Verificação
        print(f"Link do produto: {link}")  # Verificação

        # Salvar o produto nos favoritos do usuário
        salvar_favorito_db(usuario_id, titulo, preco, link)

        # Confirmação para o usuário
        bot.answer_callback_query(call.id, "Produto salvo como favorito!")
        bot.send_message(call.message.chat.id, f"✅ O produto '{titulo}' foi salvo nos seus favoritos.")
    else:
        bot.answer_callback_query(call.id, "❌ Não foi possível recuperar os dados do produto.")
        bot.send_message(call.message.chat.id, "Ocorreu um erro ao tentar salvar este produto.")

@bot.callback_query_handler(func=lambda call: call.data.count("_") == 1)  # Garantir que tem apenas dois valores
def ver_mais_callback(call):
    """
    Processa o clique no botão 'Ver mais resultados' para mostrar mais resultados.
    """
    dados = call.data.split("_")
    offset = int(dados[0])  # Obtém o offset
    termo = dados[1]  # O termo da busca

    # Buscar mais resultados com base no offset
    buscar_no_mercadolivre(termo, message=call.message, offset=offset)
    bot.answer_callback_query(call.id, "Carregando mais resultados...")


def buscar_produto_por_id(produto_id):
  """
  Busca as informações detalhadas de um produto no Mercado Livre usando seu ID.
  """
  url = f"https://api.mercadolibre.com/items/{produto_id}"
  try:
      response = requests.get(url)
      response.raise_for_status()
      dados_produto = response.json()
      return dados_produto
  except requests.exceptions.RequestException as e:
      print(f"Erro ao buscar produto: {str(e)}")
      return None


palavras_irrelevantes = ["quero", "ver", "um", "carro", "veículo", "automóvel", "do", "de", "em", "com", "para", "peça", "acessório"]

# Identificação de Marca com Fuzzy Matching (ajustada para limpar o termo)
def identificar_marca_com_fuzzy(termo):
    """
    Identifica a marca de um carro usando fuzzy matching para permitir variações na escrita,
    após remover palavras irrelevantes.
    """
    # Limpar o termo removendo palavras irrelevantes
    termo_limpo = ' '.join([palavra for palavra in termo.lower().split() if palavra not in palavras_irrelevantes])
    print(f"Termo limpo: {termo_limpo}")  # Mensagem de depuração para ver o termo limpo

    # Comparar o termo limpo com as marcas usando fuzzy matching
    melhor_correspondencia = process.extractOne(termo_limpo, marcas)

    if melhor_correspondencia[1] >= 80:  # Apenas aceitar correspondências com 80% ou mais de similaridade
        print(f"Marca encontrada: {melhor_correspondencia[0]}")  # Mensagem de depuração para mostrar a marca encontrada
        return melhor_correspondencia[0]
    print(f"Nenhuma marca encontrada para o termo: {termo}")  # Mensagem de depuração se nenhuma marca for encontrada
    return None

# Ajuste para capturar apenas o modelo correto (palavra-chave após a marca ou ano)
def identificar_intencao_e_dados(mensagem):
    """
    Identifica a intenção de busca (carro ou peça) e extrai marca, modelo e tipo de peça, se houver.
    """
    # Palavras-chave para diferentes intenções
    palavras_chave_carro = ["carro", "veículo", "automóvel", "automóveis"]
    palavras_chave_peca = ["peça", "acessório", "freio", "motor", "farol", "parachoque", "volante", "pneu", "espete", "calota", "limpador"]
    palavras_irrelevantes = ["quero", "ver", "uma", "um", "para", "de", "o", "a"]

    # Identificar a intenção
    mensagem_limpa = mensagem.lower()
    if any(palavra in mensagem_limpa for palavra in palavras_chave_carro):
        intencao = "carro"
    elif any(palavra in mensagem_limpa for palavra in palavras_chave_peca):
        intencao = "peca"
    else:
        intencao = "outros"

    # Extrair a marca
    marca = identificar_marca_com_fuzzy(mensagem)

    # Remover palavras irrelevantes
    palavras = [palavra for palavra in mensagem.split() if palavra.lower() not in palavras_irrelevantes]

    # Extrair modelo e peça
    modelo = None
    peca = None

    if marca:
        # Verificar se há algo após a marca
        index_marca = next((i for i, palavra in enumerate(palavras) if palavra.lower() == marca.lower()), None)
        if index_marca is not None and index_marca + 1 < len(palavras):
            modelo = palavras[index_marca + 1]

        # Procurar peça nas palavras restantes
        peca = next((palavra for palavra in palavras if palavra in palavras_chave_peca), None)
    else:
        # Se não encontrar marca, buscar apenas peça
        peca = next((palavra for palavra in palavras if palavra in palavras_chave_peca), None)

    # Montar o termo de busca
    termo_de_busca = ""
    if peca:
        termo_de_busca += peca
    if marca:
        termo_de_busca += f" {marca}"
    if modelo:
        termo_de_busca += f" {modelo}"

    # Depuração
    print(f"Mensagem limpa: {' '.join(palavras)}")  # Mensagem de depuração
    print(f"Intenção: {intencao}, Marca: {marca}, Modelo: {modelo}, Peça: {peca}, Termo de busca: {termo_de_busca}")  # Depuração

    return intencao, marca, modelo, peca, termo_de_busca

# @bot.callback_query_handler(func=lambda call: call.data.startswith("salvar_favorito"))
# def salvar_favorito_callback(call):
#     """
#     Processa o clique no botão 'Salvar como Favorito' e salva o produto como favorito no banco.
#     """
#     dados = call.data.split("|")
#     tipo_produto = dados[1]  # Tipo do produto (carro ou peça)
#     produto_id = dados[2]    # ID do produto (agora apenas o ID é passado na callback_data)
#     usuario_id = call.from_user.id  # ID do usuário

#     # Buscar os detalhes do produto usando o ID
#     produto_detalhado = buscar_produto_por_id(produto_id)

#     if produto_detalhado:
#         titulo = produto_detalhado["title"]
#         preco = produto_detalhado["price"]
#         link = produto_detalhado["permalink"]

#         # Salvar o produto nos favoritos do usuário
#         salvar_favorito_db(usuario_id, tipo_produto, titulo, preco, link)

#         # Confirmação para o usuário
#         bot.answer_callback_query(call.id, "Produto salvo como favorito!")
#         bot.send_message(call.message.chat.id, f"✅ O produto '{titulo}' foi salvo nos seus favoritos.")
#     else:
#         bot.answer_callback_query(call.id, "❌ Não foi possível recuperar os dados do produto.")
#         bot.send_message(call.message.chat.id, "Ocorreu um erro ao tentar salvar este produto.")


@bot.message_handler(commands=['favoritos'])
def mostrar_favoritos(message):
    """
    Mostra os produtos favoritos do usuário.
    """
    usuario_id = message.from_user.id
    favoritos = listar_favoritos(usuario_id)
    bot.send_message(message.chat.id, favoritos)

# Função de manipulação das mensagens do usuário
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Lida com as mensagens do usuário e faz a busca no Mercado Livre.
    """
    texto_usuario = message.text

    # Identificar a intenção, marca e modelo
    intencao, marca, modelo, peca, termo_de_busca = identificar_intencao_e_dados(texto_usuario)

    if intencao == "carro":
        categoria = "carros"
    elif intencao == "peca":
        categoria = "pecas"
    else:
        bot.send_message(message.chat.id, "Desculpe, não entendi sua solicitação.")
        return

    # Fazer a busca no Mercado Livre
    resposta = buscar_no_mercadolivre(termo_de_busca, categoria, message)

    # Se a resposta for vazia, significa que já enviamos as imagens com as legendas
    if resposta:
        bot.send_message(message.chat.id, resposta)


# Iniciar o bot
bot.polling()
