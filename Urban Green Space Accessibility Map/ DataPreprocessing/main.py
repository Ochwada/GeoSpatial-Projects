import os
# --------- Self packages -------------
import preprocessing as pp
import callData as cdata

if __name__ == "__main__":

    # ------------ 1. Clip and Save Datasets ------------
    #call_data.clip_all_input()  # Step 1: clip and save data

    # ------------ 2. Load File Paths ------------
    data = cdata.load_and_prepare_data()  # Step 2: load everything

    # ------------ 3. Generate or reuse centroids ------------
    gdf_points = cdata.generate_and_sample_centroids(
        data["gdf_buildings"],
        use_sample=True,
        sample_size=100,
        output_path=os.path.join(data["temp_dir"], "centroids.geojson")
    )

    # ------------ 4. Snap to graph ------------
    gdf_points, green_nodes = cdata.snap_points_and_greens(
        G=data["G"],
        gdf_points=gdf_points,
        gdf_greens=data["gdf_greens"],
        points_path=data["snapped_buildings_path"],
        greens_path=data["green_nodes_path"]
    )

 # ------------ 5. Compute distances and assign accessibility ------------
    gdf_points = cdata.compute_accessibility(data["G"], gdf_points, green_nodes)

    # Step 6: Save final result
    cdata.export_final_geojson(gdf_points, data["output_path"])