import streamlit as st
import pandas as pd
import os
import warnings
import pydeck as pdk
import altair as alt
import plotly.express as px

# Silencia warnings de parsing misto de datas
warnings.filterwarnings("ignore", message="Parsing dates in")

# Configuração da página
st.set_page_config(page_title="BioEnergy Dashboard", layout="wide")

# =============================================
# CONSTANTES E CONFIGURAÇÕES
# =============================================

# Mapeamento de siglas para nomes mais amigáveis
TIPO_GERACAO_NOMES = {
    'UHE': 'Hidrelétrica',
    'PCH': 'Pequena Central Hidrelétrica',
    'CGH': 'Central Geradora Hidrelétrica',
    'EOL': 'Eólica',
    'UFV': 'Solar Fotovoltaica',
    'UTE': 'Termelétrica',
    'BIO': 'Biomassa',
    'GT': 'Gás',
    'NUC': 'Nuclear',
    'MOT': 'Motores',
    'QSO': 'Outros',
    'UTN': 'Outros'
}

# Descrição dos tipos de geração
TIPO_DESCRICAO = {
    'Hidrelétrica': 'Usinas que utilizam a força das águas para gerar eletricidade.',
    'Pequena Central Hidrelétrica': 'Usinas hidrelétricas de pequeno porte, com capacidade limitada.',
    'Central Geradora Hidrelétrica': 'Usinas de médio porte que geram energia a partir de recursos hídricos.',
    'Eólica': 'Usinas que captam a energia dos ventos para produzir eletricidade.',
    'Solar Fotovoltaica': 'Usinas que convertem a luz solar diretamente em energia elétrica.',
    'Termelétrica': 'Usinas que geram eletricidade a partir da queima de combustíveis fósseis ou biomassa.',
    'Biomassa': 'Usinas que utilizam matéria orgânica (resíduos agrícolas, madeira, etc.) para gerar energia.',
    'Gás': 'Usinas que utilizam gás natural para produção de eletricidade.',
    'Nuclear': 'Usinas que utilizam reações nucleares para gerar eletricidade.',
    'Motores': 'Usinas de pequeno porte que utilizam motores a combustão para gerar energia.',
    'Outros': 'Outros tipos de geração de energia elétrica.'
}

# Cores para cada tipo de geração
CORES_TIPO = {
    'Hidrelétrica': [0, 100, 255],
    'Pequena Central Hidrelétrica': [0, 180, 255],
    'Central Geradora Hidrelétrica': [100, 200, 255],
    'Eólica': [0, 200, 0],
    'Solar Fotovoltaica': [255, 200, 0],
    'Termelétrica': [255, 100, 100],
    'Biomassa': [150, 255, 100],
    'Gás': [255, 150, 0],
    'Nuclear': [150, 0, 255],
    'Motores': [255, 0, 150],
    'Outros': [180, 180, 180]
}

# =============================================
# FUNÇÕES AUXILIARES
# =============================================

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """
    Carrega os dados de um arquivo CSV, realiza a limpeza e conversão de tipos.
    """
    try:
        df = pd.read_csv(path, sep=';', encoding='latin1', dtype=str)
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {str(e)}")
        return None

    # Verificação de colunas essenciais
    colunas_necessarias = ['SigTipoGeracao', 'NumCoordNEmpreendimento', 'NumCoordEEmpreendimento']
    for col in colunas_necessarias:
        if col not in df.columns:
            st.error(f"Coluna obrigatória não encontrada: {col}")
            return None

    # Processamento de colunas numéricas
    colunas_numericas = ['MdaPotenciaOutorgadaKw', 'MdaPotenciaFiscalizadaKw', 'MdaGarantiaFisicaKw']
    for col in colunas_numericas:
        if col in df:
            df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Processamento de colunas de coordenadas
    df['lat'] = pd.to_numeric(df['NumCoordNEmpreendimento'].str.replace(',', '.', regex=False), errors='coerce')
    df['lon'] = pd.to_numeric(df['NumCoordEEmpreendimento'].str.replace(',', '.', regex=False), errors='coerce')

    # Adiciona coluna de potência
    if 'MdaPotenciaFiscalizadaKw' in df:
        df['potencia'] = df['MdaPotenciaFiscalizadaKw']
    elif 'MdaPotenciaOutorgadaKw' in df:
        df['potencia'] = df['MdaPotenciaOutorgadaKw']
    else:
        df['potencia'] = 0

    # Mapeia tipos de geração para nomes amigáveis
    df['tipo'] = df['SigTipoGeracao'].map(TIPO_GERACAO_NOMES).fillna('Outros')
    
    # Processa município se a coluna existir
    if 'DscMuninicpios' in df:
        df['municipio'] = df['DscMuninicpios'].str.split(';').str[0]

    return df

# =============================================
# CARREGAMENTO DE DADOS
# =============================================

CSV_FILE = os.path.join(os.path.dirname(__file__), 'siga-empreendimentos-geracao.csv')
df = load_data(CSV_FILE)

if df is None:
    st.error("Não foi possível carregar os dados. Verifique o arquivo CSV.")
    st.stop()

# =============================================
# INTERFACE DO USUÁRIO
# =============================================

# Cabeçalho
st.image("logo.png", width=150)
st.title("BioEnergy")
st.write(
    "A plataforma BioEnergy oferece uma visão completa e interativa sobre as usinas de geração de energia no Brasil. "
    "Explore diferentes tipos de geração de energia, visualize sua localização no mapa e analise a potência instalada "
    "em cada região."
)

