import os
import sqlite3
import zipfile
import subprocess
from itertools import zip_longest

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

def print_table(headers, rows, note=None):
    """Utility function to print a table"""
    rows = list(rows)
    col_widths = [max(len(str(item)) for item in col) for col in zip(*([headers] + rows))]
    separator = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
    header_line = "|" + "|".join(f" {header:<{col_widths[idx]}} " for idx, header in enumerate(headers)) + "|"

    print(separator)
    print(header_line)
    print(separator)

    for row in rows:
        row = [(cell if cell != '' else ' ') for cell in row]  # Replace empty strings with a single space
        print("|" + "|".join(f" {cell:<{col_widths[idx]}} " for idx, cell in enumerate(row)) + "|")
    print(separator)

    if note:
        print(note)
    print("\n")


def print_table_details(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()

    headers = ["Column Name", "Type"]
    rows = [(col[1], col[2]) for col in columns]

    note = None
    if any(col[1] == 'pk_uid' for col in columns):
        note = "Note: The 'pk_uid' column is a primary key column typically added during the import process for unique identification."
    
    print_table(headers, rows, note)

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

    # Ensure that the non-unique columns list isn't empty for the table display
    if not property_boundaries_non_unique_cols:
        property_boundaries_non_unique_cols.append("N/A")
    
    print("Columns in property_boundaries:")
    print_table(["Unique Columns", "Non-unique Columns"],list(zip_longest(property_boundaries_unique_cols, property_boundaries_non_unique_cols,fillvalue="")))

