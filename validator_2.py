from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import geojson
import geopandas as gpd
from shapely.geometry import shape, Polygon
from shapely.ops import split, unary_union

app = FastAPI()

# In-memory storage for simplicity
storage = {
    "building_limits": [],
    "height_plateaus": [],
    "split_building_limits": []
}

class GeoJSONFeature(BaseModel):
    type: str
    properties: Dict
    geometry: Dict

class GeoJSONFeatureCollection(BaseModel):
    type: str
    features: List[GeoJSONFeature]

@app.post("/process/")
def process_geojson(building_limits: GeoJSONFeatureCollection, height_plateaus: GeoJSONFeatureCollection):
    try:
        # Parse building limits
        building_geometries = [shape(feature.geometry) for feature in building_limits.features]

        # Parse height plateaus
        height_geometries = [shape(feature.geometry) for feature in height_plateaus.features]
        elevations = [feature.properties["elevation"] for feature in height_plateaus.features]

        # Validate the input data
        validate_geojson(building_geometries, height_geometries)

        # Split building limits by height plateaus
        split_building_limits = []
        for building in building_geometries:
            for height, elevation in zip(height_geometries, elevations):
                if building.intersects(height):
                    intersection = building.intersection(height)
                    if isinstance(intersection, Polygon):
                        split_building_limits.append({
                            "geometry": intersection,
                            "properties": {"elevation": elevation}
                        })

        # Store the entities
        storage["building_limits"] = building_limits.features
        storage["height_plateaus"] = height_plateaus.features
        storage["split_building_limits"] = split_building_limits

        return {"message": "Processing complete", "split_building_limits": split_building_limits}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/data/")
def get_data():
    return storage

def validate_geojson(building_geometries, height_geometries):
    # Combine all height plateaus into a single geometry
    combined_height_plateaus = unary_union(height_geometries)

    # Check if each building limit is completely covered by the height plateaus
    for building in building_geometries:
        if not combined_height_plateaus.contains(building):
            raise ValueError("Height plateaus do not completely cover the building limits.")

    # Check for gaps or overlaps between height plateaus
    for i, height1 in enumerate(height_geometries):
        for j, height2 in enumerate(height_geometries):
            if i != j:
                if height1.intersects(height2):
                    raise ValueError("Height plateaus overlap.")
                if not height1.touches(height2):
                    raise ValueError("There are gaps between height plateaus.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
