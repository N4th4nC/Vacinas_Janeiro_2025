import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# ---------------------------
# Config da Página
# ---------------------------
st.set_page_config(
    page_title="Painel Vacinação no Brasil",
    page_icon="💉",
    layout="wide",
    initial_sidebar_state="expanded"
)
alt.themes.enable("dark")
# ---------------------------
# Dados
# ---------------------------
df_mapa = pd.read_csv("mapaEstados.csv")
df_idade = pd.read_csv("idade.csv")
df_raca = pd.read_csv("racaCor.csv")
df_estabelecimento = pd.read_csv("tipoEstabelecimento.csv")
df_vacinas = pd.read_csv("tipoVacinas.csv")

with open("br_states.json", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# ---------------------------
# Sidebar - Filtros
# ---------------------------
st.sidebar.title("Filtros")
estados = ["Todos"] + sorted(df_mapa["nomeUF"].unique().tolist())
estado_selecionado = st.sidebar.selectbox("Selecione o estado", estados)

# ---------------------------
# Título
# ---------------------------
st.title("💉Painel de Vacinação no Brasil")

# ---------------------------
# Linha 1: Mapa + Donuts
# ---------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Mapa - Total de Aplicações por Estado")
    df_mapa_filtro = df_mapa.copy() if estado_selecionado == "Todos" else df_mapa[df_mapa["nomeUF"] == estado_selecionado]

    fig_map = px.choropleth(
        df_mapa_filtro,
        geojson=geojson_data,
        locations="nomeUF",
        featureidkey="properties.SIGLA",
        color="total_aplicacoes",
        color_continuous_scale="Rainbow",
        scope="south america"
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(margin=dict(t=0, b=0), template="plotly_dark")
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    st.subheader("Aplicações por Localidade")

    resumo = (
        df_mapa.agg({
            "aplicacoes_mesma_localidade": "sum",
            "aplicacoes_localidade_diferente": "sum",
            "total_aplicacoes": "sum"
        }).to_frame().T if estado_selecionado == "Todos"
        else df_mapa[df_mapa["nomeUF"] == estado_selecionado]
    )

    mesma = int(resumo["aplicacoes_mesma_localidade"].iloc[0])
    diferente = int(resumo["aplicacoes_localidade_diferente"].iloc[0])
    total = int(resumo["total_aplicacoes"].iloc[0])

    perc_mesma = round((mesma / total) * 100, 1)
    perc_dif = round((diferente / total) * 100, 1)

    fig = make_subplots(rows=2, cols=1, specs=[[{"type": "domain"}], [{"type": "domain"}]], vertical_spacing=0.2)

    fig.add_trace(go.Pie(
        values=[mesma, total - mesma],
        labels=["Mesma Localidade", "Outras"],
        hole=0.6,
        marker_colors=["#2ca02c", "#393939"],
        textinfo="none",
        showlegend=False
    ), row=1, col=1)

    fig.add_trace(go.Pie(
        values=[diferente, total - diferente],
        labels=["Localidade Diferente", "Outras"],
        hole=0.6,
        marker_colors=["#d62728", "#393939"],
        textinfo="none",
        showlegend=False
    ), row=2, col=1)

    fig.update_layout(
        annotations=[
            dict(text=f"<b>{perc_mesma}%</b><br><span style='font-size:12px'>Mesma</span>",
                 x=0.5, y=0.85, showarrow=False, font=dict(color="#2ca02c", size=18), align="center"),
            dict(text=f"<b>{perc_dif}%</b><br><span style='font-size:12px'>Diferente</span>",
                 x=0.5, y=0.15, showarrow=False, font=dict(color="#d62728", size=18), align="center"),
        ],
        height=450,
        margin=dict(t=20, b=20),
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Linha 2: Idade + Cor/Raça
# ---------------------------
col3, col4 = st.columns(2)

with col3:
    st.subheader("Vacinação por Idade")

    df_idade_filtro = (
        df_idade.groupby(['idadePaciente', 'sexoPaciente'], as_index=False).agg({'total_aplicacoes': 'sum'})
        if estado_selecionado == "Todos"
        else df_idade[df_idade["nomeUF"] == estado_selecionado]
    )
    df_idade_filtro['idadePaciente'] = pd.to_numeric(df_idade_filtro['idadePaciente'], errors='coerce')
    df_idade_filtro = df_idade_filtro.sort_values(by='idadePaciente')

    fig_idade = px.line(
        df_idade_filtro,
        x='idadePaciente',
        y='total_aplicacoes',
        color='sexoPaciente',
        color_discrete_sequence=px.colors.qualitative.Dark2,
        labels={'total_aplicacoes': 'Total de Vacinas', 'idadePaciente': 'Idade', 'sexoPaciente': 'Sexo'},
        template="plotly_dark"
    )
    st.plotly_chart(fig_idade, use_container_width=True)

with col4:
    st.subheader("Distribuição por Cor/Raça")

    df_raca_filtro = (
        df_raca.groupby("racaCorPaciente", as_index=False).agg({"total_aplicacoes": "sum"})
        if estado_selecionado == "Todos"
        else df_raca[df_raca["nomeUF"] == estado_selecionado]
    )

    fig_raca = px.pie(
        df_raca_filtro,
        names="racaCorPaciente",
        values="total_aplicacoes",
        color_discrete_sequence=px.colors.qualitative.Dark2,
        template="plotly_dark"
    )
    st.plotly_chart(fig_raca, use_container_width=True)

# ---------------------------
# Linha 3: Estabelecimento + Vacina
# ---------------------------
col_full = st.columns([1])[0]  # única coluna ocupando toda a largura equivalente

with col_full:

    st.subheader("Vacinas por Tipo de Estabelecimento")

    df_estab_filtro = (
        df_estabelecimento.groupby("tipoEstabelecimento", as_index=False).agg({"total_aplicacoes": "sum"})
        if estado_selecionado == "Todos"
        else df_estabelecimento[df_estabelecimento["nomeUF"] == estado_selecionado]
    )
    df_estab_filtro = df_estab_filtro.sort_values(by="total_aplicacoes", ascending=False)

    fig_estab = px.bar(
        df_estab_filtro,
        x="tipoEstabelecimento",
        y="total_aplicacoes",
        text="total_aplicacoes",
        color="tipoEstabelecimento",
        color_discrete_sequence=px.colors.sequential.Rainbow,
        template="plotly_dark"
    )
    fig_estab.update_layout(xaxis=dict(showticklabels=False, title=''))
    st.plotly_chart(fig_estab, use_container_width=True)


    st.subheader("Aplicações por Nome da Vacina")

    df_vac_filtro = (
        df_vacinas.groupby("nome_vacina", as_index=False).agg({"total_aplicacoes": "sum"})
        if estado_selecionado == "Todos"
        else df_vacinas[df_vacinas["nomeUF"] == estado_selecionado]
    )
    df_vac_filtro = df_vac_filtro.sort_values(by="total_aplicacoes", ascending=False)

    fig_vac = px.bar(
        df_vac_filtro,
        x="total_aplicacoes",
        y="nome_vacina",
        orientation='h',
        text="total_aplicacoes",
        color="nome_vacina",
        color_discrete_sequence=px.colors.sequential.Rainbow,
        template="plotly_dark"
    )
    
    fig_vac.update_layout(yaxis=dict(title='', showticklabels=False))
    st.plotly_chart(fig_vac, use_container_width=True)
