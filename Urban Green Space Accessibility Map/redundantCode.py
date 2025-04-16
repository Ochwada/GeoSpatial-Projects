import os
import osmnx as ox


# ---------------------------- Data Preprocessing ----------------------------
def snap_points_to_graph(G, gdf_points):
    """Snap all points in GeoDataFrame to nearest nodes in graph."""
    from osmnx.distance import nearest_nodes

    gdf_points["nearest_node"] = gdf_points.geometry.apply(lambda pt: nearest_nodes(G, pt.x, pt.y))
    #gdf_points["nearest_node"] = gdf_points.geometry.progress_apply(lambda pt: nearest_nodes(G, pt.x, pt.y))

    return gdf_points

# -------------------- main-------------
import os
import osmnx as ox
import geopandas as gpd

import pickle
import time


if __name__ == "__main__":

    # --- 1. Load File Paths ---
    buildings_path = "../DataCollection/data/berlin_mitte_buildings.geojson"
    greens_path = "../DataCollection/data/berlin_green.geojson"
    road_path = "../DataCollection/data/berlin_roads_walks.geojson"
    graphml_path = "../DataCollection/data/berlin_walk.graphml"

    output_path = "data/green_accessibility.geojson"

    # Temporary cache folder
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    # Cached files
    snapped_buildings_path = os.path.join(temp_dir, "snapped_buildings.geojson")
    green_nodes_path = os.path.join(temp_dir, "green_nodes.pkl")

    # --- 1.5 Clip Datasets ---
    print("✂️ Clipping roads and green spaces to Berlin-Mitte area...")
    pp.clip_to_area(
        input_path=road_path,
        clip_mask_path=buildings_path,
        output_path="data/berlin_mitte_roads.geojson"
    )
    pp.clip_to_area(
        input_path=greens_path,
        clip_mask_path=buildings_path,
        output_path="data/berlin_mitte_green.geojson"
    )

    greens_path = "data/berlin_mitte_green.geojson"

    # --- 2. Sanity Check on File Paths ---
    assert os.path.exists(buildings_path), f"❌ Missing: {buildings_path}"
    assert os.path.exists(greens_path), f"❌ Missing: {greens_path}"
    assert os.path.exists(graphml_path), f"❌ Missing: {graphml_path}"
    print("📂 All required input files found.")

    # --- 3. Load Graph ---
    print("📡 Loading road network from saved GraphML...")
    G = ox.load_graphml(graphml_path)
    print(f"✅ Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges")

    # --- 4. Load and Preprocess Datasets ---
    print("🏢 Loading buildings...")
    gdf_buildings = pp.load_and_reproject(buildings_path)
    print(f"✅ Loaded {len(gdf_buildings)} buildings")

    print("🌿 Loading green spaces...")
    gdf_greens_raw = pp.load_and_reproject(greens_path)
    print(f"✅ Loaded {len(gdf_greens_raw)} green features")

    print("🧹 Filtering green polygons...")
    gdf_greens, green_union = pp.filter_green_spaces(gdf_greens_raw)
    print(f"✅ Retained {len(gdf_greens)} green polygons")

    # --- 5. Optional: Sampling ---
    USE_SAMPLE = True
    SAMPLE_SIZE = 100

    print("📍 Generating building centroids...")
    gdf_points = pp.generate_building_centroids(gdf_buildings)

    if USE_SAMPLE:
        print(f"⚠️ Using a sample of {SAMPLE_SIZE} centroids for testing...")
        gdf_points = gdf_points.sample(SAMPLE_SIZE, random_state=42)

    print(f"✅ Generated {len(gdf_points)} centroids")

    # --- 6. Snap to Graph OR Load from Cache ---
    if os.path.exists(snapped_buildings_path) and os.path.exists(green_nodes_path):
        print("♻️ Using cached snapped points and green nodes...")
        gdf_points = gpd.read_file(snapped_buildings_path)
        with open(green_nodes_path, "rb") as f:
            green_nodes = pickle.load(f)
    else:
        print("📌 Snapping buildings to nearest graph nodes...")
        gdf_points = pp.snap_points_to_graph(G, gdf_points)
        gdf_points.to_file(snapped_buildings_path, driver="GeoJSON")
        print("✅ Snapping complete and cached")

        print("🌱 Snapping green spaces to graph nodes...")
        green_nodes = pp.get_green_space_nodes(G, gdf_greens)
        with open(green_nodes_path, "wb") as f:
            pickle.dump(green_nodes, f)
        print(f"✅ Found and cached {len(green_nodes)} green space nodes")

    # --- 7. Compute Walking Distances ---
    print("🚶 Calculating walking distances and times...")
    start_time = time.time()
    gdf_points = pp.compute_shortest_distances(G, gdf_points, green_nodes)
    print(f"✅ Distance + time calculation complete in {round(time.time() - start_time, 2)} seconds")

    # --- 8. Assign Accessibility Categories ---
    print("🎨 Assigning color categories based on walk time...")
    gdf_points = pp.add_accessibility_color(gdf_points)
    print("✅ Colors assigned")

    # --- 9. Export Final GeoJSON ---
    print("💾 Exporting final GeoJSON...")
    unsupported_types = ["datetime64[ns]", "object"]
    cols_to_drop = gdf_points.select_dtypes(include=unsupported_types).columns

    if len(cols_to_drop) > 0:
        print(f"⚠️ Dropping unsupported fields before saving: {list(cols_to_drop)}")
        gdf_points = gdf_points.drop(columns=cols_to_drop)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    gdf_points.to_file(output_path, driver="GeoJSON")
    print(f"✅ Accessibility analysis saved to: {output_path}")


# ----------------------  Access like this: ------------------------
    G = data["G"]
    gdf_buildings = data["gdf_buildings"]
    gdf_greens = data["gdf_greens"]
    green_union = data["green_union"]
    output_path = data["output_path"]
    snapped_buildings_path = data["snapped_buildings_path"]
    green_nodes_path = data["green_nodes_path"]


# ---------------------------- Data Collection ----------------------------
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