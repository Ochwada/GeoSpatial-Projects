import os
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
from tqdm import tqdm
tqdm.pandas()
import numpy as np
from osmnx.distance import nearest_nodes



def load_and_reproject(filepath, epsg=25833):
    """Load GeoJSON and reproject to specified CRS (default UTM33N)."""
    gdf = gpd.read_file(filepath)

    # Drop problematic fields like datetime or unsupported objects
    unsupported_fields = ["check_out"]
    for field in unsupported_fields:
        if field in gdf.columns:
            print(f"⚠️ Dropping unsupported field: {field}")
            gdf = gdf.drop(columns=[field])

    return gdf.to_crs(epsg=epsg)


def filter_green_spaces(gdf_greens):
    """Filter only Polygon/MultiPolygon green spaces and merge them."""
    gdf_filtered = gdf_greens[gdf_greens.geometry.type.isin(["Polygon", "MultiPolygon"])]
    return gdf_filtered, unary_union(gdf_filtered.geometry)


def generate_building_centroids(gdf_buildings):
    """Return GeoDataFrame with centroids from building polygons."""
    gdf_buildings["centroid"] = gdf_buildings.centroid
    return gpd.GeoDataFrame(geometry=gdf_buildings["centroid"], crs=gdf_buildings.crs)


def snap_points_to_graph(G, gdf_points):
    """Efficiently snap all points to nearest graph nodes."""
    x_coords = gdf_points.geometry.x.values
    y_coords = gdf_points.geometry.y.values
    nearest = nearest_nodes(G, X=x_coords, Y=y_coords, return_dist=False)
    gdf_points["nearest_node"] = nearest
    return gdf_points


def get_green_space_nodes(G, gdf_greens):
    """Efficiently return a list of node IDs closest to green space centroids."""
    centroids = gdf_greens.geometry.centroid
    x_coords = centroids.x.values
    y_coords = centroids.y.values
    green_nodes = nearest_nodes(G, X=x_coords, Y=y_coords, return_dist=False)
    return green_nodes


def compute_shortest_distances(G, gdf_points, green_nodes):
    """Compute shortest distance and time from each point to nearest green space node."""
    import networkx as nx

    distances = []
    times = []
    for node in gdf_points["nearest_node"]:
        try:
            lengths = [
                nx.shortest_path_length(G, node, g_node, weight="length")
                for g_node in green_nodes
            ]
            min_dist = min(lengths)
            walk_time_min = round(min_dist / 1.4 / 60, 2)  # 1.4 m/s, then convert to minutes
            distances.append(min_dist)
            times.append(walk_time_min)
        except:
            distances.append(None)
            times.append(None)

    gdf_points["access_distance_m"] = distances
    gdf_points["walk_time_min"] = times
    return gdf_points


def add_accessibility_color(gdf_points):
    """Add a color column for accessibility levels (based on walk time)."""
    def colorize(time):
        if time is None:
            return "#cccccc"  # gray for no data
        elif time <= 5:
            return "#2ecc71"  # green
        elif time <= 10:
            return "#f1c40f"  # yellow
        elif time <= 20:
            return "#e67e22"  # orange
        else:
            return "#e74c3c"  # red

    gdf_points["access_color"] = gdf_points["walk_time_min"].apply(colorize)
    return gdf_points


def clip_to_area(input_path, clip_mask_path, output_path):
    """
    Clips input GeoDataFrame to a polygon mask and saves the result as GeoJSON.
    Removes unsupported fields before writing.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"⏳ Reading: {input_path}")
    gdf = gpd.read_file(input_path)
    gdf = sanitize_gdf(gdf)

    print(f"⏳ Reading clip mask: {clip_mask_path}")
    mask = gpd.read_file(clip_mask_path)
    if gdf.crs != mask.crs:
        mask = mask.to_crs(gdf.crs)

    print("✂️ Clipping in progress...")
    clipped = gpd.clip(gdf, mask)
    clipped = sanitize_gdf(clipped)

    if clipped.empty:
        print("⚠️ Result is empty after clipping.")
    else:
        print("💾 Saving to GeoJSON...")
        clipped.to_file(output_path, driver="GeoJSON")
        print(f"✅ Clipped data saved to: {output_path}")


def sanitize_gdf(gdf):
    """
    Removes fields that contain list, dict, or datetime types not supported by GeoJSON.
    """
    to_drop = [col for col in gdf.columns if gdf[col].apply(lambda x: isinstance(x, (list, dict))).any()]
    if to_drop:
        print(f"⚠️ Dropping unsupported fields: {to_drop}")
        gdf = gdf.drop(columns=to_drop)

    # Drop datetime columns too
    unsupported_types = ["datetime64[ns]", "object"]
    for col in gdf.select_dtypes(include=unsupported_types).columns:
        if gdf[col].dtype.name == "datetime64[ns]":
            print(f"⚠️ Dropping datetime field: {col}")
            gdf = gdf.drop(columns=[col])

    return gdf
