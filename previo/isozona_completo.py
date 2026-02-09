import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from tkinter import filedialog
from matplotlib.patches import Patch

# Abre janela para selecionar o arquivo .shp
Caminho = filedialog.askopenfilename(
    title="Selecione o arquivo Shapefile",
    filetypes=[("Shapefile", "*.shp")]
)

# Cores para cada isozona
CORES = {
    'A': '#00FFFF', 'B': '#FFA500', 'C': '#006400', 'D': '#FFFF00',
    'E': '#0000FF', 'F': '#00FF00', 'G': '#FF00FF', 'H': '#FF0000',
}


def get_isozona(gdf, lat, lon):
    """Identifica a isozona para uma coordenada."""
    ponto = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(gdf.crs).iloc[0]
    for _, row in gdf.iterrows():
        if row.geometry.contains(ponto):
            return row.drop('geometry').to_dict()
    return None


def visualizar_mapa(gdf, lat, lon, zona_nome):
    """Exibe o mapa com a coordenada marcada."""
    gdf_plot = gdf.to_crs("EPSG:4326")
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    for zona, cor in CORES.items():
        subset = gdf_plot[gdf_plot['ZONA'] == zona]
        if not subset.empty:
            subset.plot(ax=ax, color=cor, edgecolor='black', linewidth=0.5, alpha=0.8)
    
    # Marca a coordenada no mapa
    ax.plot(lon, lat, 'ko', markersize=10, label=f'Coordenada ({lat}, {lon})')
    ax.plot(lon, lat, 'w+', markersize=8)
    
    patches = [Patch(facecolor=cor, edgecolor='black', label=f'Isozona {z}') 
               for z, cor in CORES.items() if z in gdf_plot['ZONA'].values]
    patches.append(Patch(facecolor='black', edgecolor='black', label=f'Coordenada ({lat}, {lon})'))
    
    ax.set_title(f'Isozonas de Taborga - Coordenada na Zona {zona_nome}', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.legend(handles=patches, loc='lower left', fontsize=10, title='Legenda')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    if not Caminho:
        print("Nenhum arquivo selecionado.")
    else:
        gdf = gpd.read_file(Caminho)
        
        latitude = float(input("Digite a latitude: "))
        longitude = float(input("Digite a longitude: "))
        
        zona = get_isozona(gdf, latitude, longitude)
        
        if zona:
            print(f"\nCoordenada: ({latitude}, {longitude})")
            print(f"Isozona: {zona['ZONA']}")
            print(f"Parâmetros:")
            for tempo in ['5', '10', '25', '50', '100']:
                if tempo in zona:
                    print(f"  TR {tempo} anos: {zona[tempo]}")
            
            visualizar_mapa(gdf, latitude, longitude, zona['ZONA'])
        else:
            print("Coordenada fora das isozonas.")
