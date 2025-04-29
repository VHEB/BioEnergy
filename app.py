import streamlit as st
import pandas as pd
import os
import warnings

# Silencia warnings de parsing misto de datas
warnings.filterwarnings("ignore", message="Parsing dates in")

st.set_page_config(page_title="BioEnergy Dashboard", layout="wide")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    # Lê tudo como string para maior controle
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

    # Conversão de coordenadas para floats
    df['lat'] = df.get('NumCoordNEmpreendimento', pd.Series()).str.replace(',', '.', regex=False)
    df['lon'] = df.get('NumCoordEEmpreendimento', pd.Series()).str.replace(',', '.', regex=False)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

    # Campo de potência simplificado
    if 'MdaPotenciaFiscalizadaKw' in df:
        df['potencia'] = df['MdaPotenciaFiscalizadaKw']

    return df

# Caminho do CSV deve estar na mesma pasta do app.py
CSV_FILE = os.path.join(os.path.dirname(__file__), 'siga-empreendimentos-geracao.csv')
df = load_data(CSV_FILE)

# Título do dashboard
st.title("🗺️ Mapa das Usinas de Geração (ANEEL)")

# Debug de coordenadas antes do mapa
st.write("### Amostra de coordenadas (lat/lon)", df[['lat', 'lon']].head(10))
st.write("### Contagem de coordenadas válidas:", df[['lat','lon']].notnull().sum().to_frame(name='valid_count'))

# Filtros de tipo de geração
st.sidebar.header("Filtros")
tipos = df['SigTipoGeracao'].dropna().unique().tolist()
filtro = st.sidebar.multiselect("Tipo de Geração", tipos, default=tipos)
df_filtrado = df[df['SigTipoGeracao'].isin(filtro)]

# Mapa interativo
st.markdown("---")
st.markdown("### Mapa de Usinas")
map_data = df_filtrado[['lat','lon']].dropna()
st.map(map_data, zoom=4)

# Gráfico de barras por estado
st.markdown("---")
st.markdown("### Potência Total por Estado")
if 'SigUFPrincipal' in df_filtrado and 'potencia' in df_filtrado:
    df_estado = (
        df_filtrado
        .groupby('SigUFPrincipal')['potencia']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={'SigUFPrincipal':'Estado','potencia':'Potência (kW)'})
    )
    st.bar_chart(data=df_estado.set_index('Estado'))
else:
    st.write("Dados de UF ou potência não encontrados para o gráfico.")
