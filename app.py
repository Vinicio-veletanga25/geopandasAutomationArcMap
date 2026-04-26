# -*- coding: utf-8 -*-

import geopandas as gpd
from shapely.geometry import Point, LineString
from tqdm import tqdm


#esta funcion crea un archivo shapefile a partir de una lista de coordenadas
def create_lines_shp(list_coords, file_name, old_lines=None):
    try:
        estructure = {}
        if old_lines:
            #Recuperando los atributos de la capa de lineas antiguas
            for key in old_lines[0].keys():
                if key != 'geometry':
                    lista = [line[key] for line in old_lines]
                    estructure[key] = lista
        geometry_lines = [LineString(coordenadas) for coordenadas in list_coords]
        estructure['geometry'] = geometry_lines
        lineas_gdf = gpd.GeoDataFrame(estructure, crs='EPSG:32717')
        lineas_gdf.to_file(file_name + '.shp')
    except Exception as e:
        print(e)

#esta funcion compara dos coordenadas y retorna true si las coordenadas estan 
# cerca en la distancia de 1 metro
def compare_coords(tupla1, tupla2):
    point1 = Point(tupla1)
    point2 = Point(tupla2)
    distance = point1.distance(point2)
    if distance < 1:
        return True
    else:
        return False

#busca las coordenadas de un punto con el id enviado en otro shape
def search_new_coords(id, shape, code='CODIGOELEM'):
    for row in shape.iterrows():
        if row[1][code] == id:
            return row[1]['geometry'].coords[:]
    return False


def generate(file_old_points, file_new_points, file_old_lines, code='CODIGOELEM', directory='./result/capa_generada'):
    lineas = gpd.read_file(file_old_lines)
    old_points = gpd.read_file(file_old_points)
    new_points = gpd.read_file(file_new_points)
    trazo = []
    new_vertices = []
    old_lines =[]
    for index, linea in tqdm(lineas.iterrows()):
        vertices = linea['geometry']
        trazo = []
        for vertice in vertices.coords:
            vertice_flag = False
            for idx, point in old_points.iterrows():
                point_tuple = tuple(point.geometry.coords[0])
                if compare_coords(vertice, point_tuple):
                    id = point[code]
                    point_update = search_new_coords(id, new_points, code)
                    if point_update:
                        punto_trazo = point_update[0]
                        trazo.append(punto_trazo)
                        vertice_flag = True
                    #busqueda de punto nuevo en la capa de puntos antiguos
                    for idx, new_point in new_points.iterrows():
                        point_tuple = tuple(new_point.geometry.coords[0])
                        if compare_coords(vertice, point_tuple):
                            new_id = new_point[code]
                            update_point = search_new_coords(new_id, new_points, code)
                            if not update_point:
                                #aqui agrega un poste nuevo que no existe en la capa de postes antiguos
                                trazo.append(vertice)
                                vertice_flag = True
            #en el caso que la linea pase por un punto que no existe en la capa de postes
            if not vertice_flag:
                trazo.append(vertice)
        #para realizar un trazo debe existir almenos 2 puntos
        if len(trazo) >= 2:
            new_vertices.append(trazo)
            old_lines.append(linea)
    if len(new_vertices) > 0:
        create_lines_shp(new_vertices, directory, old_lines)


if __name__ == '__main__':
    archivo_puntos_antiguos = './tramos/POSTE_ANTIGUO.shp' #archivo de postes antiguos
    archivo_lineas_antiguos = './tramos/TramoMTA.shp' #archivo de lineas antiguas
    archivo_puntos_nuevos = './tramos/POSTE.shp' #archivo de postes nuevos
    directorio_resultado = './movido/capa_VinicioMovido' #directorio donde se guardara el archivo shapefile de lineas nuevas
    code = 'CODIGOELEM'
    generate(archivo_puntos_antiguos, archivo_puntos_nuevos, archivo_lineas_antiguos, code, directorio_resultado)
