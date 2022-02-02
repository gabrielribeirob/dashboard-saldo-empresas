from dash.dependencies import Input, Output
import pandas as pd
import re, json, dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go


# ===========================
# Abrindo a planilha por abas
def open_xlsx(path_name, sheetName, colunas, index_row):
  df = pd.read_excel(
    io = path_name,
    sheet_name = sheetName,
    usecols = colunas,
    header = index_row
  )
  return df

# Aba Atacado 
df_atacado     = open_xlsx("Saldo Empresas.xlsx", "Atacado - Saldo_Atacado", "A:BK", 1)

# Aba Varejo
df_varejo      = open_xlsx("Saldo Empresas.xlsx", "Varejo - Saldo_Varejo", "A:BK", 1)

# Aba Alimentacao 
df_alimentacao = open_xlsx("Saldo Empresas.xlsx", "Negócios de alimentação - Saldo", "A:BK", 1)


# ===========================
# A coluna com as informações de localização veio com um nome errado
# Além disso a última coluna que é uma soma dos valores não precisa estar aqui (iria atrabalhar o tratamento)
# Aba Atacado
df_atacado.rename(columns={"Unnamed: 0": "location"}, inplace=True)
df_atacado.drop(df_atacado.index[-1], inplace=True)
# Aba Varejo 
df_varejo.rename(columns={"Unnamed: 0": "location"}, inplace=True)
df_varejo.drop(df_varejo.index[-1], inplace=True)
# Aba Alimentacao
df_alimentacao.rename(columns={"Unnamed: 0": "location"}, inplace=True)
df_alimentacao.drop(df_alimentacao.index[-1], inplace=True)


# ===========================
# Separando os valores da coluna location. O objtivo é obter 3 colunas: municipio e estado
def coluna_estado_municipio(df):
  """ Recebe um dataframe e retorna o mesmo com as colunas 'estado' e 'municipio' """
  lista_location = df['location'].to_list()
  # Separando Estado
  padrao_estado  = r'(-\w\w-\d)'
  estados_uf     = [re.sub(r'\d+','',re.search(padrao_estado, i, re.I).group()).replace('-','').strip() for i in lista_location]
  # Criando uma coluna de estado
  df['estado'] = estados_uf
  # Separando Município
  padrao_municipio        = r'\w+\s?((\w+)?(\s)?(\w+)?)*-?\w+[^\d\W]'
  municipios_             = [re.search(padrao_municipio, i).group() for i in lista_location]
  padrao_municipio2       = r'([^\-\W]*\s?)+'
  municipios              = [re.search(padrao_municipio2, i).group() for i in municipios_]
  df['municipio']         = municipios
  return df


df_atacado     = coluna_estado_municipio(df_atacado)
df_varejo      = coluna_estado_municipio(df_varejo)
df_alimentacao = coluna_estado_municipio(df_alimentacao)

# ===========================
# Abrindo o geojson
brazil_states = json.load(open("./brazil_geo.json", "r"))


# ===========================
# Recorte de visualização para o mapa
df_estados_2021 = df_atacado[[2021, 'estado']].groupby(['estado']).sum().reset_index()


# ===========================
# Recorte para o gráfico de linhas
def soma_ano(df):
  df_soma_ano                     = df.drop(['location', 'Total', 'municipio', 'estado'], 1)
  df_soma_ano.loc['Column_Total'] = df.sum(numeric_only=True, axis=0)
  soma                            = df_soma_ano.loc['Column_Total'].sum()
  return soma 

def coluna_total(df):
  """ Cria um linha com o valor total das colunas """
  df                     = df.drop(['location', 'Total', 'municipio', 'estado'], 1)
  df.loc['Column_Total'] = df.sum(numeric_only=True, axis=0)
  return df.loc['Column_Total'].tolist()

coluna_total_atacado      = coluna_total(df_atacado)
coluna_total_varejo       = coluna_total(df_varejo)
coluna_total_aliemntacao  = coluna_total(df_alimentacao)

# ===========================
# Selação de anos
anos_lista = df_atacado.drop(['location', 'Total', 'municipio', 'estado'], 1).columns.tolist()
anos_dict = {}
for k,v in enumerate(anos_lista):
  anos_dict[anos_lista[k]] = v

# ===========================
# Selação de colunas para o dropdown de Estados
selected_aba = {}
for i in df_atacado['estado'].tolist():
  selected_aba[i] = str(i)


