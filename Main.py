"""
Cálculo de Precipitação e Distribuição Temporal

Combina os módulos:
    - Cálculo de Precipitação por Isozonas
    - Distribuição Temporal - Método Huff
"""

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point


# =============================================================================
# CONFIGURAÇÃO DE CAMINHOS
# =============================================================================
CSV_COEFICIENTES = (
    r"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Data\isozonas_coeficientes.csv"
)
CSV_PRECIPITACAO = (
    r"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Data\precipitacao-teste.csv"
)
SHAPEFILE_PATH = (
    r"C:\Users\joser\projects\Codes\Python"
    r"\Trabalho Qgis Areas\Isozonas_GrausDecimais (1)\Isozonas_GrausDecimais.shp"
)
CSV_HUFF_ENTRADA = r"Data/precipitacao_zona_A.csv"
CSV_HUFF_SAIDA = r"Data/precipitacao_huff_saida.csv"
# =============================================================================
"""
O CSV de precipitação deve conter apenas 2 colunas:
    tempo_retorno, precipitacao
A isozona detectada pelas coordenadas será usada
apenas para selecionar os coeficientes corretos.
"""
# Colunas esperadas
COLUNAS_PRECIPITACAO = ['tempo_retorno', 'precipitacao']
COLUNAS_COEFICIENTES = ['isozona', 'coef_1h_24h', 'coef_6min_24h']

# Durações em horas (6 min até 24h)
DURACOES_HORAS = [
    6/60, 10/60, 15/60, 20/60, 25/60, 30/60,
    1, 2, 3, 4, 6, 8, 10, 12, 18, 24
]

# =============================================================================
# Cálculo de Precipitação por Isozonas
# =============================================================================

def get_isozona(lat: float, lon: float) -> str | None:
    """
    Carrega o shapefile e retorna a zona correspondente à coordenada.
    Shapefile = arquivo que contém informações geográficas.

    Argumentos:
        lat: Latitude da coordenada em graus decimais.
        lon: Longitude da coordenada em graus decimais.

    Retornos:
        Nome da zona ou None se a coordenada estiver fora das isozonas.
    """
    gdf = gpd.read_file(SHAPEFILE_PATH)
    ponto = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
    ponto = ponto.to_crs(gdf.crs).iloc[0]
    
    for _, row in gdf.iterrows():
        if row.geometry.contains(ponto):
            return row['ZONA']
    return None


def validar_csv_precipitacao(df: pd.DataFrame) -> bool:
    """
    Valida se o DataFrame de precipitação tem as colunas corretas.
    DataFrame = estrutura bidimensional de dados (tabela).

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
    df = pd.read_csv(caminho)
    for col in df.columns:
        if df[col].dtype == 'object' and col != 'isozona':
            try:
                df[col] = df[col].str.replace(',', '.').astype(float)
            except (ValueError, AttributeError):
                pass
    return df


def carregar_dados(zona: str) -> pd.DataFrame:
    """
    Carrega o CSV de precipitação e combina
    com os coeficientes da isozona detectada.

    O CSV de precipitação contém apenas tempo_retorno e
    precipitacao. A isozona é usada somente para buscar
    os coeficientes no CSV de coeficientes.

    Argumentos:
        zona: Nome da isozona para buscar coeficientes.

    Retornos:
        DataFrame com precipitação + coeficientes da zona.

    Exceções:
        ValueError: Se a zona não for encontrada.
    """
    df_precip = carregar_csv_com_decimal(CSV_PRECIPITACAO)
    df_coef = carregar_csv_com_decimal(CSV_COEFICIENTES)

    if not validar_csv_precipitacao(df_precip):
        raise ValueError(
            "CSV de precipitação inválido. "
            "Colunas esperadas: tempo_retorno, precipitacao"
        )

    zona_upper = zona.strip().upper()
    df_coef_zona = df_coef[
        df_coef['isozona'].str.strip().str.upper() == zona_upper
    ]

    if df_coef_zona.empty:
        zonas_disponiveis = df_coef['isozona'].unique()
        raise ValueError(
            f"Zona '{zona}' não encontrada. "
            f"Zonas: {list(zonas_disponiveis)}"
        )

    df_zona = df_precip.merge(
        df_coef_zona[[
            'tempo_retorno', 'coef_1h_24h', 'coef_6min_24h'
        ]],
        on='tempo_retorno', how='left'
    )
    return df_zona


def calcular_precipitacao_base(df_zona: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula os valores base de precipitação para 24h, 1h e 6min.
    Guarda os valores em uma tabela interna.

    Argumentos:
        df_zona: DataFrame com os dados da zona.

    Retornos:
        DataFrame com as colunas de precipitação calculadas.
    """
    resultado = df_zona.copy()
    resultado['precip_24h'] = resultado['precipitacao'] * 1.14
    resultado['precip_1h'] = (resultado['precip_24h'] * resultado['coef_1h_24h']) / 100
    resultado['precip_6min'] = (resultado['precip_24h'] * resultado['coef_6min_24h']) / 100
    return resultado


