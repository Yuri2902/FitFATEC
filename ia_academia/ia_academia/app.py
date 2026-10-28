# Interface alternativa com Streamlit (use servidor.py + index.html para a versão HTML/CSS)
import streamlit as st
from assistente import responder, risco_de_desistir

st.set_page_config(page_title="Assistente da Academia", page_icon="🏋️")
st.title("🏋️ Assistente da Academia")

st.sidebar.header("Dados do aluno")
aluno = {
    "idade": st.sidebar.number_input("Idade", 14, 90, 25),
    "objetivo": st.sidebar.selectbox(
        "Objetivo",
        ["ganhar massa muscular", "emagrecer", "condicionamento", "saúde geral"],
    ),
    "nivel": st.sidebar.selectbox("Nível", ["iniciante", "intermediário", "avançado"]),
    "frequencia_semanal": st.sidebar.slider("Treinos por semana", 0, 7, 3),
    "meses_matricula": st.sidebar.number_input("Meses de matrícula", 0, 120, 3),
    "faltas_ultimo_mes": st.sidebar.number_input("Faltas no último mês", 0, 30, 4),
}

st.sidebar.metric("Risco de desistência", f"{risco_de_desistir(aluno):.0%}")

if "historico" not in st.session_state:
    st.session_state.historico = []

for msg in st.session_state.historico:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

pergunta = st.chat_input("Como posso ajudar no seu treino?")
if pergunta:
    st.session_state.historico.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.write(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resposta = responder(aluno, st.session_state.historico)
        st.write(resposta)
    st.session_state.historico.append({"role": "assistant", "content": resposta})
