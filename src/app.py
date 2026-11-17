
import streamlit as st
import requests
import os
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# CONFIGURAÇÕES
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODELO = "openai/gpt-4o-mini"

# CARREGAR DADOS
perfil = json.load(open('./data/perfil_investidor.json', encoding='utf-8'))
transacoes = pd.read_csv('./data/transacoes.csv')
historico = pd.read_csv('./data/historico_atendimento.csv')
produtos = json.load(open('./data/produtos_financeiros.json', encoding='utf-8'))

# CONTEXTO

contexto = f"""
CLIENTE: {perfil['nome']}, {perfil['idade']} anos, perfil {perfil['perfil_investidor']}
OBJETIVO: {perfil['objetivo_principal']}
PATRIMONIO: R$ {perfil['patrimonio_total']} | RESERVA: R$ {perfil['reserva_emergencia_atual']}

TRANSAÇÕES RECENTES:
{transacoes.to_string(index=False)}

ATENDIMENTO ANTERIORES:
{historico.to_string(index=False)}

PRODUTOS DISPONIVEIS:
{json.dumps(produtos, indent=2, ensure_ascii=False)}
"""

# SYSTEM PROMPT
SYSTEM_PROMPT = """
Você é a Elisa, uma educadora financeira amigável e didática.

OBJETIVO:
Ensinar conceitos de finanças pessoais de forma simples, usando os dados do cliente como exemplos práticos.

REGRAS:
- Nunca recomende investimentos específicos apenas explique como funcionam;
- JAMAIS responda a perguntas fora do tema ensino de finanças pessoais.
  Quando ocorrer, responda lembrando o seu papel de educadora financeira;
- Use os dados fornecidos para dar exemplos personalizados;
- Linguagem simples, como se estivesse explicando para um amigo;
- Se não souber algo, admita: 'Não tenho essa informação, mas posso explicar...';
- Sempre pergunte se o cliente entendeu
- Responda de forma sucinta e direta, com no maximo 3 parágrafos;
- NUNCA recomendar começar a investir
"""

# FUNÇÃO DA IA
def perguntar(mensagens):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    mensagens_api = [
        {
            "role": "system",
            "content": f"""
            {SYSTEM_PROMPT}

            CONTEXTO DO CLIENTE:
            {contexto}
            """
        }
    ] + mensagens

    payload = {
        "model": MODELO,
        "messages": mensagens_api,
        "stream": False,
        "temperature": 0.7
    }

    resposta = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=60
    )

    resposta.raise_for_status()

    return resposta.json()["choices"][0]["message"]["content"]


# INTERFACE STREAMLIT
st.set_page_config(
    page_title="Elisa - Assistente Financeira",
    page_icon="💰"
)

st.title("💰 Elisa - Assistente Financeira")
st.write("Olá! Sou a Elisa. Vamos conversar sobre suas finanças?")

# HISTÓRICO DA CONVERSA
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

# EXIBIR MENSAGENS
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

# CAMPO DE PERGUNTA
if pergunta := st.chat_input("Digite sua pergunta..."):

    st.session_state.mensagens.append({
        "role": "user",
        "content": pergunta
    })

    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Elisa está pensando..."):
            try:
                resposta = perguntar(st.session_state.mensagens)

                st.markdown(resposta)

                st.session_state.mensagens.append({
                    "role": "assistant",
                    "content": resposta
                })

            except requests.RequestException as erro:
                st.error(f"Erro ao acessar a API: {erro}")
