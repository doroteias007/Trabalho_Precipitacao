"""
Módulo para cálculo de precipitação por isozonas.

Este script identifica a isozona de uma coordenada geográfica e calcula
valores de precipitação interpolados para diferentes durações e tempos
de retorno.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
"""
Caminhos dos arquivos
Siga essa ordem de colunas no seu arquivo.csv de precipitação
Leve em consideracao que esses precisam ser os nomes das colunas:
    Isozona, Tempo_retorno, Duracao, Precipitacao
altere apenas o CSV_PRECIPITACAO, qualquer outro dado alterado vai resultar em erros.
"""

# =============================================================================
# CONFIGURACAO - Defina os caminhos dos arquivos aqui
# =============================================================================
CSV_COEFICIENTES = (
    r"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Data\isozonas_coeficientes.csv"
    
)
CSV_PRECIPITACAO = (
    r"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Data\isozonas_precipitacao.csv"
)
# =============================================================================

# Shapefile das isozonas
SHAPEFILE_PATH = (
    r"C:\Users\joser\projects\Codes\Python"
    r"\Trabalho Qgis Areas\Isozonas_GrausDecimais (1)\Isozonas_GrausDecimais.shp"
)

# Colunas esperadas no arquivo de precipitação
COLUNAS_PRECIPITACAO = ['isozona', 'tempo_retorno', 'duracao', 'precipitacao']
COLUNAS_COEFICIENTES = ['isozona', 'coef_1h_24h', 'coef_6min_24h']

# Durações em horas (6 min até 24h)
DURACOES_HORAS = [
    6/60, 10/60, 15/60, 20/60, 25/60, 30/60,
    1, 2, 3, 4, 6, 8, 10, 12, 18, 24
]


def get_isozona(lat: float, lon: float) -> str | None:
    """
    Carrega o shapefile e retorna a zona correspondente à coordenada.

    Argumentos:
        lat: Latitude da coordenada em graus decimais.
        lon: Longitude da coordenada em graus decimais.

    Retornos:
        Nome da zona ou None se a coordenada estiver fora das isozonas.
    """
    gdf = gpd.read_file(SHAPEFILE_PATH)

    # Cria o ponto em WGS84 e converte para o CRS do shapefile
    ponto = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
    ponto = ponto.to_crs(gdf.crs).iloc[0]

    # Busca a zona que contém o ponto
    for _, row in gdf.iterrows():
        if row.geometry.contains(ponto):
            return row['ZONA']

    return None


def validar_csv_precipitacao(df: pd.DataFrame) -> bool:
    """
    Valida se o DataFrame de precipitação tem as colunas corretas.
    DataFrame = estrutura bidimensional de dados(tabela)

    Argumentos:
        df: DataFrame carregado do CSV de precipitação.
    Retornos:
        True se válido, False caso contrário.
    """
    colunas_presentes = [col.lower().strip() for col in df.columns]
    colunas_esperadas = [col.lower() for col in COLUNAS_PRECIPITACAO]
    return all(col in colunas_presentes for col in colunas_esperadas)


def carregar_csv_com_decimal(caminho: str) -> pd.DataFrame:
    """
    Carrega um CSV detectando automaticamente o separador decimal.

    Tenta primeiro com ponto (.), depois com vírgula (,).

    Argumentos:
        caminho: Caminho do arquivo CSV.

    Retornos:
        DataFrame com os dados carregados.
    """
    # Tenta carregar com ponto como separador decimal (padrão)
    df = pd.read_csv(caminho)

    # Verifica se há colunas numéricas que podem estar como string
    for col in df.columns:
        if df[col].dtype == 'object' and col != 'isozona' and col != 'duracao':
            # Tenta converter substituindo vírgula por ponto
            try:
                df[col] = df[col].str.replace(',', '.').astype(float)
            except (ValueError, AttributeError):
                pass

    return df


def carregar_dados(zona: str) -> pd.DataFrame:
    """
    Carrega os dados dos CSVs e filtra pela zona especificada.

    Combina os dados de precipitação e coeficientes em um único DataFrame.

    Argumentos:
        zona: Nome da isozona para filtrar os dados.

    Retornos:
        DataFrame filtrado com os dados da zona (precipitação + coeficientes).

    Exceções:
        ValueError: Se a zona não for encontrada ou arquivo inválido.
    """
    # Carrega os dois CSVs com detecção automática de separador decimal
    df_precip = carregar_csv_com_decimal(CSV_PRECIPITACAO)
    df_coef = carregar_csv_com_decimal(CSV_COEFICIENTES)

    # Valida o arquivo de precipitação
    if not validar_csv_precipitacao(df_precip):
        raise ValueError(
            "Verifique se o arquivo isozonas_precipitacao.csv "
            "esta de acordo com o descrito."
        )

    # Filtra pela zona
    zona_upper = zona.strip().upper()
    df_precip_zona = df_precip[
        df_precip['isozona'].str.strip().str.upper() == zona_upper
    ]
    df_coef_zona = df_coef[
        df_coef['isozona'].str.strip().str.upper() == zona_upper
    ]

    if df_precip_zona.empty:
        zonas_disponiveis = df_precip['isozona'].unique()
        raise ValueError(
            f"Zona '{zona}' não encontrada. "
            f"Zonas disponíveis: {list(zonas_disponiveis)}"
        )

    # Combina precipitação com coeficientes por tempo de retorno
    df_zona = df_precip_zona.merge(
        df_coef_zona[['tempo_retorno', 'coef_1h_24h', 'coef_6min_24h']],
        on='tempo_retorno',
        how='left'
    )

    return df_zona


def calcular_precipitacao_base(df_zona: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula os valores base de precipitação para 24h, 1h e 6min.

    Argumentos:
        df_zona: DataFrame com os dados da zona.

    Retornos:
        DataFrame com as colunas de precipitação calculadas.
    """
    resultado = df_zona.copy()
    resultado['precip_24h'] = resultado['precipitacao'] * 1.14
    resultado['precip_1h'] = (
        resultado['precip_24h'] * resultado['coef_1h_24h']
    ) / 100
    resultado['precip_6min'] = (
        resultado['precip_24h'] * resultado['coef_6min_24h']
    ) / 100
    return resultado


