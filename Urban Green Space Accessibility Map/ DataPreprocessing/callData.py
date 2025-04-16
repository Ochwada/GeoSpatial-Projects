

import os
import osmnx as ox
import geopandas as gpd
import pickle
import time

import preprocessing as pp
def clip_all_input():
    """Clip raw input data (roads + green spaces) to Berlin-Mitte area."""

    print("Starting data clipping process...")

    pp.clip_to_area(
        input_path="../DataCollection/data/berlin_roads_walks.geojson",
        clip_mask_path="../DataCollection/data/berlin_mitte_buildings.geojson",
        output_path="data/berlin_mitte_roads.geojson"
    )

    pp.clip_to_area(
        input_path="../DataCollection/data/berlin_green.geojson",
        clip_mask_path="../DataCollection/data/berlin_mitte_buildings.geojson",
        output_path="data/berlin_mitte_green.geojson"
    )
    print("All input data clipped.\n")


def load_and_prepare_data():
    # --- Load File Paths ---
    buildings_path = "../DataCollection/data/berlin_mitte_buildings.geojson"
    greens_path = "data/berlin_mitte_green.geojson"
    road_path = "data/berlin_mitte_roads.geojson"
    graphml_path = "../DataCollection/data/berlin_walk.graphml"
    output_path = "data/green_accessibility.geojson"

    # --- Create Temp Dir and Cache Paths ---
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    snapped_buildings_path = os.path.join(temp_dir, "snapped_buildings.geojson")
    green_nodes_path = os.path.join(temp_dir, "green_nodes.pkl")

    # --- Sanity Check ---
    assert os.path.exists(buildings_path), f"❌ Missing: {buildings_path}"
    assert os.path.exists(greens_path), f"❌ Missing: {greens_path}"
    assert os.path.exists(graphml_path), f"❌ Missing: {graphml_path}"
    print("📂 All required input files found.")

    # --- Load Graph ---
    print("📡 Loading road network from saved GraphML...")
    G = ox.load_graphml(graphml_path)
    print(f"✅ Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges")

    # --- Load and Preprocess GeoDataFrames ---
    print("🏢 Loading buildings...")
    gdf_buildings = pp.load_and_reproject(buildings_path)
    print(f"✅ Loaded {len(gdf_buildings)} buildings")

    print("🌿 Loading green spaces...")
    gdf_greens_raw = pp.load_and_reproject(greens_path)
    print(f"✅ Loaded {len(gdf_greens_raw)} green features")

    print("🧹 Filtering green polygons...")
    gdf_greens, green_union = pp.filter_green_spaces(gdf_greens_raw)
    print(f"✅ Retained {len(gdf_greens)} green polygons")

    return {
        "buildings_path": buildings_path,
        "greens_path": greens_path,
        "road_path": road_path,
        "graphml_path": graphml_path,
        "output_path": output_path,
        "temp_dir": temp_dir,
        "snapped_buildings_path": snapped_buildings_path,
        "green_nodes_path": green_nodes_path,
        "G": G,
        "gdf_buildings": gdf_buildings,
        "gdf_greens": gdf_greens,
        "green_union": green_union,
    }

#  ------------- Generate & Sample Centroids (with optional save) -------------

def generate_and_sample_centroids(gdf_buildings, use_sample=True, sample_size=100, output_path="temp/centroids.geojson"):
    print("📍 Generating building centroids...")
    gdf_points = pp.generate_building_centroids(gdf_buildings)

    if use_sample:
        print(f"⚠️ Using a sample of {sample_size} centroids for testing...")
        gdf_points = gdf_points.sample(sample_size, random_state=42)

    print(f"✅ Generated {len(gdf_points)} centroids")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    gdf_points.to_file(output_path, driver="GeoJSON")
    print(f"💾 Centroids saved to: {output_path}")

    return gdf_points


#  ------------- Snap Points and Greens to Graph Nodes (cache if available) -------------

def snap_points_and_greens(G, gdf_points, gdf_greens, points_path, greens_path):
    if os.path.exists(points_path) and os.path.exists(greens_path):
        print("♻️ Using cached snapped points and green nodes...")
        gdf_points = gpd.read_file(points_path)
        with open(greens_path, "rb") as f:
            green_nodes = pickle.load(f)
    else:
        print("📌 Snapping buildings to nearest graph nodes...")
        gdf_points = pp.snap_points_to_graph(G, gdf_points)
        gdf_points.to_file(points_path, driver="GeoJSON")
        print("✅ Snapping complete and cached")

        print("🌱 Snapping green spaces to graph nodes...")
        green_nodes = pp.get_green_space_nodes(G, gdf_greens)
        with open(greens_path, "wb") as f:
            pickle.dump(green_nodes, f)
        print(f"✅ Found and cached {len(green_nodes)} green space nodes")

    return gdf_points, green_nodes

#  ------------- Compute Distances and Add Categories -------------
def compute_accessibility(G, gdf_points, green_nodes):
    print("🚶 Calculating walking distances and times...")
    start_time = time.time()
    gdf_points = pp.compute_shortest_distances(G, gdf_points, green_nodes)
    print(f"✅ Distance + time calculation complete in {round(time.time() - start_time, 2)} seconds")

    print("🎨 Assigning color categories based on walk time...")
    gdf_points = pp.add_accessibility_color(gdf_points)
    print("✅ Colors assigned")

    return gdf_points

#  ------------- Export Final GeoJSON -------------
def export_final_geojson(gdf_points, output_path):
    print("💾 Exporting final GeoJSON...")

    unsupported_types = ["datetime64[ns]", "object"]
    cols_to_drop = gdf_points.select_dtypes(include=unsupported_types).columns

    if len(cols_to_drop) > 0:
        print(f"⚠️ Dropping unsupported fields before saving: {list(cols_to_drop)}")
        gdf_points = gdf_points.drop(columns=cols_to_drop)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    gdf_points.to_file(output_path, driver="GeoJSON")
    print(f"✅ Accessibility analysis saved to: {output_path}")