# =============================================
# BARRA LATERAL COM FILTROS
# =============================================

st.sidebar.header("Filtros")

# Filtro por tipo de geração
tipos = df['tipo'].dropna().unique().tolist()
tipos.sort()
filtro_tipo = st.sidebar.multiselect("Tipo de Geração", tipos, default=tipos)

# Filtro por estado
estados = df['SigUFPrincipal'].dropna().unique().tolist()
estados.sort()
filtro_estado = st.sidebar.multiselect("Estado", estados, default=estados)

# Filtro por faixa de potência
potencia_min, potencia_max = st.sidebar.slider(
    "Faixa de Potência (kW)",
    min_value=0.0,
    max_value=float(df['potencia'].max()),
    value=(0.0, float(df['potencia'].max()))
)

# Aplicação dos filtros
df_filtrado = df[df['tipo'].isin(filtro_tipo)]
df_filtrado = df_filtrado[df_filtrado['SigUFPrincipal'].isin(filtro_estado)]
df_filtrado = df_filtrado[
    (df_filtrado['potencia'] >= potencia_min) & 
    (df_filtrado['potencia'] <= potencia_max)
]

# =============================================
# VISUALIZAÇÃO DO MAPA
# =============================================

st.markdown("---")
st.markdown("### Mapa de Usinas")

# Prepara dados para o mapa
df_mapa = df_filtrado[
    ['lat', 'lon', 'NomEmpreendimento', 'tipo', 'municipio', 'SigUFPrincipal', 'potencia']
].dropna()

# CORREÇÃO APLICADA AQUI: Usando apply() em vez de map().fillna()
df_mapa['color'] = df_mapa['tipo'].apply(lambda x: CORES_TIPO.get(x, [180, 180, 180]))

if df_mapa.empty:
    st.warning("Nenhuma usina encontrada com os filtros atuais.")
else:
    # Configuração do layer do mapa
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_mapa,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=5000,
        pickable=True
    )

    # Configuração do tooltip
    tooltip = {
        "html": "<b>{NomEmpreendimento}</b><br/>Tipo: {tipo}<br/>Local: {municipio} - {SigUFPrincipal}<br/>Potência: {potencia:,.2f} kW",
        "style": {"backgroundColor": "#4682B4", "color": "white"}
    }

    # Renderização do mapa
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(latitude=-14.2, longitude=-51.9, zoom=4),
        layers=[layer],
        tooltip=tooltip
    ))

# Legenda interativa
st.markdown("#### 🔵 Legenda Interativa:")

num_colunas = 4
tipos_com_cores = list(CORES_TIPO.items())
for i in range(0, len(tipos_com_cores), num_colunas):
    colunas = st.columns(num_colunas)
    for j in range(num_colunas):
        if i + j < len(tipos_com_cores):
            tipo, cor = tipos_com_cores[i + j]
            with colunas[j]:
                st.markdown(
                    f"""
                    <div style='display: flex; flex-direction: column; align-items: center; cursor: pointer;'
                         onclick="document.getElementById('{tipo}').style.display = document.getElementById('{tipo}').style.display === 'block' ? 'none' : 'block';">
                        <div style='width: 20px; height: 20px; background-color: rgb{tuple(cor)};'></div>
                        <small style='text-align: center; color: black;'>{tipo}</small>
                    </div>
                    <div id='{tipo}' style='display: none; padding-top: 5px; text-align: justify; background-color: white; color: black;'>
                        {TIPO_DESCRICAO.get(tipo, 'Descrição não disponível.')}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# =============================================
# VISUALIZAÇÕES E ESTATÍSTICAS
# =============================================

st.markdown("---")
st.subheader("Análise dos Dados")

# Métricas resumidas
col1, col2, col3 = st.columns(3)
col1.metric("Total de Usinas", len(df_filtrado))
col2.metric("Potência Total (kW)", f"{df_filtrado['potencia'].sum():,.2f}")
col3.metric("Tipos de Geração", len(df_filtrado['tipo'].unique()))

# Gráfico de Pizza
if not df_filtrado.empty:
    distribuicao_tipos = df_filtrado.groupby('tipo')['potencia'].sum().reset_index()
    fig_pie = px.pie(
        distribuicao_tipos, 
        values='potencia', 
        names='tipo',
        color='tipo', 
        color_discrete_map=CORES_TIPO,
        title='Total de Potência por Tipo de Geração'
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Gráfico de Barras por Estado
if not df_filtrado.empty and 'SigUFPrincipal' in df_filtrado.columns:
    potencia_por_estado = df_filtrado.groupby('SigUFPrincipal')['potencia'].sum().reset_index()
    chart_estado = alt.Chart(potencia_por_estado).mark_bar().encode(
        x=alt.X('SigUFPrincipal', title='Estado'),
        y=alt.Y('potencia', title='Potência Total (kW)'),
        color=alt.Color('SigUFPrincipal', scale=alt.Scale(scheme='category20'), legend=None),
        tooltip=['SigUFPrincipal', 'potencia']
    ).properties(
        title='Potência Total por Estado'
    ).interactive()
    st.altair_chart(chart_estado, use_container_width=True)

# Tabela de dados e opção de download
st.subheader("Dados Filtrados")
st.dataframe(df_filtrado)

# Botão de download
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(df_filtrado)
st.download_button(
    label="Baixar Dados Filtrados (CSV)",
    data=csv,
    file_name="dados_filtrados.csv",
    mime="text/csv",
)