def calcular_coeficientes_log(
    x1: float, y1: float, x2: float, y2: float
) -> tuple:
    """
    Calcula coeficientes a e b da equação y = a·ln(x) + b.

    Argumentos:
        x1: Primeiro valor de x.
        y1: Primeiro valor de y.
        x2: Segundo valor de x.
        y2: Segundo valor de y.

    Retornos:
        Tupla (a, b) com os coeficientes angular e linear.
    """
    ln_x1 = np.log(x1)  # ln(x1)
    ln_x2 = np.log(x2)  # ln(x2)
    a = (y2 - y1) / (ln_x2 - ln_x1)  # coeficiente angular
    b = y1 - a * ln_x1  # coeficiente linear
    return a, b


def interpolar_precipitacao(
    duracao_h: float, p_6min: float, p_1h: float, p_24h: float
) -> float:
    """
    Interpola precipitação para uma duração específica.

    Utiliza equações logarítmicas:
    - Equação 1: 6min (0.1h) até 1h
    - Equação 2: 1h até 24h

    Argumentos:
        duracao_h: Duração em horas.
        p_6min: Precipitação para 6 minutos.
        p_1h: Precipitação para 1 hora.
        p_24h: Precipitação para 24 horas.

    Retornos:
        Valor interpolado de precipitação.
    """
    if duracao_h < 1:
        # Equação 1: 6min (0.1h) até 1h
        a, b = calcular_coeficientes_log(0.1, p_6min, 1.0, p_1h)
    else:
        # Equação 2: 1h até 24h
        a, b = calcular_coeficientes_log(1.0, p_1h, 24.0, p_24h)

    return a * np.log(duracao_h) + b


def formatar_duracao(duracao_h: float) -> str:
    """
    Formata a duração para exibição.

    Argumentos:
        duracao_h: Duração em horas.

    Retornos:
        String formatada (ex: "6 min" ou "1 h").
    """
    if duracao_h < 1:
        minutos = int(duracao_h * 60)
        return f"{minutos} min"
    else:
        return f"{int(duracao_h)} h"


def gerar_tabela(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Gera tabela com precipitações interpoladas para todas as durações.

    Argumentos:
        df_base: DataFrame com precipitações base calculadas.

    Retornos:
        DataFrame com a tabela de precipitações interpoladas.
    """
    tabela = []

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


def exibir_tabela(
    df_tabela: pd.DataFrame, zona: str, lat: float, lon: float
) -> None:
    """
    Exibe a tabela de precipitações interpoladas.

    Argumentos:
        df_tabela: DataFrame com a tabela de precipitações.
        zona: Nome da isozona.
        lat: Latitude da coordenada.
        lon: Longitude da coordenada.
    """
    separador = "=" * 100
    print(separador)
    print("TABELA DE PRECIPITAÇÃO (mm)")
    print(f"Coordenadas: ({lat}, {lon}) - Zona: {zona.upper()}")
    print(separador)

    # Cabeçalho
    colunas = df_tabela.columns.tolist()
    header = f"{'Duração':<10}"
    for col in colunas[1:]:
        header += f"{col:>12}"
    print(header)
    print("-" * 100)

    # Dados
    for _, row in df_tabela.iterrows():
        linha = f"{row['Duração']:<10}"
        for col in colunas[1:]:
            linha += f"{row[col]:>12.2f}"
        print(linha)

    print(separador)


def main() -> None:
    """
    Função principal, Inicia a execução do programa.
    
    Exceções:
        ValueError: Se a zona não for encontrada ou arquivo inválido.
    """
    # Input de latitude e longitude
    try:
        latitude = float(input("Digite a latitude: "))
        longitude = float(input("Digite a longitude: "))
    except ValueError:
        print("Erro: Valores inválidos para latitude/longitude.")
        return

    # Identifica a zona pela coordenada
    zona = get_isozona(latitude, longitude)

    if zona is None:
        print(
            f"\nErro: Coordenada ({latitude}, {longitude}) "
            "está fora das isozonas."
        )
        return

    print(f"\nZona identificada: {zona}")

    try:
        # Carregar dados da zona
        df_zona = carregar_dados(zona)

        # Calcular precipitações base
        df_base = calcular_precipitacao_base(df_zona)

        # Gera tabela com precipitações interpoladas
        df_tabela = gerar_tabela(df_base)
        print()
        exibir_tabela(df_tabela, zona, latitude, longitude)

        # Pergunta se deseja salvar como CSV
        print()
        salvar = input("Deseja salvar a tabela como CSV? (s/n): ").strip().lower()
        if salvar in ('s', 'sim', 'y', 'yes'):
            caminho_saida = rf"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Data\precipitacao_zona_{zona.upper()}.csv"
            df_tabela.to_csv(caminho_saida, index=False, sep=';', decimal='.')
            print(f"\nArquivo salvo em: {caminho_saida}")

    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e}")
    except ValueError as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()
