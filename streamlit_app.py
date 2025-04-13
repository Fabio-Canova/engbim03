import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import matplotlib.pyplot as plt
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from streamlit.components.v1 import html
import json

########################################################
import warnings
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")


########################################################
##########TITULOS#######################################
########################################################
# Define o layout da página para 'wide'
st.set_page_config(layout="wide")

st.title("ENGEBIM - Modelo de apresetação")



###################################################
##########BUSCA OS ARQUIVOS########################
###################################################

# Função para remover ou substituir caracteres indesejados
def importar_CSV(caminho_arquivo):

    df = pd.read_csv(caminho_arquivo,
                                sep=";",  # Delimitador usado no CSV
                                header = 0,
                                encoding="utf-8",  # Define a codificação do arquivo
                                na_values=["<Nenhum>","NaN","N/A", "", "NULL"],  # Considera "NaN", valores vazios e "NULL" como NaN
                                encoding_errors='replace',
                                on_bad_lines="skip",
                                keep_default_na=False,  # Ignora os valores padrão do Pandas para NaN
                                na_filter=True,  # Mantém a detecção de NaN ativada
                                skip_blank_lines=False,  # Mantém as linhas em branco
                                low_memory=False,  # Habilita leitura em pedaços menores para economizar memória
                                memory_map=True  # Usa mapeamento de memória para leitura mais rápida
    ) #Elementos
    df.fillna("")

    # Retorna o DataFrame com os dados limpos
    return df

# Carregar os CSVs como DataFrames
@st.cache_data
def load_table_1():
    # Carrega a primeira tabela
    arquivo_elmentos="data/elementos.csv"
    return importar_CSV(arquivo_elmentos)

@st.cache_data
def load_table_2():
    # Carrega a segunda tabela
    arquivo_elmentos_unique="data/elementos_unique.csv"
    return importar_CSV(arquivo_elmentos_unique)

@st.cache_data
def load_table_3():
    # Carrega a terceira tabela
    arquivo_elmentos_xyz="data/elementos_xyz.csv"
    return importar_CSV(arquivo_elmentos_xyz)

@st.cache_data
def load_table_4():
    # Carrega a quarta tabela
    arquivo_elmentos_unique_transp="data/elementos_unique_transp.csv"
    return importar_CSV(arquivo_elmentos_unique_transp)

# Carrega as tabelas
df_elementos = load_table_1()
df_elementos_unique = load_table_2()
df_elementos_xyz = load_table_3()
df_elementos_unique_transp = load_table_4()


#Remove registros desnecessarios
def filter_dataframe(df: pd.DataFrame, filters: dict, exclude: dict = None):
    """Filtra um DataFrame para conter apenas as linhas onde as colunas especificadas têm determinados valores,
    e exclui linhas onde as colunas especificadas têm determinados valores."""
    for column, value in filters.items():
        df = df[df[column] == value]
    if exclude:
        for column, value in exclude.items():
            df = df[df[column] != value]
    return df

filters = {"tagnum": "OK"}
exclude = {"Parametro_group": "OUTROS"}
df_elementos_filter = filter_dataframe(df_elementos, filters, exclude)
df_elementos_unique_filter = filter_dataframe(df_elementos_unique, filters, exclude)

#Converte para numerico
df_elementos['Valuenum'] = pd.to_numeric(df_elementos['Valuenum'], errors='coerce')
df_elementos_unique['Valuenum'] = pd.to_numeric(df_elementos_unique['Valuenum'], errors='coerce')
df_elementos_xyz['X'] = pd.to_numeric(df_elementos_xyz['X'], errors='coerce')
df_elementos_xyz['Y'] = pd.to_numeric(df_elementos_xyz['Y'], errors='coerce')
df_elementos_xyz['Z'] = pd.to_numeric(df_elementos_xyz['Z'], errors='coerce')
df_elementos_unique_transp['Altura'] = pd.to_numeric(df_elementos_unique_transp['Altura'], errors='coerce')
df_elementos_unique_transp['Comprimento'] = pd.to_numeric(df_elementos_unique_transp['Comprimento'], errors='coerce')
df_elementos_unique_transp['Contador'] = pd.to_numeric(df_elementos_unique_transp['Contador'], errors='coerce')
df_elementos_unique_transp['Área'] = pd.to_numeric(df_elementos_unique_transp['Área'], errors='coerce')
df_elementos_unique_transp['Área Calculada'] = pd.to_numeric(df_elementos_unique_transp['Área Calculada'], errors='coerce')
 
