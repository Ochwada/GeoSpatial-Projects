import os
import osmnx as ox


def download_filtered_road_network(place="Berlin, Germany", output_path="data/berlin_selected_roads.geojson"):
    """
    Downloads road network for a place and filters for highways, residential streets, and footpaths.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"🛣 Downloading full road network for: {place}")

    try:
        # Get all road types
        G = ox.graph_from_place(place, network_type='all')
        edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

        # Filter by highway tag values
        selected_types = [
            'motorway', 'trunk', 'primary',       # highways
            'residential', 'tertiary', 'unclassified',  # residential streets
            'footway', 'path', 'pedestrian'       # footpaths
        ]

        filtered = edges[edges['highway'].apply(
            lambda x: any(t in x if isinstance(x, list) else [x] for t in selected_types)
        )]

        # Save filtered results
        filtered.to_file(output_path, driver="GeoJSON")
        print(f"✅ Filtered roads saved to: {output_path} ({len(filtered)} features)")

    except Exception as e:
        print(f"❌ Failed to download or filter road network: {e}")


# ----------------------------
def download_road_network(place, output_path):
    """
    Downloads OSM road network for a place and saves it as GeoJSON.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"🛣 Downloading road network for: {place}")

    try:
        # Get the drivable road network (you can also use network_type='highway' or 'all')

        roads = ox.graph_from_place(place, network_type='highways')

        # Convert to GeoDataFrame
        edges = ox.graph_to_gdfs(roads, nodes=False, edges=True)

        # Save as GeoJSON
        edges.to_file(output_path, driver="GeoJSON")

        print(f"✅ Road network saved to: {output_path}")

    except Exception as e:
        print(f"❌ Failed to download road network: {e}")