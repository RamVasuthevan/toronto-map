import os
import sqlite3
import geopandas as gpd
from download_data import download_data

API_PACKAGE_IDS = ["property-boundaries", "address-points-municipal-toronto-one-address-repository"]
DB_PATH = "toronto_map.sqlite"


def load_shp_to_sqlite(db_path: str, package_ids: list):
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    conn.execute("SELECT load_extension('mod_spatialite')")  # Enable Spatialite extension
    
    for package_id in package_ids:
        package_dir = os.path.join(os.getcwd(), package_id)
        
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                if file.endswith('.shp'):
                    shp_file_path = os.path.join(root, file)
                    gdf = gpd.read_file(shp_file_path)
                    
                    # Convert GeoDataFrame to DataFrame and upload to SQLite
                    table_name = os.path.splitext(file)[0]  # Use filename without extension as table name
                    gdf.to_sql(table_name, conn, if_exists='replace', index=False)
                    
                    # Extract the EPSG code from the GeoDataFrame's CRS
                    epsg_code = gdf.crs.to_epsg() if gdf.crs else 4326  # Use 4326 as default if CRS is not set
                    
                    # Add geometry column to the table
                    conn.execute(f"SELECT AddGeometryColumn('{table_name}', 'geometry', {epsg_code}, 'POLYGON', 'XY')")
                    
    conn.close()



if __name__ == "__main__":
    download_data(API_PACKAGE_IDS)
    load_shp_to_sqlite(DB_PATH, API_PACKAGE_IDS)
