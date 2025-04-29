import streamlit as st
import pandas as pd
import os
import warnings
import pydeck as pdk

# Silencia warnings de parsing misto de datas
warnings.filterwarnings("ignore", message="Parsing dates in")

st.set_page_config(page_title="BioEnergy Dashboard", layout="wide")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        sep=';',
        encoding='latin1',
        dtype=str
    )

    # Limpa espaços nos nomes das colunas e valores
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

    # Conversões numéricas (potências)
    for col in [
        'MdaPotenciaOutorgadaKw',
        'MdaPotenciaFiscalizadaKw',
        'MdaGarantiaFisicaKw'
    ]:
        if col in df:
            df[col] = (
                df[col]
                .str.replace(',', '.', regex=False)
                .pipe(pd.to_numeric, errors='coerce')
                .fillna(0)
            )

    # Flag booleano para geração qualificada
    if 'IdcGeracaoQualificada' in df:
        df['IdcGeracaoQualificada'] = df['IdcGeracaoQualificada'].str.lower() == 'sim'

    # Conversão de coordenadas
    df['lat'] = df.get('NumCoordNEmpreendimento', pd.Series()).str.replace(',', '.', regex=False)
    df['lon'] = df.get('NumCoordEEmpreendimento', pd.Series()).str.replace(',', '.', regex=False)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Campo de potência simplificado
    if 'MdaPotenciaFiscalizadaKw' in df:
        df['potencia'] = df['MdaPotenciaFiscalizadaKw']

    return df

# Caminho do CSV na mesma pasta do app.py
CSV_FILE = os.path.join(os.path.dirname(__file__), 'siga-empreendimentos-geracao.csv')
df = load_data(CSV_FILE)

st.title("🗺️ Mapa das Usinas de Geração (ANEEL)")

# Filtro lateral com nomes legíveis
st.sidebar.header("Filtros")

tipo_legenda = {
    'UHE': 'Hidrelétrica de Grande Porte',
    'PCH': 'Pequena Central Hidrelétrica',
    'CGH': 'Central Geradora Hidrelétrica',
    'EOL': 'Eólica',
    'UFV': 'Fotovoltaica (Solar)',
    'UTE': 'Termelétrica',
    'UTN': 'Nuclear',
    'BIO': 'Biomassa',
    'UHE/BIO': 'Hidrelétrica/Biomassa',
    'UTE/BIO': 'Termelétrica/Biomassa',
}

# Paleta de cores RGB para cada tipo
cores_por_tipo = {
    'UHE': [0, 100, 255],
    'PCH': [0, 180, 255],
    'CGH': [0, 230, 255],
    'EOL': [0, 200, 0],
    'UFV': [255, 200, 0],
    'UTE': [255, 0, 0],
    'UTN': [160, 0, 160],
    'BIO': [100, 255, 100],
    'UHE/BIO': [140, 180, 255],
    'UTE/BIO': [255, 100, 100],
}

# Inverte legenda
legenda_invertida = {v: k for k, v in tipo_legenda.items()}

# Filtro
siglas_disponiveis = df['SigTipoGeracao'].dropna().unique().tolist()
nomes_legiveis = [tipo_legenda.get(sigla, sigla) for sigla in siglas_disponiveis]
filtro_legivel = st.sidebar.multiselect("Tipo de Geração", nomes_legiveis, default=nomes_legiveis)
siglas_selecionadas = [legenda_invertida.get(nome, nome) for nome in filtro_legivel]

# Aplica o filtro
df_filtrado = df[df['SigTipoGeracao'].isin(siglas_selecionadas)]

# Mapa com pydeck
st.markdown("---")
st.markdown("### Mapa de Usinas")

df_mapa = df_filtrado[['lat', 'lon', 'SigTipoGeracao']].dropna()
df_mapa['color'] = df_mapa['SigTipoGeracao'].apply(lambda x: cores_por_tipo.get(x, [100, 100, 100]))

layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_mapa,
    get_position='[lon, lat]',
    get_fill_color='color',
    get_radius=30000,
    pickable=True,
    opacity=0.8
)

view_state = pdk.ViewState(latitude=-14.2, longitude=-51.9, zoom=4)

r = pdk.Deck(layers=[layer], initial_view_state=view_state)
st.pydeck_chart(r)

# Legenda abaixo do mapa
st.markdown("### Legenda das Cores")
for sigla, nome in tipo_legenda.items():
    if sigla in siglas_disponiveis:
        cor = cores_por_tipo.get(sigla, [150, 150, 150])
        cor_hex = '#%02x%02x%02x' % tuple(cor)
        st.markdown(f"<div style='display: flex; align-items: center;'>"
                    f"<div style='width: 20px; height: 20px; background-color: {cor_hex}; margin-right: 10px;'></div>"
                    f"{nome}</div>", unsafe_allow_html=True)

# Gráfico de barras
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
