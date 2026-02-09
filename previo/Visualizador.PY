# visualizar_shapefile.py
import geopandas as gpd

# Carrega o shapefile
gdf = gpd.read_file(r"C:\Users\joser\projects\Codes\Python\Trabalho Qgis Areas\Isozonas_GrausDecimais (1)\Isozonas_GrausDecimais.shp")

# Mostra os dados
print(f"CRS: {gdf.crs}")
print(f"Colunas: {list(gdf.columns)}")
print(f"\nDados:\n{gdf}")
