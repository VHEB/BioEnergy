import streamlit as st
import pandas as pd
import os
import warnings

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

# Título do dashboard
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
    # Adicione outros conforme necessidade
}

# Inverte legenda
legenda_invertida = {v: k for k, v in tipo_legenda.items()}

# Siglas disponíveis no DataFrame
siglas_disponiveis = df['SigTipoGeracao'].dropna().unique().tolist()
nomes_legiveis = [tipo_legenda.get(sigla, sigla) for sigla in siglas_disponiveis]

# Filtro com nomes legíveis
filtro_legivel = st.sidebar.multiselect("Tipo de Geração", nomes_legiveis, default=nomes_legiveis)
siglas_selecionadas = [legenda_invertida.get(nome, nome) for nome in filtro_legivel]

# Aplica o filtro
df_filtrado = df[df['SigTipoGeracao'].isin(siglas_selecionadas)]

# Mapa
st.markdown("---")
st.markdown("### Mapa de Usinas")
map_data = df_filtrado[['lat', 'lon']].dropna()
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
        .rename(columns={'SigUFPrincipal': 'Estado', 'potencia': 'Potência (kW)'})
    )
    st.bar_chart(data=df_estado.set_index('Estado'))
else:
    st.write("Dados de UF ou potência não encontrados para o gráfico.")
