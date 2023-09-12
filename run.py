import os
import subprocess
import sqlite3


# Define the paths to your zip files
address_points_zip = "Municipal address points (wgs84) - shapefile.zip"
property_boundaries_zip = "Property Boundaries (wgs84) - shapefile.zip"

# Function to extract zip files
def extract_zip(zip_path, output_path="."):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_path)

# Create the directories if they don't exist
address_points_dir = "Municipal address points (wgs84) - shapefile"
property_boundaries_dir = "Property Boundaries (wgs84) - shapefile"

os.makedirs(address_points_dir, exist_ok=True)
os.makedirs(property_boundaries_dir, exist_ok=True)

# Paths for the database and shapefiles
db_path = "toronto.sqlite"
address_points_shp_basepath = "Municipal address points (wgs84) - shapefile/ADDRESS_POINT_WGS84"
property_boundaries_shp_basepath = "Property Boundaries (wgs84) - shapefile/PROPERTY_BOUNDARIES_WGS84"

# Delete the database if it already exists
if os.path.exists(db_path):
    os.remove(db_path)

# Connect to the SQLite database and initialize SpatiaLite
conn = sqlite3.connect(db_path)
conn.enable_load_extension(True)
conn.load_extension("mod_spatialite")  # Load the SpatiaLite extension
cursor = conn.cursor()
cursor.execute("SELECT InitSpatialMetadata(1);")
conn.close()

# Load shapefiles into the SpatiaLite database using spatialite_tool
def load_shapefile_into_db(shp_basepath, table_name):
    cmd = [
        "spatialite_tool",
        "-i",
        "-shp", shp_basepath,
        "-d", db_path,
        "-t", table_name,
        "--charset", "CP1252"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stderr.decode('utf-8'))

# Load the address points shapefile
load_shapefile_into_db(address_points_shp_basepath, "address_points")

# Load the property boundaries shapefile
load_shapefile_into_db(property_boundaries_shp_basepath, "property_boundaries")

print("Shapefiles loaded into SpatiaLite database successfully!")