# ========================
# Instanciação do Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# ========================
# Construção das figures
# 1) Mapa
fig = px.choropleth_mapbox(data_frame=df_estados_2021, locations="estado", color=2021,
                          center={"lat": -16.95, "lon": -47.78}, 
                          zoom=4,
                          geojson=brazil_states, color_continuous_scale="Redor", opacity=0.4)

fig.update_layout(
  paper_bgcolor="#242424",
  autosize=True,
  margin=go.layout.Margin(l=0, r=0, t=0, b=0),
  showlegend=False,
  mapbox_style="carto-darkmatter"
)

fig2 = go.Figure(layout={"template": "plotly_dark"})
fig2.add_trace(go.Scatter(x=anos_lista, y=coluna_total_atacado))
fig2.update_layout(
  paper_bgcolor = "#242424",
  plot_bgcolor  = "#242424",
  autosize      = True,
  margin        = dict(l=10, r=10, t=10, b=10)
)


# ========================
# Layout

app.layout = dbc.Container(
  dbc.Row([
     
    dbc.Col([
      html.Div([
        html.Img(id="logo", src=app.get_asset_url("catcry.png"), height=50),
        html.H5("Saldo das Empresas no Brasil 1960 - 2021"),
        dbc.Button("BRASIL", color="primary", id="location-button", size="md")
        ], style={}),
      
      html.Div([
        html.P("Informe o ano:", style={"margin-top": "40px"}),
        html.Div(id= 'div-dropdown-year', className='div-for-dropdown1', children=[
          dcc.Dropdown(id='year-dropdown', 
            options=[{"label":j, "value":i} for i,j in anos_dict.items()],
            value=2021,
            style={"margin-top": "10px"})
        ])
      ]),
      
      dbc.Row([
        dbc.Col([
          dbc.Card([
            dbc.CardBody([
              html.Span("Somatório Atacado", className="card-text"),
              html.H4(style={"color": "#adfc92"}, id="soma-atacado-text"),
              ])
              ], color="light", outline=True, style={"margin-top": "10px",
                  "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
                  "color": "#FFFFFF"})], md=4),
        
        dbc.Col([
          dbc.Card([
            dbc.CardBody([
              html.Span("Somatório Varejo"),
              html.H3(style={"color": "#389fd6"}, id="soma-varejo-text"),

            ])
          ], color="light", outline=True, style={"margin-top": "10px",
              "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
              "color": "#FFFFFF"})], md=4),
        
        dbc.Col([
          dbc.Card([
            dbc.CardBody([
              html.Span("Negócio de alimentação"),
              html.H3(style={"color": "#DF2935"}, id="negocio-alimentacao-text"),

            ])
          ], color="light", outline=True, style={"margin-top": "10px",
              "box-shadow": "0 4px 4px 0 rgba(0, 0, 0, 0.15), 0 4px 20px 0 rgba(0, 0, 0, 0.19)",
              "color": "#FFFFFF"})], md=4)
      ]),
      html.Div([
        html.P("Informe o estado:", style={"margin-top": "25px"}),
          html.Div(id = 'div-test', className="div-for-dropdown2", children=[
            dcc.Dropdown(id='state-dropdown', 
            options=[{"label": j, "value":i} for i, j  in selected_aba.items()],
            value= "SP",
            style={"margin-top": "10px"}), 
        dcc.Graph(id="line-graph", figure=fig2)
          ]),
    
      ]),
  
    ], md=5, style={"padding": "25px", "background-color": "#242424"}),


    dbc.Col([
      dcc.Loading(id="loading-1", type="default", 
        children=[dcc.Graph(id="choropleth-map", figure=fig, style={"height": "100vh", "margin-right": "10px"})])
    ], md=7)
  ], className="g-0"),
fluid=True)
# ========================
# Interatividade

@app.callback(
  [
    Output("soma-atacado-text", "children"),
    Output("soma-varejo-text", "children"),
    Output("negocio-alimentacao-text", "children")
  ],
  [
    Input("location-button", "children")
  ]
)

def display_status(location):
  if location=="BRASIL":
    valor_por_estado_atacado = sum(coluna_total_atacado)
  else:
    valor_por_estado_atacado = df_atacado[df_atacado["estado"] == location]
  
  if location=="BRASIL":
    valor_por_estado_varejo = []
  else:
    valor_por_estado_varejo = []
  
  soma_atacado = valor_por_estado_atacado
  return (soma_atacado,2,3)

def plot_line_graph():
  pass

# ========================
# Roda o aplicativo
if __name__ == "__main__":
  app.run_server(debug=True)