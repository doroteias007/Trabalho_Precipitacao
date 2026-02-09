"""
Distribuição Temporal de Chuvas - Método Huff

Lê um CSV com dados de precipitação e gera hietogramas com intensidade em mm/min.

Formato do CSV de entrada:
    tempo_retorno,duracao_horas,precipitacao_mm
    100,0.167,30.8
    100,0.25,39.9
    ...

Saída: DataFrame com colunas no formato "TR_min" ou "TR_h"
"""

import numpy as np
import pandas as pd


# =============================================================================
# CONFIGURACAO - Defina os caminhos dos arquivos aqui
# =============================================================================
CSV_PATH = r"Data/precipitacao_zona_A.csv"
CSV_SAIDA = r"Data/precipitacao_huff_saida.csv"
# =============================================================================


def calcular_pac_huff(pb: float, duracao_horas: float) -> float:
    """
    Calcula a porcentagem acumulada de precipitação usando as curvas de Huff.
    
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
    
    # 1º Quartil: Duração <= 6 horas (polinômio grau 17)
    if duracao_horas <= 6:
        pac = (4.02817498644692E-26 * pb**17 +
              -3.52064227661328E-23 * pb**16 +
               1.40597068416381E-20 * pb**15 +
              -3.39749477703355E-18 * pb**14 +
               5.54497997392431E-16 * pb**13 +
              -6.45955102401168E-14 * pb**12 +
               5.53311153502673E-12 * pb**11 +
              -3.53601335024796E-10 * pb**10 +
               1.69157185342832E-08 * pb**9 +
              -6.01477294241886E-07 * pb**8 +
               1.55857516691692E-05 * pb**7 +
              -2.82804931812996E-04 * pb**6 +
               3.30423804127657E-03 * pb**5 +
              -1.95440226611134E-02 * pb**4 +
              -1.78285694295392E-02 * pb**3 +
               0.843704743033219 * pb**2 +
               0.460519860597484 * pb +
               0.105509396306812)
    
    # 2º Quartil: 6h < Duração <= 12h (polinômio grau 19)
    elif duracao_horas <= 12:
        pac = (1.38673921100494E-29 * pb**19 +
              -1.21613849024923E-26 * pb**18 +
               4.81175587207619E-24 * pb**17 +
              -1.13061048055895E-21 * pb**16 +
               1.74322289744585E-19 * pb**15 +
              -1.82955175694565E-17 * pb**14 +
               1.29362605433794E-15 * pb**13 +
              -5.57716800214043E-14 * pb**12 +
               7.05502076331805E-13 * pb**11 +
               8.26435609777427E-11 * pb**10 +
              -6.63085914357193E-09 * pb**9 +
               2.63606231276545E-07 * pb**8 +
              -6.63478625779216E-06 * pb**7 +
               1.10122543439505E-04 * pb**6 +
              -1.19013879689829E-03 * pb**5 +
               8.05401322603745E-03 * pb**4 +
              -3.34138101445273E-02 * pb**3 +
               0.107328692602926 * pb**2 +
               0.434452891319131 * pb +
              -9.29064257700887E-03)
    
    # 3º Quartil: 12h < Duração <= 24h (dois polinômios)
    elif duracao_horas <= 24:
        if pb <= 56:
            pac = (-7.60644888142597E-19 * pb**13 +
                    2.26532324896959E-16 * pb**12 +
                   -2.77322200030732E-14 * pb**11 +
                    1.74614948354883E-12 * pb**10 +
                   -5.42723072107129E-11 * pb**9 +
                    2.88453725150229E-10 * pb**8 +
                    3.40120100322963E-08 * pb**7 +
                   -9.87326768780573E-07 * pb**6 +
                    4.6775676050966E-06 * pb**5 +
                    2.53896092445158E-04 * pb**4 +
                   -5.65737144328779E-03 * pb**3 +
                    5.39029497668964E-02 * pb**2 +
                    0.359808518609887 * pb +
                   -5.32553512302088E-12)
        else:
            pac = (7.93878771768824E-11 * pb**8 +
                  -5.24871539129577E-08 * pb**7 +
                   1.51310191157137E-05 * pb**6 +
                  -2.48406960877551E-03 * pb**5 +
                   0.25398132631186 * pb**4 +
                  -16.5564133934408 * pb**3 +
                   671.654540274205 * pb**2 +
                  -15489.8757952666 * pb +
                   155336.538705823)
    
    # 4º Quartil: Duração > 24h (dois polinômios)
    else:
        if pb < 78:
            pac = (4.45646156443285E-20 * pb**13 +
                  -2.22681580593717E-17 * pb**12 +
                   4.96794969032244E-15 * pb**11 +
                  -6.5250621619299E-13 * pb**10 +
                   5.59641539762932E-11 * pb**9 +
                  -3.28222385169418E-09 * pb**8 +
                   1.33763527344691E-07 * pb**7 +
                  -3.76248289158519E-06 * pb**6 +
                   7.06366898909776E-05 * pb**5 +
                  -8.12975145227206E-04 * pb**4 +
                   4.3426645265125E-03 * pb**3 +
                   1.05914948857879E-02 * pb**2 +
                   0.30574957410383 * pb +
                   2.4217656685223E-04)
        else:
            pac = (4.81964349956249E-10 * pb**8 +
                  -2.71720789296904E-07 * pb**7 +
                   6.08665963510088E-05 * pb**6 +
                  -0.006357548911514 * pb**5 +
                   0.185523370306902 * pb**4 +
                   25.3341694344528 * pb**3 +
                  -2889.70554544436 * pb**2 +
                   119076.774334982 * pb +
                  -1835700.24767339)
    
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
    else:
        horas = duracao_minutos // 60
        return f"{tempo_retorno},{horas}h"


def distribuir_chuva_huff(precipitacao_mm: float, duracao_horas: float) -> np.ndarray:
    """
    Distribui a precipitação total ao longo do tempo usando o Método de Huff.
    
    Retorna:
        Array de intensidades em mm/min (1 valor por minuto)
    """
    duracao_minutos = int(round(duracao_horas * 60))
    
    intensidades = []
    p_acum_anterior = 0.0
    
    for i in range(1, duracao_minutos + 1):
        pb = (i / duracao_minutos) * 100
        pac = calcular_pac_huff(pb, duracao_horas)
        p_acum = precipitacao_mm * pac / 100
        
        # Intensidade = precipitação do minuto / 1 min = mm/min
        intensidade = p_acum - p_acum_anterior
        intensidades.append(intensidade)
        
        p_acum_anterior = p_acum
    
    return np.array(intensidades)


def converter_csv_para_huff(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte o formato de saída do parte-1.py para o formato Huff.
    
    Formato de entrada (parte-1.py):
        Duração;TR 2;TR 5;TR 10;...
        6 min;12,34;15,67;18,90;...
        
    Formato de saída (Huff):
        tempo_retorno,duracao_horas,precipitacao_mm
        2,0.1,12.34
    """
    dados = []
    
    # Encontrar a coluna de duração (pode ter acentos ou não)
    col_duracao = None
    for col in df.columns:
        if 'dura' in col.lower():
            col_duracao = col
            break
    
    if col_duracao is None:
        raise ValueError("Coluna 'Duração' não encontrada no CSV")
    
    for _, row in df.iterrows():
        duracao_str = str(row[col_duracao]).strip()
        
        # Converter duração para horas
        if 'min' in duracao_str:
            minutos = int(duracao_str.replace('min', '').strip())
            duracao_horas = minutos / 60
        elif 'h' in duracao_str:
            horas = int(duracao_str.replace('h', '').strip())
            duracao_horas = float(horas)
        else:
            continue
        
        # Processar cada coluna TR
        for col in df.columns:
            if col == col_duracao:
                continue
            
            # Extrair tempo de retorno do nome da coluna (ex: "TR 100" -> 100)
            tr_str = col.replace('TR', '').strip()
            try:
                tempo_retorno = int(tr_str)
            except ValueError:
                continue
            
            # Obter precipitação (ignorar valores vazios)
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


