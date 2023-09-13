import os
import sqlite3
import zipfile
import subprocess

# Constants
DB_PATH = "toronto.sqlite"
ADDRESS_POINTS_ZIP = "Municipal address points (wgs84) - shapefile.zip"
PROPERTY_BOUNDARIES_ZIP = "Property Boundaries (wgs84) - shapefile.zip"
ADDRESS_POINTS_DIR = "Municipal address points (wgs84) - shapefile"
PROPERTY_BOUNDARIES_DIR = "Property Boundaries (wgs84) - shapefile"
CHARSET = "CP1252"

def extract_zip(zip_path, output_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

def unzip_shapefiles():
    os.makedirs(ADDRESS_POINTS_DIR, exist_ok=True)
    os.makedirs(PROPERTY_BOUNDARIES_DIR, exist_ok=True)

    extract_zip(ADDRESS_POINTS_ZIP, ADDRESS_POINTS_DIR)
    extract_zip(PROPERTY_BOUNDARIES_ZIP, PROPERTY_BOUNDARIES_DIR)

def load_shapefile_into_db(shp_basepath, table_name, db_path):
    cmd = [
        "spatialite_tool",
        "-i",
        "-shp", shp_basepath,
        "-d", db_path,
        "-t", table_name,
        "--charset", CHARSET
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stderr.decode('utf-8'))

def load_shapefiles_into_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    conn.load_extension("mod_spatialite")
    cursor = conn.cursor()
    cursor.execute("SELECT InitSpatialMetadata(1);")
    conn.close()

    load_shapefile_into_db(os.path.join(ADDRESS_POINTS_DIR, "ADDRESS_POINT_WGS84"), "address_points", DB_PATH)
    load_shapefile_into_db(os.path.join(PROPERTY_BOUNDARIES_DIR, "PROPERTY_BOUNDARIES_WGS84"), "property_boundaries", DB_PATH)
    print("Shapefiles loaded into SpatiaLite database successfully!")

def get_row_count(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def print_table_details(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get column details
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    print(f"\nDetails for table: {table_name}")
    header = "| {:<20} | {:<10} |".format("Column Name", "Type")
    separator = "+" + "-"*22 + "+" + "-"*12 + "+"
    print(separator)
    print(header)
    print(separator)
    for column in columns:
        print(f"| {column[1]:<20} | {column[2]:<10} |")
    print(separator)
    if any(col[1] == 'pk_uid' for col in columns):
        print("Note: The 'pk_uid' column is a primary key column typically added during the import process for unique identification.")
    print("\n")
    conn.close()

def check_column_uniqueness(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    unique_columns = []
    non_unique_columns = []

    total_rows = get_row_count(table_name)
    for column in columns:
        column_name = column[1]
        cursor.execute(f"SELECT COUNT(DISTINCT {column_name}) FROM {table_name};")
        distinct_count = cursor.fetchone()[0]
        if distinct_count == total_rows:
            unique_columns.append(column_name)
        else:
            non_unique_columns.append(column_name)

    conn.close()

    return unique_columns, non_unique_columns

if __name__ == "__main__":
    #unzip_shapefiles()
    #load_shapefiles_into_db()

    # Address Points Section
    print("Address points:")
    print("Address point count:", get_row_count("address_points"))
    print_table_details("address_points")
    
    # Property Boundaries Section
    print("Property boundaries:")
    print("Parcel count:", get_row_count("property_boundaries"))
    print_table_details("property_boundaries")

    # Check uniqueness for property_boundaries table
    property_boundaries_unique_cols, property_boundaries_non_unique_cols = check_column_uniqueness("property_boundaries")
    print("Columns with all values unique in property_boundaries:", property_boundaries_unique_cols)
    print("Columns without non-unique values in property_boundaries:", property_boundaries_non_unique_cols)
