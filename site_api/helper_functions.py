import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from .data_model import BuildSite


def to_geodataframe(features):
    geometries = [Polygon(feature.geometry.coordinates[0]) for feature in features]
    return gpd.GeoDataFrame(geometry=geometries)

def buildsite_to_geodataframes(buildsite: BuildSite):
    building_limits_gdf = to_geodataframe(buildsite.building_limits.features)
    height_plateaus_gdf = to_geodataframe(buildsite.height_plateaus.features)
    height_plateaus_gdf['elevation'] =[feature.properties['elevation'] for feature in buildsite.height_plateaus.features]
    return building_limits_gdf, height_plateaus_gdf

def split_building_limits(project_name, building_limits_gdf, height_plateaus_gdf):
    output_dict = {}
    for i, b in building_limits_gdf.iterrows():
        result_gdf = gpd.GeoDataFrame()
        for _, h in height_plateaus_gdf.iterrows():
            intersection = b.geometry.intersection(h.geometry)
            # put in gdf
            if not intersection.is_empty:
                tmp = gpd.GeoDataFrame(geometry=[intersection])
                tmp['elevation'] = h['elevation']
                result_gdf = pd.concat([result_gdf,tmp]).reset_index(drop=True)
        output_dict[i] = {
            'project_name':project_name,
            'building_id':i,
            'split_building_limits':result_gdf.to_geo_dict(),
            'building_limits':gpd.GeoDataFrame(geometry=[building_limits_gdf.iloc[0].geometry]).to_geo_dict(),
            'height_plateaus':height_plateaus_gdf.to_geo_dict()
        }
    return output_dict