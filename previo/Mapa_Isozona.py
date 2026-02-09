import geopandas as gpd
import matplotlib.pyplot as plt




# Cores para cada isozona
CORES = {
    'A': '#00FFFF',  # Ciano
    'B': '#FFA500',  # Laranja
    'C': '#006400',  # Verde escuro
    'D': '#FFFF00',  # Amarelo
    'E': '#0000FF',  # Azul
    'F': '#00FF00',  # Verde claro
    'G': '#FF00FF',  # Magenta
    'H': '#FF0000',  # Vermelho
}


def visualizar_isozonas():
    """Carrega o shapefile e exibe o mapa das isozonas."""
    
    # Carrega o shapefile e converte para WGS84 (graus)
    gdf = gpd.read_file(r"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Isozonas_GrausDecimais (1)\Isozonas_GrausDecimais.shp")
    gdf = gdf.to_crs("EPSG:4326")
    
    # Cria a figura
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plota cada zona com sua cor específica
    for zona, cor in CORES.items():
        subset = gdf[gdf['ZONA'] == zona]
        if not subset.empty:
            subset.plot(ax=ax, color=cor, edgecolor='black', linewidth=0.5, alpha=0.8)
    
    # Cria legenda colorida
    from matplotlib.patches import Patch
    patches = [Patch(facecolor=cor, edgecolor='black', label=f'Isozona {zona}') 
               for zona, cor in CORES.items() if zona in gdf['ZONA'].values]
    
    # Configurações do mapa, Titulos
    ax.set_title('Isozonas de Taborga - Brasil', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.legend(handles=patches, loc='lower left', fontsize=10, title='Legenda')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()

visualizar_isozonas()
