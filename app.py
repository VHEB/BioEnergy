import streamlit as st
import pandas as pd
import os
import warnings
import pydeck as pdk
import altair as alt
import plotly.express as px

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
    'QSO': 'Outros',
    'UTN': 'Outros'  # Adicionado 'UTN' para corrigir o KeyError
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
    'Outros': 'Outros tipos de geração de energia elétrica.',
    'UTN': 'Outros tipos de geração de energia elétrica não especificados.'  # Descrição para UTN
}


def standardize_column_name(col_name: str) -> str:
    """
    Standardiza o nome de uma coluna, convertendo para minúsculas e substituindo espaços por underscores.

    Args:
        col_name: O nome da coluna a ser padronizado.

    Returns:
        O nome da coluna padronizado.
    """
    return col_name.lower().replace(' ', '_')


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """
    Carrega os dados de um arquivo CSV, realiza a limpeza e conversão de tipos.

    Args:
        path: O caminho para o arquivo CSV.

    Returns:
        Um DataFrame com os dados carregados e processados.
    """
    try:
        df = pd.read_csv(
            path,
            sep=';',
            encoding='latin1',
            dtype=str
        )
    except FileNotFoundError:
        st.error(f"Erro: Arquivo não encontrado em {path}. Verifique se o caminho está correto.")
        return None  # Retorna None em caso de erro

    # df.columns = [standardize_column_name(c) for c in df.columns]  # Remove a padronização aqui

    # Verifica se a coluna 'SigTipoGeracao' existe
    if 'SigTipoGeracao' not in df.columns:
        st.error(
            f"Erro: A coluna 'SigTipoGeracao' não foi encontrada no arquivo CSV. Verifique se o arquivo contém os dados corretos e se o nome da coluna está correto.")
        return None  # Retorna None em caso de erro

    # Imprime os nomes das colunas para debug
    print("Nomes das colunas no DataFrame:")
    print(df.columns)

    for col in ['MdaPotenciaOutorgadaKw', 'MdaPotenciaFiscalizadaKw', 'MdaGarantiaFisicaKw']:
        if col in df:
            df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            na_count = df[col].isnull().sum()
            if na_count > 0:
                st.warning(f"Encontrados {na_count} valores não numéricos na coluna '{col}'. Substituindo por 0.")
            df[col] = df[col].fillna(0)

    if 'IdcGeracaoQualificada' in df:
        df['IdcGeracaoQualificada'] = df['IdcGeracaoQualificada'].str.lower() == 'sim'

    df['lat'] = pd.to_numeric(df.get('NumCoordNEmpreendimento', pd.Series()).str.replace(',', '.', regex=False),
                             errors='coerce')
    df['lon'] = pd.to_numeric(df.get('NumCoordEEmpreendimento', pd.Series()).str.replace(',', '.', regex=False),
                             errors='coerce')

    if 'MdaPotenciaFiscalizadaKw' in df:
        df['potencia'] = df['MdaPotenciaFiscalizadaKw']

    df['tipo'] = df['SigTipoGeracao'].map(TIPO_GERACAO_NOMES).fillna(df['SigTipoGeracao'])

    if 'DscMuninicpios' in df:
        df['municipio'] = df['DscMuninicpios'].str.split(';').str[0]

    return df


CSV_FILE = os.path.join(os.path.dirname(__file__), 'siga-empreendimentos-geracao.csv')
df = load_data(CSV_FILE)