# Unindo as tabelas para criar um banco de dados único
df_completo = df_elementos_unique_transp.merge(df_elementos_xyz, on="Element ID", how="left")
df_completo = df_completo.rename(columns={'Área':'Area'})


###################################################
######## FILROS ###################################
# Usando groupby para agrupar por 'Categoria' e somar os valores de 'Valor' e 'Quantidade'
df = df_completo

# 1. Estado da sessão para armazenar filtros
# 1. Estado da sessão para armazenar filtros
if 'filtros' not in st.session_state:
    st.session_state.filtros = {
        'Category': [],
        'Level': [],
        'Family': [],
        'Type': []
    }

# 2. Função para aplicar filtros ao DataFrame
def aplicar_filtros(df, filtros):
    for coluna, valores in filtros.items():
        if valores and coluna in df.columns:
            df = df[df[coluna].isin(valores)]
    return df

# 3. Função para criar tabelas de filtro simplificadas
def criar_tabela_filtro(titulo, coluna_filtro, df_filtrado):
    # Agrupar dados
    df_agg = df_filtrado.groupby(coluna_filtro).agg({
        'Comprimento': 'sum',
        'Contador': 'sum',
        'Area': 'sum'
    }).reset_index()
    
    # Adicionar coluna de seleção
    df_agg['Selecionar'] = df_agg[coluna_filtro].isin(st.session_state.filtros[coluna_filtro])
    
    # Formatar números para exibição
    df_exibicao = df_agg.copy()
    for col in ['Comprimento', 'Contador', 'Area']:
        df_exibicao[col] = df_exibicao[col].apply(
            lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) else x
        )
    
    # Exibir tabela
    st.subheader(titulo)
    edited_df = st.data_editor(
        df_exibicao,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(
                "Selecionar",
                help=f"Selecione os {titulo.split()[-1]}s para filtrar",
                default=False
            )
        },
        hide_index=True,
        disabled=df_exibicao.columns.drop('Selecionar'),
        height=200,
        key=f"tabela_{coluna_filtro}"
    )
    
    # Atualizar filtros
    selecionados = edited_df[edited_df['Selecionar']][coluna_filtro].tolist()
    if set(selecionados) != set(st.session_state.filtros[coluna_filtro]):
        st.session_state.filtros[coluna_filtro] = selecionados
        st.rerun()

# 4. Aplicar filtros atuais para obter base filtrada
df_filtrado = aplicar_filtros(df, st.session_state.filtros)

# 5. Layout das tabelas de filtro
col1, col2 = st.columns(2)

# Primeira coluna
with col1:
    criar_tabela_filtro("Tabela de Category", "Category", df_filtrado)
    st.write("")  # Espaçamento
    criar_tabela_filtro("Tabela de Level", "Level", df_filtrado)

# Segunda coluna
with col2:
    criar_tabela_filtro("Tabela de Family", "Family", df_filtrado)
    st.write("")  # Espaçamento
    criar_tabela_filtro("Tabela de Type", "Type", df_filtrado)

# 6. Mostrar totais antes da tabela de resultados
st.subheader("Resultados Filtrados")


# 9. Botão para limpar filtros
if st.button("🔄 Limpar Todos os Filtros"):
    st.session_state.filtros = {
        'Category': [],
        'Level': [],
        'Family': [],
        'Type': []
    }
    st.rerun()


