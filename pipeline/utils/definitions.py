import pydantic
import geopandas as gpd
from shapely.geometry import Polygon
from typing import List, Optional, Dict
from pydantic import ConfigDict


class CBSA(pydantic.BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    area_code: str
    cbsa_title: str
    component_counties_fips: List[str]
    total_population: Optional[int] = None
    geometry: Optional[gpd.GeoDataFrame] = None


class CBSADict(pydantic.RootModel[Dict[str, CBSA]]):
    pass