def calcular_coeficientes_log(x1: float, y1: float, x2: float, y2: float) -> tuple:
    """
    Calcula coeficientes a e b da equação y = a·ln(x) + b.
    Equacao utilizada para achar qualquer valor de precipitação entre 6min e 24h.

    Argumentos:
        x1: Primeiro valor de x.
        y1: Primeiro valor de y.
        x2: Segundo valor de x.
        y2: Segundo valor de y.

    Retornos:
        Tupla (a, b) com os coeficientes angular e linear.
    """
    ln_x1, ln_x2 = np.log(x1), np.log(x2)
    a = (y2 - y1) / (ln_x2 - ln_x1)
    b = y1 - a * ln_x1
    return a, b


def interpolar_precipitacao(duracao_h: float, p_6min: float, p_1h: float, p_24h: float) -> float:
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
        a, b = calcular_coeficientes_log(0.1, p_6min, 1.0, p_1h)
    else:
        a, b = calcular_coeficientes_log(1.0, p_1h, 24.0, p_24h)
    return a * np.log(duracao_h) + b


def formatar_duracao(duracao_h: float) -> str:
    """
    Formata a duração para exibição.
    Transforma os valores de horas para minutos se for menor que 1 hora.

    Argumentos:
        duracao_h: Duração em horas.

    Retornos:
        String formatada (ex: "6 min" ou "1 h").
    """
    if duracao_h < 1:
        return f"{int(duracao_h * 60)} min"
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
                duracao, row['precip_6min'], row['precip_1h'], row['precip_24h']
            )
            linha[f'TR {tr}'] = precip
        tabela.append(linha)
    return pd.DataFrame(tabela)


def exibir_tabela(df_tabela: pd.DataFrame, zona: str, lat: float, lon: float) -> None:
    """
    Exibe a tabela de precipitações interpoladas.

    Argumentos:
        df_tabela: DataFrame com a tabela de precipitações.
        zona: Nome da isozona.
        lat: Latitude da coordenada.
        lon: Longitude da coordenada.
    """
    separador = "=" * 142
    print(separador)
    print("TABELA DE PRECIPITAÇÃO (mm)")
    print(f"Coordenadas: ({lat}, {lon}) - Zona: {zona.upper()}")
    print(separador)

    colunas = df_tabela.columns.tolist()
    header = f"{'Duração':<10}"
    for col in colunas[1:]:
        header += f"{col:>12}"
    print(header)
    print("-" * 142)

    for _, row in df_tabela.iterrows():
        linha = f"{row['Duração']:<10}"
        for col in colunas[1:]:
            linha += f"{row[col]:>12.2f}"
        print(linha)
    print(separador)


