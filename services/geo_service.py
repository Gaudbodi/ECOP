import json
import os
from shapely.geometry import shape, Point
import logging

# Set the path to the regions file
REGIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'ghana_regions.json')

class GeoService:
    def __init__(self):
        self.regions_data = None
        self.load_regions()

    def load_regions(self):
        """Loads the GeoJSON data for Ghana regions."""
        try:
            with open(REGIONS_PATH, 'r') as f:
                self.regions_data = json.load(f)
            logging.info("Successfully loaded Ghana regions GeoJSON.")
        except Exception as e:
            logging.error(f"Failed to load Ghana regions GeoJSON: {e}")
            self.regions_data = None

    def resolve_location(self, lat, lon):
        """
        Determines which administrative areas a coordinate intersects with.
        Returns a list of affected region names.
        """
        if not self.regions_data:
            return ["Unknown Region"]

        point = Point(lon, lat) # Point(x, y) -> Point(lon, lat)
        affected_areas = []

        for feature in self.regions_data['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                region_name = feature['properties'].get('region')
                if region_name:
                    affected_areas.append(region_name)
        
        return affected_areas if affected_areas else ["Ghana (General)"]

# Singleton instance
geo_service = GeoService()