def processar_csv(caminho_entrada: str, caminho_saida: str = None) -> pd.DataFrame:
    """
    Lê o CSV de entrada no formato parte-1.py e gera o DataFrame de saída.
    
    Formato de entrada esperado (saída do parte-1.py):
        Duração;TR 2;TR 5;TR 10;...
        6 min;12,34;15,67;18,90;...
    
    Parâmetros:
        caminho_entrada: Caminho do CSV de entrada (formato parte-1.py)
        caminho_saida: Caminho opcional para salvar o resultado em CSV
        
    Retorna:
        DataFrame com colunas para cada combinação TR/duração
    """
    # Ler CSV no formato parte-1.py (separador ; e decimal ,)
    df_entrada = pd.read_csv(caminho_entrada, sep=';', decimal='.')
    
    # Converter para formato interno (a função já ignora valores vazios)
    df_entrada = converter_csv_para_huff(df_entrada)
    
    # Determinar número máximo de minutos (maior duração)
    max_duracao_horas = df_entrada['duracao_horas'].max()
    max_minutos = int(round(max_duracao_horas * 60))
    
    # Criar DataFrame de saída
    resultado = {'minuto': list(range(1, max_minutos + 1))}
    
    # Processar cada linha do CSV
    for _, row in df_entrada.iterrows():
        tr = int(row['tempo_retorno'])
        duracao = row['duracao_horas']
        precip = row['precipitacao_mm']
        
        # Gerar nome da coluna
        nome_coluna = formatar_nome_coluna(tr, duracao)
        
        # Calcular intensidades
        intensidades = distribuir_chuva_huff(precip, duracao)
        
        # Preencher com zeros para completar até max_minutos
        intensidades_completas = np.zeros(max_minutos)
        intensidades_completas[:len(intensidades)] = intensidades
        
        resultado[nome_coluna] = intensidades_completas
    
    df_saida = pd.DataFrame(resultado)
    
    # Ordenar colunas: primeiro por TR, depois por duração
    def ordenar_coluna(col):
        if col == 'minuto':
            return (0, 0)  # minuto sempre primeiro
        
        partes = col.split(',')
        tr = int(partes[0])
        duracao_str = partes[1]
        
        # Converter duração para minutos para ordenação
        if 'min' in duracao_str:
            minutos = int(duracao_str.replace('min', ''))
        else:
            horas = int(duracao_str.replace('h', ''))
            minutos = horas * 60
        
        return (tr, minutos)
    
    colunas_ordenadas = sorted(df_saida.columns, key=ordenar_coluna)
    df_saida = df_saida[colunas_ordenadas]
    
    # Salvar se caminho especificado
    if caminho_saida:
        # Arredondar para 4 casas decimais e usar separador ponto-e-virgula para Excel
        df_saida.round(4).to_csv(caminho_saida, index=False, sep=';', decimal='.')
    
    return df_saida


def exibir_resumo(df: pd.DataFrame):
    """Exibe resumo dos resultados no console."""
    print("\n" + "="*70)
    print("   DISTRIBUICAO TEMPORAL DE CHUVAS - METODO HUFF")
    print("="*70)
    
    # Colunas (excluindo 'minuto')
    colunas = [c for c in df.columns if c != 'minuto']
    print(f"\nTotal de cenarios processados: {len(colunas)}")
    print(f"Total de linhas (minutos): {len(df)}")
    
    print("\nColunas geradas:")
    for i, col in enumerate(colunas, 1):
        intensidade_max = df[col].max()
        print(f"   {i:2d}. {col:<20} | Imax = {intensidade_max:.4f} mm/min")
    
    print("\n" + "="*70)


def main():
    """Funcao principal."""
    try:
        df = processar_csv(CSV_PATH, CSV_SAIDA)
        exibir_resumo(df)
    except FileNotFoundError:
        print(f"ERRO: Arquivo nao encontrado: {CSV_PATH}")
    except Exception as e:
        print(f"ERRO: Erro ao processar: {e}")


if __name__ == "__main__":
    main()

