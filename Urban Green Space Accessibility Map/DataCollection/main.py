from owslib.wfs import WebFeatureService
from downloader import download_osm_data, download_osm_buildings, download_demography_data

# Example usage:
if __name__ == '__main__':
    print("Hello Linda")



    """
    # Use the base WFS URL (no GetCapabilities params!)
    url = "https://gdi.berlin.de/services/wfs/ua_einwohnerdichte_2023"

    wfs = WebFeatureService(url=url, version="2.0.0")
    print("\n📄 Available Layers:")
    for layer in list(wfs.contents):
        print("🔹", layer)


    # ------- Download the Green Area -------
    base_url = "https://gdi.berlin.de/services/wfs/ua_einwohnerdichte_2023"
    layer = "ua_einwohnerdichte_2023:einwohnerdichte2023"
    output_path = "data/berlin_population_density.geojson"

    download_demography_data(base_url, layer, output_path)

# download_osm_data("Berlin, Germany", "data/berlin_green.geojson")

# ------- Download the Green Area -------
# download_osm_buildings("Mitte, Berlin, Germany", "data/berlin_mitte_buildings.geojson")
# OR
# --- bbox = (52.54, 52.49, 13.42, 13.37)  # North, South, East, West
# --- download_osm_buildings("Berlin", "data/berlin_subset.geojson", bbox=bbox)

"""