# Garantir que as colunas numéricas sejam tratadas corretamente
df_filtrado_numerico = df_filtrado.copy()
for col in ['Comprimento', 'Contador', 'Area']:
    df_filtrado_numerico[col] = df_filtrado_numerico[col].apply(
        lambda x: float(x) if str(x).replace('.','',1).isdigit() else 0
    )

# Cards de totalização antes da tabela
if not df_filtrado_numerico.empty:
    # Criar 3 colunas para os cards
    total_col1, total_col2, total_col3 = st.columns(3)
    
    with total_col1:
        st.metric(
            label="📏 Total Comprimento", 
            value=f"{df_filtrado_numerico['Comprimento'].sum():,.0f}",
            help="Soma total da coluna Comprimento"
        )
    
    with total_col2:
        st.metric(
            label="🔢 Total Contador", 
            value=f"{df_filtrado_numerico['Contador'].sum():,.0f}",
            help="Soma total da coluna Contador"
        )
    
    with total_col3:
        st.metric(
            label="📊 Total Area", 
            value=f"{df_filtrado_numerico['Area'].sum():,.0f}",
            help="Soma total da coluna Area"
        )


#####GRAFICO################
# Criar 3 colunas para os gráficos
# Agregar os dados por Level
df_agg = df_filtrado_numerico.groupby('Level', as_index=False).agg({
    'Comprimento': 'sum',
    'Contador': 'sum',
    'Area': 'sum'
})

# Configurações comuns para os gráficos
config = {
    'displaylogo': False,
    'modeBarButtonsToAdd': [
        'zoom2d',
        'pan2d',
        'zoomIn2d', 
        'zoomOut2d',
        'autoScale2d',
        'resetScale2d',
        'toImage'
    ],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'custom_image',
        'height': 500,
        'width': 700,
        'scale': 1
    }
}

# Criar 3 colunas para os gráficos
col1, col2, col3 = st.columns(3)

# Gráfico 1: Comprimento total por Level
with col1:
    st.markdown("### Comprimento Total por Level")
    fig1 = px.bar(df_agg, x='Level', y='Comprimento', 
                 color='Level', text='Comprimento',
                 template='plotly_white')
    fig1.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig1.update_layout(
        xaxis_title='Level',
        yaxis_title='Comprimento Total',
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig1, use_container_width=True, config=config)

# Gráfico 2: Contador total por Level
with col2:
    st.markdown("### Contador Total por Level")
    fig2 = px.bar(df_agg, x='Level', y='Contador', 
                 color='Level', text='Contador',
                 template='plotly_white')
    fig2.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig2.update_layout(
        xaxis_title='Level',
        yaxis_title='Contador Total',
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig2, use_container_width=True, config=config)

# Gráfico 3: Area total por Level
with col3:
    st.markdown("### Area Total por Level")
    fig3 = px.bar(df_agg, x='Level', y='Area', 
                 color='Level', text='Area',
                 template='plotly_white')
    fig3.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig3.update_layout(
        xaxis_title='Level',
        yaxis_title='Area Total',
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig3, use_container_width=True, config=config)








# 7. Exibir tabela de resultados
# Formatar números para exibição
# Prepara interação
# Configuração do estado da sessão
if 'element_id' not in st.session_state:
    st.session_state.element_id = ""
if 'selected_index' not in st.session_state:
    st.session_state.selected_index = None

# Preparar DataFrame para exibição
df_exibicao = df_filtrado_numerico[['Element ID','Element Name','Category', 'Family', 'Type','Level','Comprimento','Contador','Area']].copy()
for col in ['Comprimento', 'Contador', 'Area']:
    df_exibicao[col] = df_exibicao[col].apply(lambda x: f"{x:,.0f}")

# Adicionar coluna de seleção
df_exibicao['Selecionar'] = False
if st.session_state.selected_index is not None and st.session_state.selected_index in df_exibicao.index:
    df_exibicao.loc[st.session_state.selected_index, 'Selecionar'] = True

