import streamlit as st
import pandas as pd
import os
import warnings
import pydeck as pdk

# Silencia warnings de parsing misto de datas
warnings.filterwarnings("ignore", message="Parsing dates in")

st.set_page_config(page_title="BioEnergy Dashboard", layout="wide")

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
    'QSO': 'Outros'
}

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        sep=';',
        encoding='latin1',
        dtype=str
    )
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    # Conversões numéricas
    for col in ['MdaPotenciaOutorgadaKw', 'MdaPotenciaFiscalizadaKw', 'MdaGarantiaFisicaKw']:
        if col in df:
            df[col] = df[col].str.replace(',', '.', regex=False).pipe(pd.to_numeric, errors='coerce').fillna(0)

    if 'IdcGeracaoQualificada' in df:
        df['IdcGeracaoQualificada'] = df['IdcGeracaoQualificada'].str.lower() == 'sim'

    df['lat'] = pd.to_numeric(df.get('NumCoordNEmpreendimento', pd.Series()).str.replace(',', '.', regex=False), errors='coerce')
    df['lon'] = pd.to_numeric(df.get('NumCoordEEmpreendimento', pd.Series()).str.replace(',', '.', regex=False), errors='coerce')

    if 'MdaPotenciaFiscalizadaKw' in df:
        df['potencia'] = df['MdaPotenciaFiscalizadaKw']

    # Aplica nomes amigáveis ao tipo de geração
    df['Tipo'] = df['SigTipoGeracao'].map(TIPO_GERACAO_NOMES).fillna(df['SigTipoGeracao'])

    # Extrai primeiro município se houver múltiplos
    if 'DscMuninicpios' in df:
        df['Municipio'] = df['DscMuninicpios'].str.split(';').str[0]

    return df

# Carrega os dados
CSV_FILE = os.path.join(os.path.dirname(__file__), 'siga-empreendimentos-geracao.csv')
df = load_data(CSV_FILE)

# Interface
st.title("🗺️ Mapa das Usinas de Geração (ANEEL)")
st.sidebar.header("Filtros")

# Filtro por tipo
tipos = df['Tipo'].dropna().unique().tolist()
tipos.sort()
filtro = st.sidebar.multiselect("Tipo de Geração", tipos, default=tipos)
df_filtrado = df[df['Tipo'].isin(filtro)]

# Define cores fixas por tipo
cores_tipo = {
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

# Prepara dados para o mapa
df_mapa = df_filtrado[['lat', 'lon', 'NomEmpreendimento', 'Tipo', 'Municipio', 'SigUFPrincipal', 'potencia']].dropna()

df_mapa['color'] = df_mapa['Tipo'].map(cores_tipo)

# Cria camada do mapa com pydeck
layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_mapa,
    get_position='[lon, lat]',
    get_color='color',
    get_radius=5000,
    pickable=True
)

# Tooltip interativo
tooltip = {
    "html": "<b>{NomEmpreendimento}</b><br/>"
            "Tipo: {Tipo}<br/>"
            "Local: {Municipio} - {SigUFPrincipal}<br/>"
            "Potência: {potencia} kW",
    "style": {"backgroundColor": "steelblue", "color": "white"}
}

# Exibe o mapa
st.markdown("---")
st.markdown("### Mapa de Usinas")
st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(latitude=-14.2, longitude=-51.9, zoom=4),
    layers=[layer],
    tooltip=tooltip
))

# Legenda
st.markdown("#### 🔵 Legenda das cores:")
for tipo, cor in cores_tipo.items():
    st.markdown(f"<span style='display:inline-block;width:12px;height:12px;background-color:rgb{tuple(cor)};border-radius:50%;margin-right:8px'></span>{tipo}", unsafe_allow_html=True)

# Gráfico por estado
st.markdown("---")
st.markdown("### Potência Total por Estado")
if 'SigUFPrincipal' in df_filtrado and 'potencia' in df_filtrado:
    df_estado = (
        df_filtrado
        .groupby('SigUFPrincipal')['potencia']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={'SigUFPrincipal': 'Estado', 'potencia': 'Potência (kW)'})
    )
    st.bar_chart(data=df_estado.set_index('Estado'))
else:
    st.write("Dados de UF ou potência não encontrados para o gráfico.")