def executar_Precipitação_por_Isozonas(
    salvar_automatico: bool = False, caminho_saida: str = None
) -> str | None:
    """
    Executa o Cálculo de Precipitação por Isozonas.
    
    Argumentos:
        salvar_automatico: Se True, salva o CSV sem perguntar.
        caminho_saida: Caminho opcional para salvar o arquivo.

    Retornos:
        Caminho do arquivo CSV salvo (se salvo) ou None.
    """
    print("\n" + "=" * 70)
    print("   CÁLCULO DE PRECIPITAÇÃO POR ISOZONAS")
    print("=" * 70)
    
    try:
        latitude = float(input("\nDigite a latitude: "))
        longitude = float(input("Digite a longitude: "))
    except ValueError:
        print("Erro: Valores inválidos para latitude/longitude.")
        return None

    zona = get_isozona(latitude, longitude)
    if zona is None:
        print(f"\nErro: Coordenada ({latitude}, {longitude}) está fora das isozonas.")
        return None

    print(f"\nZona identificada: {zona}")

    try:
        df_zona = carregar_dados(zona)
        df_base = calcular_precipitacao_base(df_zona)
        df_tabela = gerar_tabela(df_base)
        print()
        exibir_tabela(df_tabela, zona, latitude, longitude)

        if caminho_saida is None:
            caminho_saida = (
                rf"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas"
                rf"\Data\precipitacao_zona_{zona.upper()}.csv"
            )

        if salvar_automatico:
            df_tabela.to_csv(caminho_saida, index=False, sep=';', decimal='.')
            print(f"\nArquivo salvo em: {caminho_saida}")
            return caminho_saida
        else:
            print()
            salvar = input("Deseja salvar a tabela como CSV? (s/n): ").strip().lower()
            if salvar in ('s', 'sim', 'y', 'yes'):
                df_tabela.to_csv(caminho_saida, index=False, sep=';', decimal='.')
                print(f"\nArquivo salvo em: {caminho_saida}")
                return caminho_saida

    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e}")
    except ValueError as e:
        print(f"Erro: {e}")
    
    return None


# =============================================================================
# Distribuição Temporal - Método Huff
# =============================================================================