if df is not None:  # Verifica se os dados foram carregados corretamente
    st.image("logo.png", width=150)
    st.title("BioEnergy")
    st.write(
        "A plataforma BioEnergy oferece uma visão completa e interativa sobre as usinas de geração de energia no Brasil. Explore diferentes tipos de geração de energia, visualize sua localização no mapa e analise a potência instalada em cada região.")

    st.sidebar.header("Filtros")
    tipos = df['tipo'].dropna().unique().tolist()
    tipos.sort()
    filtro = st.sidebar.multiselect("Tipo de Geração", tipos, default=tipos)
    df_filtrado = df[df['tipo'].isin(filtro)]

    # --- Adicionando Filtros ---
    estados = df['SigUFPrincipal'].dropna().unique().tolist()
    estados.sort()
    filtro_estado = st.sidebar.multiselect("Estado", estados, default=estados)
    df_filtrado = df_filtrado[df['SigUFPrincipal'].isin(filtro_estado)]

    potencia_min, potencia_max = st.sidebar.slider("Faixa de Potência (kW)",
                                                 min_value=0.0,
                                                 max_value=float(df['potencia'].max()),
                                                 value=(0.0, float(df['potencia'].max())))
    df_filtrado = df_filtrado[(df_filtrado['potencia'] >= potencia_min) & (df_filtrado['potencia'] <= potencia_max)]

    # Definindo cores_tipo
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
        'Outros': [180, 180, 180],
        'UTN': [180, 180, 180]  # Cor padrão para UTN
    }

    df_mapa = df_filtrado[
        ['lat', 'lon', 'NomEmpreendimento', 'tipo', 'municipio', 'SigUFPrincipal', 'potencia']].dropna()
    df_mapa['color'] = df_mapa['tipo'].map(cores_tipo)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_mapa,
        get_position='[lon, lat]',
        get_color='color',
        get_radius=5000,
        pickable=True
    )

    tooltip = {
        "html": "<b>{NomEmpreendimento}</b><br/>Tipo: {tipo}<br/>Local: {municipio} - {sig_uf_principal}<br/>Potência: {potencia} kW",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }

    st.markdown("---")
    st.markdown("### Mapa de Usinas")
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(latitude=-14.2, longitude=-51.9, zoom=4),
        layers=[layer],
        tooltip=tooltip
    ))

    st.markdown("#### 🔵 Legenda Interativa:")

    # Usando columns para organizar os quadrados lado a lado
    num_colunas = 4  # Número de colunas desejado
    tipos_com_cores = list(cores_tipo.items())
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

    # --- Adicionando Visualizações e Resumos ---

    st.markdown("---")
    st.subheader("Análise dos Dados")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total de Usinas", len(df_filtrado))
    col2.metric("Potência Total (kW)", f"{df_filtrado['potencia'].sum():,.2f}")
    col3.metric("Tipos de Geração", len(df_filtrado['tipo'].unique()))


    # Gráfico de Pizza
    distribuicao_tipos = df_filtrado.groupby('tipo')['potencia'].sum().reset_index()
    distribuicao_tipos.columns = ['tipo', 'potencia']
    fig_pie = px.pie(distribuicao_tipos, values='potencia', names='tipo',
                 color='tipo', color_discrete_map=cores_tipo,
                 title='Total de Potência por Tipo de Geração')
    st.plotly_chart(fig_pie, use_container_width=True)

    # Gráfico de Geração por Estado
    potencia_por_estado = df_filtrado.groupby('SigUFPrincipal')['potencia'].sum().reset_index()
    if not potencia_por_estado.empty:
        chart_estado = alt.Chart(potencia_por_estado).mark_bar().encode(
            x=alt.X('SigUFPrincipal', title='Estado'),
            y=alt.Y('potencia', title='Potência Total (kW)'),
            color=alt.Color('SigUFPrincipal',
                            scale=alt.Scale(domain=estados, range=list(cores_tipo.values())[:len(estados)])
                            , legend=alt.Legend(title="Estado")
                            ),
            tooltip=['SigUFPrincipal', 'potencia']
        ).properties(
            title='Potência Total por Estado'
        ).interactive()
        st.altair_chart(chart_estado, use_container_width=True)
    else:
        st.warning("Não há dados suficientes para exibir o gráfico de Potência Total por Estado com os filtros selecionados.")


    # Tabela de Dados
    st.subheader("Dados Filtrados")
    st.dataframe(df_filtrado)

    # Download dos Dados
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')


    csv = convert_df_to_csv(df_filtrado)

    st.download_button(
        label="Baixar Dados Filtrados (CSV)",
        data=csv,
        file_name="dados_filtrados.csv",
        mime="text/csv",
    )
