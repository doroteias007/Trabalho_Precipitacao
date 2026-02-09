import geopandas as gpd
from shapely.geometry import Point

#COLOQUE AQUI O CAMINHO DO SEU ARQUIVO.SHP
Caminho = "C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Isozonas_GrausDecimais (1)\Isozonas_GrausDecimais.shp"


def get_isozona(lat: float, lon: float) -> dict | None:
    """
    Identifica a Isozona Taborga para uma coordenada.
    
    Args:
        lat: Latitude (graus decimais, ex: -30.03)
        lon: Longitude (graus decimais, ex: -51.22)
    
    Returns:
        Dicionário com atributos da zona, ou None se não encontrada.
    """
    # Carrega o shapefile
    gdf = gpd.read_file(Caminho)
    
    # Cria o ponto em WGS84 e converte para o CRS do shapefile
    ponto = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
    ponto = ponto.to_crs(gdf.crs).iloc[0]
    
    # Busca a zona que contém o ponto
    for _, row in gdf.iterrows():
        if row.geometry.contains(ponto):
            resultado = row.drop('geometry').to_dict()
            return resultado
    
    return None


if __name__ == "__main__":
    latitude = float(input("Digite a latitude: "))
    longitude = float(input("Digite a longitude: "))
    
    zona = get_isozona(latitude, longitude)
    
    if zona:
        print(f"\nCoordenada: ({latitude}, {longitude})")
        print(f"Isozona: {zona['ZONA']}")
        print(f"Parâmetros:")
        for tempo in ['5', '10', '25', '50', '100']:
            if tempo in zona:
                print(f"  TR {tempo} anos: {zona[tempo]}")
    else:
        print("Coordenada fora das isozonas.")