def calcular_pac_huff(pb: float, duracao_horas: float) -> float:
    """
    Calcula a porcentagem acumulada de precipitação mm/min usando as curvas de Huff.
    
    Parâmetros:
        pb: Porcentagem do tempo decorrido (0 a 100)
        duracao_horas: Duração total da chuva em horas
        
    Retorna:
        PAc: Porcentagem acumulada da precipitação (0 a 100)
    """
    if pb <= 0:
        return 0.0
    if pb >= 100:
        return 100.0
    #valores referentes aos cálculos matemáticos de cada quartil de huff.
    if duracao_horas <= 6:
        pac = (4.02817498644692E-26 * pb**17 - 3.52064227661328E-23 * pb**16 +
               1.40597068416381E-20 * pb**15 - 3.39749477703355E-18 * pb**14 +
               5.54497997392431E-16 * pb**13 - 6.45955102401168E-14 * pb**12 +
               5.53311153502673E-12 * pb**11 - 3.53601335024796E-10 * pb**10 +
               1.69157185342832E-08 * pb**9 - 6.01477294241886E-07 * pb**8 +
               1.55857516691692E-05 * pb**7 - 2.82804931812996E-04 * pb**6 +
               3.30423804127657E-03 * pb**5 - 1.95440226611134E-02 * pb**4 -
               1.78285694295392E-02 * pb**3 + 0.843704743033219 * pb**2 +
               0.460519860597484 * pb + 0.105509396306812)
    elif duracao_horas <= 12:
        pac = (1.38673921100494E-29 * pb**19 - 1.21613849024923E-26 * pb**18 +
               4.81175587207619E-24 * pb**17 - 1.13061048055895E-21 * pb**16 +
               1.74322289744585E-19 * pb**15 - 1.82955175694565E-17 * pb**14 +
               1.29362605433794E-15 * pb**13 - 5.57716800214043E-14 * pb**12 +
               7.05502076331805E-13 * pb**11 + 8.26435609777427E-11 * pb**10 -
               6.63085914357193E-09 * pb**9 + 2.63606231276545E-07 * pb**8 -
               6.63478625779216E-06 * pb**7 + 1.10122543439505E-04 * pb**6 -
               1.19013879689829E-03 * pb**5 + 8.05401322603745E-03 * pb**4 -
               3.34138101445273E-02 * pb**3 + 0.107328692602926 * pb**2 +
               0.434452891319131 * pb - 9.29064257700887E-03)
    elif duracao_horas <= 24:
        if pb <= 56:
            pac = (-7.60644888142597E-19 * pb**13 + 2.26532324896959E-16 * pb**12 -
                   2.77322200030732E-14 * pb**11 + 1.74614948354883E-12 * pb**10 -
                   5.42723072107129E-11 * pb**9 + 2.88453725150229E-10 * pb**8 +
                   3.40120100322963E-08 * pb**7 - 9.87326768780573E-07 * pb**6 +
                   4.6775676050966E-06 * pb**5 + 2.53896092445158E-04 * pb**4 -
                   5.65737144328779E-03 * pb**3 + 5.39029497668964E-02 * pb**2 +
                   0.359808518609887 * pb - 5.32553512302088E-12)
        else:
            pac = (7.93878771768824E-11 * pb**8 - 5.24871539129577E-08 * pb**7 +
                   1.51310191157137E-05 * pb**6 - 2.48406960877551E-03 * pb**5 +
                   0.25398132631186 * pb**4 - 16.5564133934408 * pb**3 +
                   671.654540274205 * pb**2 - 15489.8757952666 * pb + 155336.538705823)
    else:
        if pb < 78:
            pac = (4.45646156443285E-20 * pb**13 - 2.22681580593717E-17 * pb**12 +
                   4.96794969032244E-15 * pb**11 - 6.5250621619299E-13 * pb**10 +
                   5.59641539762932E-11 * pb**9 - 3.28222385169418E-09 * pb**8 +
                   1.33763527344691E-07 * pb**7 - 3.76248289158519E-06 * pb**6 +
                   7.06366898909776E-05 * pb**5 - 8.12975145227206E-04 * pb**4 +
                   4.3426645265125E-03 * pb**3 + 1.05914948857879E-02 * pb**2 +
                   0.30574957410383 * pb + 2.4217656685223E-04)
        else:
            pac = (4.81964349956249E-10 * pb**8 - 2.71720789296904E-07 * pb**7 +
                   6.08665963510088E-05 * pb**6 - 0.006357548911514 * pb**5 +
                   0.185523370306902 * pb**4 + 25.3341694344528 * pb**3 -
                   2889.70554544436 * pb**2 + 119076.774334982 * pb - 1835700.24767339)
    
    return max(0.0, min(100.0, pac))


def formatar_nome_coluna(tempo_retorno: int, duracao_horas: float) -> str:
    """
    Formata o nome da coluna no padrao TR,duracao.
    
    Exemplos:
        100 anos, 0.167h -> "100,10min"
        100 anos, 1h -> "100,1h"
        1000 anos, 24h -> "1000,24h"
    """
    duracao_minutos = int(round(duracao_horas * 60))
    if duracao_minutos < 60:
        return f"{tempo_retorno},{duracao_minutos}min"
    return f"{tempo_retorno},{duracao_minutos // 60}h"


