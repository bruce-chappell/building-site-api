from pydantic import BaseModel, conlist, field_validator, ValidationError, model_validator, Field 
from typing import List, Dict, Optional, Any
from shapely.geometry import Polygon
from shapely.ops import unary_union


class Geometry(BaseModel):
    type: str
    coordinates: List[conlist(conlist(float, min_length=2, max_length=2),min_length=3)]

class BuildLimit(BaseModel):
    type: str
    properties: Optional[Dict[str,Any]]
    geometry: Geometry


class HeightPlateau(BaseModel):
    type: str
    properties: Dict[str,Any] = Field(..., example={"elevation": 0})
    geometry: Geometry

    @field_validator('properties')
    def check_elevation(cls, v: Dict):
        if 'elevation' not in v:
            raise ValueError('properties must have an elevation key')
        if not isinstance(v['elevation'], (int,float)):
            raise TypeError('The value of elevation must be a float')
        return v 

class BuildLimits(BaseModel):
    type: str
    features: List[BuildLimit] 

class HeightPlateaus(BaseModel):
    type: str
    features: List[HeightPlateau]

class BuildSite(BaseModel):
    building_limits: BuildLimits
    height_plateaus: HeightPlateaus

    @model_validator(mode='before')
    def check_input(cls, values):
        if 'height_plateaus' not in values or not values['height_plateaus']:
            raise ValueError('At least one height plateau must be provided')
        if 'building_limits' not in values or not values['building_limits']:
            raise ValueError('At least one building limit must be provided')
        return values
    
    @field_validator('height_plateaus')
    def check_height_plateaus(cls, v: HeightPlateaus):
        if len(v.features) == 0:
            raise ValueError('At least one height plateau must be provided')
        return v
    
    @field_validator('building_limits')
    def check_building_limits(cls, v: BuildLimits):
        if len(v.features) == 0:
            raise ValueError('At least one building limit must be provided')
        return v

    def validate_site(self, tolerance: int = 6):
        building_geometries = [Polygon(feature.geometry.coordinates[0]) for feature in self.building_limits.features]
        height_geometries = [Polygon(feature.geometry.coordinates[0]) for feature in self.height_plateaus.features]

        combined_height_plateaus = unary_union(height_geometries)

        # Ensure height plateaus have area
        for i, height in enumerate(height_geometries):
            if round(height.area == 0,tolerance):
                raise ValueError(f"Height plateau {i} has no area.")
            
        # Ensure building limits have area
        for i, building in enumerate(building_geometries):
            if round(building.area,tolerance) == 0:
                raise ValueError(f"Building limit {i} has no area.")


        # Check if each building limit is completely covered by the height plateaus
        for i, building in enumerate(building_geometries):
            if not combined_height_plateaus.contains(building):
                intersection = combined_height_plateaus.intersection(building)
                area = round(building.difference(intersection).area,tolerance)
                if area > 0:
                    raise ValueError(f"Height plateaus do not completely cover building {i}.")
        print(f'Buildings are covered by height plateaus to {tolerance} decimal places')

        # Check for overlaps between height plateaus
        for i, height1 in enumerate(height_geometries):
            for j, height2 in enumerate(height_geometries):
                if i != j:
                    area = round(height1.intersection(height2).area,tolerance)
                    if area > 0:
                        print(area)
                        raise ValueError(f"Height plateaus {i} and {j} overlap.")
        print(f'Height plateaus do not overlap to {tolerance} decimal places')