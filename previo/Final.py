import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

# Caminhos dos arquivos
CSV_PATH = r"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Data\isozonas_1dia copy.csv"
SHAPEFILE_PATH = r"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Isozonas_GrausDecimais (1)\Isozonas_GrausDecimais.shp"

# Durações
DURACOES_HORAS = [6/60, 10/60, 15/60, 20/60, 25/60, 30/60, 1, 2, 3, 4, 6, 8, 10, 12, 18, 24]
# 6 min --> até 24hr

# Carrega o shapefile e retorna a zona
def get_isozona(lat: float, lon: float) -> str | None:
    
    gdf = gpd.read_file(SHAPEFILE_PATH)
    
    # Cria o ponto em WGS84 e converte para o CRS do shapefile
    ponto = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
    ponto = ponto.to_crs(gdf.crs).iloc[0]
    
    # Busca a zona que contém o ponto
    for _, row in gdf.iterrows():
        if row.geometry.contains(ponto):
            return row['ZONA']
    
    return None


# Carrega os dados do csv e filtra pela zona especificada pelas coordenadas
def carregar_dados(zona: str) -> pd.DataFrame:

    df = pd.read_csv(CSV_PATH)
    df_zona = df[df['isozona'].str.strip().str.upper() == zona.strip().upper()]
    
    if df_zona.empty:
        zonas_disponiveis = df['isozona'].unique()
        raise ValueError(f"Zona '{zona}' não encontrada. Zonas disponíveis: {list(zonas_disponiveis)}")
    
    return df_zona

# Calcula os valores base de precipitação para 24h, 1h e 6min
def calcular_precipitacao_base(df_zona: pd.DataFrame) -> pd.DataFrame:

    resultado = df_zona.copy()
    resultado['precip_24h'] = resultado['precipitacao'] * 1.14
    resultado['precip_1h'] = (resultado['precip_24h'] * resultado['coef_1h_24h']) / 100
    resultado['precip_6min'] = (resultado['precip_24h'] * resultado['coef_6min_24h']) / 100
    return resultado

# Calcula coeficientes a e b da equação y = a·ln(x) + b
def calcular_coeficientes_log(x1: float, y1: float, x2: float, y2: float) -> tuple:

    ln_x1 = np.log(x1) #ln x1
    ln_x2 = np.log(x2) #ln x2
    a = (y2 - y1) / (ln_x2 - ln_x1) #coeficiente angular 
    b = y1 - a * ln_x1 #coeficiente linear
    return a, b

# Interpola precipitação para uma duração específica usando as equações logarítmicas
def interpolar_precipitacao(duracao_h: float, p_6min: float, p_1h: float, p_24h: float) -> float:
    if duracao_h < 1:
        # Equação 1: 6min (0.1h) até 1h
        a, b = calcular_coeficientes_log(0.1, p_6min, 1.0, p_1h)
    else:
        # Equação 2: 1h até 24h
        a, b = calcular_coeficientes_log(1.0, p_1h, 24.0, p_24h)
    
    return a * np.log(duracao_h) + b

# Formata a duração para exibição
def formatar_duracao(duracao_h: float) -> str:
    if duracao_h < 1:
        minutos = int(duracao_h * 60)
        return f"{minutos} min"
    else:
        return f"{int(duracao_h)} h"

# Gera tabela com precipitações interpoladas para todas as durações
def gerar_tabela(df_base: pd.DataFrame) -> pd.DataFrame:
    tabela = []
    # Atua sobre as durações
    for duracao in DURACOES_HORAS:
        linha = {'Duração': formatar_duracao(duracao)}
        
        for _, row in df_base.iterrows():
            tr = int(row['tempo_retorno'])
            precip = interpolar_precipitacao(
                duracao,
                row['precip_6min'],
                row['precip_1h'],
                row['precip_24h']
            )
            linha[f'TR {tr}'] = precip
        
        tabela.append(linha)
    
    return pd.DataFrame(tabela)


def exibir_tabela(df_tabela: pd.DataFrame, zona: str, lat: float, lon: float):
    """Exibe a tabela de precipitações interpoladas."""
    print("=" * 142)
    print(f"TABELA DE PRECIPITAÇÃO (mm)")
    print(f"Coordenadas: ({lat}, {lon}) - Zona: {zona.upper()}")
    print("=" * 142)
    
    # Cabeçalho
    colunas = df_tabela.columns.tolist()
    header = f"{'Duração':<10}"
    for col in colunas[1:]:
        header += f"{col:>12}"
    print(header)
    print("-" * 142)
    
    # Dados
    for _, row in df_tabela.iterrows():
        linha = f"{row['Duração']:<10}"
        for col in colunas[1:]:
            linha += f"{row[col]:>12.2f}"
        print(linha)
    
    print("=" * 142)


def main():
    #input Lat e Lon
    try:
        latitude = float(input("Digite a latitude: "))
        longitude = float(input("Digite a longitude: "))
    except ValueError:
        print("Erro: Valores inválidos para latitude/longitude.")
        return
    
    # Identifica a zona pela coordenada
    zona = get_isozona(latitude, longitude)
    
    if zona is None:
        print(f"\nErro: Coordenada ({latitude}, {longitude}) está fora das isozonas.")
        return
    
    print(f"\nZona identificada: {zona}")
    
    try:
        # Carregar dados da zona
        df_zona = carregar_dados(zona)
        
        # Calcular precipitações base 
        df_base = calcular_precipitacao_base(df_zona)
        
        # Calcula os valores de precipitação da chuva para diferentes durações e gera a tabela
        df_tabela = gerar_tabela(df_base)
        print()
        exibir_tabela(df_tabela, zona, latitude, longitude)
        
    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e}")
    except ValueError as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()