def distribuir_chuva_huff(precipitacao_mm: float, duracao_horas: float) -> np.ndarray:
    """
    Distribui a precipitação total ao longo do tempo usando o Método de Huff.
    Calcula o volume de chuva em mm minuto a minuto utilizando os quartis de Huff.
    Para encontrar o valor de cada minuto, subtrai o volume atual - 1 minuto antes.

    Argumentos:
        precipitacao_mm: Precipitação total em mm (ex: 100)
        duracao_horas: Duração da chuva em horas (ex: 2)

    Retorna:
        Array de intensidades em mm/min (1 valor por minuto)
    
    Exemplo:
        - Minuto 1:  pb=0.83%  → PAc=0.5%  → acum=0.5mm  → intensidade=0.5mm
        - Minuto 2:  pb=1.67%  → PAc=1.2%  → acum=1.2mm  → intensidade=0.7mm (1.2-0.5)
        - Minuto 3:  pb=2.50%  → PAc=2.0%  → acum=2.0mm  → intensidade=0.8mm (2.0-1.2)
        - Minuto 4:  pb=3.33%  → PAc=2.9%  → acum=2.9mm  → intensidade=0.9mm (2.9-2.0)
        - Minuto 60: pb=50%    → PAc=70%   → acum=70mm   → intensidade=2.0mm (pico)
        - Minuto 120: pb=100%  → PAc=100%  → acum=100mm  → intensidade=0.3mm
    """
    duracao_minutos = int(round(duracao_horas * 60))
    intensidades = []
    p_acum_anterior = 0.0
    
    for i in range(1, duracao_minutos + 1):
        pb = (i / duracao_minutos) * 100
        pac = calcular_pac_huff(pb, duracao_horas)
        p_acum = precipitacao_mm * pac / 100
        intensidades.append(p_acum - p_acum_anterior)
        p_acum_anterior = p_acum
    
    return np.array(intensidades)


