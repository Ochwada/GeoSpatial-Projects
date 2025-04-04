import os
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
from owslib.wfs import WebFeatureService

# Download OSM data (roads)



# Download OSM data (leisure=park, landuse=grass, natural=wood)
def download_osm_data(place, output_path):
    tags = {
        "leisure": "park",
        "landuse": "grass",
        "natural": "wood"
    }

    # Make sure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Downloading green space data for: {place}")

    green_spaces = ox.features_from_place(place, tags)

    if green_spaces.empty:
        print("⚠️ No green space data found.")
    else:
        green_spaces.to_file(output_path, driver="GeoJSON")
        print(f"✅ Data Saved to {output_path}")


def download_osm_buildings(place, output_path, bbox=None):
    """
    Download OSM building footprints for a given place or bounding box.

    Parameters:
    - place (str): e.g. "Mitte, Berlin, Germany"
    - output_path (str): Where to save the GeoJSON
    - bbox (tuple, optional): (north, south, east, west) to limit the area
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tags = {"building": True}

    try:
        if bbox:
            north, south, east, west = bbox
            print(f"🔍 Using bounding box: {bbox}")
            buildings = ox.features_from_bbox(north, south, east, west, tags=tags)
        else:
            print(f"📍 Geocoding place: {place}")
            gdf = ox.geocode_to_gdf(place)
            polygon = gdf.geometry[0]
            buildings = ox.features_from_polygon(polygon, tags=tags)

        print(f"🏗️  Downloaded {len(buildings)} building footprints.")
        buildings.to_file(output_path, driver="GeoJSON")
        print(f"✅ Buildings saved to {output_path}")

    except MemoryError:
        print("❗ MemoryError: Try reducing the size of the area (use a smaller place or a bounding box).")
    except Exception as e:
        print(f"❗ Failed to download buildings: {e}")


def download_demography_data(base_url, typename, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"🌍 Connecting to WFS: {typename}")

    try:
        wfs = WebFeatureService(url=base_url, version="2.0.0")
        response = wfs.getfeature(typename=typename, outputFormat='application/json')

        gdf = gpd.read_file(response)

        if gdf.empty:
            print("⚠️ No data found.")
        else:
            gdf.to_file(output_path, driver="GeoJSON")
            print(f"✅ Data saved to: {output_path}")

    except Exception as e:
        print(f"❌ Failed to download: {e}")