# Exibir tabela interativa
st.write("Clique em uma linha para selecionar o elemento (apenas uma seleção permitida):")
edited_df = st.data_editor(
    df_exibicao,
    column_config={
        "Selecionar": st.column_config.CheckboxColumn(
            "Selecionar",
            help="Selecione uma linha para escolher o elemento",
            default=False
        )
    },
    hide_index=True,
    disabled=df_exibicao.columns.drop('Selecionar'),
    height=300,
    use_container_width=True,
    key="element_table"
)



# 8. Mostrar resumo dos filtros
#st.subheader("Filtros Aplicados")
#filtros_aplicados = False
#for coluna in ['Category', 'Level', 'Family', 'Type']:
#    if st.session_state.filtros[coluna]:
#        st.write(f"- {coluna}: {', '.join(st.session_state.filtros[coluna])}")
#        filtros_aplicados = True
#
#if not filtros_aplicados:
#    st.info("Nenhum filtro aplicado. Selecione itens nas tabelas acima para filtrar.")


###################################################
######## CRIA 3D###################################

##################################################
########### ELEMENTO #############################





st.title("Visualizador 3D de Modelos Revit")

# Campo de input para Element ID
element_id = st.text_input(
    "Digite o ID do elemento:",
    value=st.session_state.element_id,
    key="element_input"
)

# Atualizar session_state quando o input é alterado manualmente
if element_id != st.session_state.element_id:
    st.session_state.element_id = element_id
    st.session_state.selected_index = None
    st.rerun()

# Processar seleção - garantindo apenas uma seleção
selected_rows = edited_df[edited_df['Selecionar']]
if len(selected_rows) > 1:
    # Se mais de uma linha estiver selecionada, manter apenas a última
    selected_index = selected_rows.index[-1]
    selected_element_id = selected_rows.iloc[-1]['Element ID']
    st.session_state.element_id = selected_element_id
    st.session_state.selected_index = selected_index
    st.rerun()
elif len(selected_rows) == 1:
    selected_index = selected_rows.index[0]
    selected_element_id = selected_rows.iloc[0]['Element ID']
    if selected_element_id != st.session_state.element_id:
        st.session_state.element_id = selected_element_id
        st.session_state.selected_index = selected_index
        st.rerun()
elif st.session_state.selected_index is not None:
    st.session_state.element_id = ""
    st.session_state.selected_index = None
    st.rerun()

viewer_html = f"""
<div style="width: 100%; height: 800px;">
    <iframe
        src="https://fabio-canova.github.io/meu-visualizador-3d/"
        id="model-viewer"
        width="100%"
        height="100%"
        frameborder="0"
        style="border: none;"
        allowfullscreen
    ></iframe>
</div>

<script>
    // Função simplificada e robusta
    function sendToViewer(elementId) {{
        try {{
            const iframe = document.getElementById('model-viewer');
            if (iframe && iframe.contentWindow) {{
                iframe.contentWindow.postMessage(
                    {{
                        type: 'streamlit-focus',
                        elementId: String(elementId || '')
                    }},
                    'https://fabio-canova.github.io'
                );
            }}
        }} catch (error) {{
            console.error('Erro ao enviar para viewer:', error);
        }}
    }}

    // Listener seguro para o campo de entrada
    const setup = () => {{
        const input = document.querySelector('input[aria-label="Digite o ID do elemento:"]');
        if (input) {{
            input.addEventListener('keyup', function(e) {{
                if (e.key === 'Enter') {{
                    sendToViewer(this.value);
                }}
            }});
        }} else {{
            setTimeout(setup, 100);
        }}
    }};

    // Inicialização segura
    document.addEventListener('DOMContentLoaded', function() {{
        setup();
        setTimeout(() => sendToViewer({json.dumps(element_id)}), 1500);
    }});
</script>
"""

html(viewer_html, height=800)

if element_id != st.session_state.element_id:
    st.session_state.element_id = element_id