def converter_csv_para_huff(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte o formato de saída do Cálculo de Precipitação para o formato Huff.
    
    Formato de entrada (Cálculo de Precipitação por Isozonas):
        Duração;TR 2;TR 5;TR 10;...
        6 min;12,34;15,67;18,90;...
        
    Formato de saída (Huff):
        tempo_retorno,duracao_horas,precipitacao_mm
        2,0.1,12.34
    """
    dados = []
    col_duracao = next((col for col in df.columns if 'dura' in col.lower()), None)
    
    if col_duracao is None:
        raise ValueError("Coluna 'Duração' não encontrada no CSV")
    
    for _, row in df.iterrows():
        duracao_str = str(row[col_duracao]).strip()
        if 'min' in duracao_str:
            duracao_horas = int(duracao_str.replace('min', '').strip()) / 60
        elif 'h' in duracao_str:
            duracao_horas = float(duracao_str.replace('h', '').strip())
        else:
            continue
        
        for col in df.columns:
            if col == col_duracao:
                continue
            tr_str = col.replace('TR', '').strip()
            try:
                tempo_retorno = int(tr_str)
            except ValueError:
                continue
            
            precip = row[col]
            if pd.isna(precip) or precip == '':
                continue
            if isinstance(precip, str):
                precip = float(precip.replace(',', '.'))
            
            dados.append({
                'tempo_retorno': tempo_retorno,
                'duracao_horas': duracao_horas,
                'precipitacao_mm': precip
            })
    
    return pd.DataFrame(dados)


def processar_csv_huff(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    """
    Lê o CSV de entrada e gera o DataFrame de saída com distribuição Huff.
    
    Formato de entrada esperado (saída do Cálculo de Precipitação por Isozonas):
        Duração;TR 2;TR 5;TR 10;...
        6 min;12,34;15,67;18,90;...
    
    Parâmetros:
        caminho_entrada: Caminho do CSV de entrada
        caminho_saida: Caminho opcional para salvar o resultado em CSV
        
    Retorna:
        DataFrame com colunas para cada combinação TR/duração
    """
    df_entrada = pd.read_csv(caminho_entrada, sep=';', decimal='.')
    df_entrada = converter_csv_para_huff(df_entrada)
    
    max_minutos = int(round(df_entrada['duracao_horas'].max() * 60))
    resultado = {'minuto': list(range(1, max_minutos + 1))}
    
    for _, row in df_entrada.iterrows():
        nome_coluna = formatar_nome_coluna(int(row['tempo_retorno']), row['duracao_horas'])
        intensidades = distribuir_chuva_huff(row['precipitacao_mm'], row['duracao_horas'])
        intensidades_completas = np.zeros(max_minutos)
        intensidades_completas[:len(intensidades)] = intensidades
        resultado[nome_coluna] = intensidades_completas
    
    df_saida = pd.DataFrame(resultado)
    
    def ordenar_coluna(col):
        if col == 'minuto':
            return (0, 0)
        partes = col.split(',')
        tr = int(partes[0])
        dur = partes[1]
        minutos = int(dur.replace('min', '')) if 'min' in dur else int(dur.replace('h', '')) * 60
        return (tr, minutos)
    
    df_saida = df_saida[sorted(df_saida.columns, key=ordenar_coluna)]
    
    if caminho_saida:
        df_saida.round(4).to_csv(caminho_saida, index=False, sep=';', decimal='.')
    
    return df_saida


def exibir_resumo_huff(df: pd.DataFrame):
    """Exibe resumo dos resultados Huff no console."""
    colunas = [c for c in df.columns if c != 'minuto']
    print(f"\nTotal de cenários processados: {len(colunas)}")
    print(f"Total de linhas (minutos): {len(df)}")
    print("\nColunas geradas:")
    for i, col in enumerate(colunas, 1):
        print(f"   {i:2d}. {col:<20} | Pmax = {df[col].sum():.2f} mm")
    print("\n" + "=" * 70)


def executar_Distribuição_Temporal(caminho_entrada: str = None) -> None:
    """Executa a Distribuição Temporal - Método Huff."""
    print("\n" + "=" * 70)
    print("   DISTRIBUIÇÃO TEMPORAL - MÉTODO HUFF")
    print("=" * 70)
    
    if caminho_entrada is None:
        caminho_entrada = CSV_HUFF_ENTRADA
    
    try:
        df = processar_csv_huff(caminho_entrada, CSV_HUFF_SAIDA)
        exibir_resumo_huff(df)
        print(f"\nArquivo salvo em: {CSV_HUFF_SAIDA}")
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {caminho_entrada}")
    except Exception as e:
        print(f"ERRO: Erro ao processar: {e}")


# =============================================================================
# MENU PRINCIPAL
# =============================================================================

def exibir_menu():
    """Exibe o menu principal."""
    print("\n" + "=" * 70)
    print("   SISTEMA DE CÁLCULO DE PRECIPITAÇÃO + DISTRIBUIÇÃO TEMPORAL")
    print("=" * 70)
    print("\n   Opções:")
    print("   [1] Cálculo de Precipitação por Isozonas")
    print("   [2] Distribuição Temporal - Método Huff")
    print("   [3] Executar os dois (Encadeado)")
    print("   [0] Sair")
    print("\n" + "-" * 70)


def main():
    """Função principal."""
    while True:
        exibir_menu()
        
        try:
            opcao = input("   Digite sua opção: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSaindo...")
            break
        
        if opcao == '1':
            executar_Precipitação_por_Isozonas()
        elif opcao == '2':
            executar_Distribuição_Temporal()
        elif opcao == '3':
            print("\n>>> Executando Precipitação + Distribuição (Encadeado) <<<")
            caminho_csv = executar_Precipitação_por_Isozonas(salvar_automatico=True)
            if caminho_csv:
                print("\n>>> Iniciando Distribuição Temporal com o arquivo gerado <<<")
                executar_Distribuição_Temporal(caminho_entrada=caminho_csv)
            else:
                print("\nDistribuição Temporal não foi executada pois não há arquivo de entrada.")
        elif opcao == '0':
            print("\nSaindo...")
            break
        else:
            print("\nOpção inválida. Tente novamente.")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    main()
