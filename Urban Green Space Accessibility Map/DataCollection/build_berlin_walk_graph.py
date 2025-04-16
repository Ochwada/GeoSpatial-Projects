# build_berlin_walk_graph.py

import os
import osmnx as ox
import geopandas as gpd

# Create data folder
os.makedirs("data", exist_ok=True)

# File paths
graphml_path = "data/berlin_walk.graphml"
nodes_path = "data/berlin_walk_nodes.geojson"
edges_path = "data/berlin_walk_edges.geojson"

# --- STEP 1: Download walkable street network ---
print("📥 Downloading walkable road network for Berlin...")
G = ox.graph_from_place("Berlin, Germany", network_type="walk")

# --- STEP 2: Save the full graph as GraphML ---
print("💾 Saving full graph to GraphML...")
ox.save_graphml(G, filepath=graphml_path)
print(f"✅ Graph saved to: {graphml_path}")

# --- STEP 3: Export nodes and edges as GeoJSON (optional) ---
print("🗂 Exporting nodes and edges for visualization...")
nodes, edges = ox.graph_to_gdfs(G)
nodes.to_file(nodes_path, driver="GeoJSON")
edges.to_file(edges_path, driver="GeoJSON")
print(f"✅ Nodes saved to: {nodes_path}")
print(f"✅ Edges saved to: {edges_path}")

# --- STEP 4: Load the graph back from GraphML ---
print("🔁 Reloading graph from GraphML...")
G_loaded = ox.load_graphml(graphml_path)
print(f"✅ Reloaded graph has {len(G_loaded.nodes)} nodes and {len(G_loaded.edges)} edges")
