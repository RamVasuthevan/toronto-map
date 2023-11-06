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
    columns = [col[1] for col in cursor.fetchall()]

    # Prepare a single SQL query to get distinct counts for all columns
    distinct_counts_query = ", ".join(f"COUNT(DISTINCT {col}) AS {col}" for col in columns)
    cursor.execute(f"SELECT {distinct_counts_query} FROM {table_name};")
    distinct_counts = cursor.fetchone()

    total_rows = get_row_count(table_name)

    unique_columns = [col for idx, col in enumerate(columns) if distinct_counts[idx] == total_rows]
    non_unique_columns = [col for idx, col in enumerate(columns) if distinct_counts[idx] != total_rows]

    conn.close()

    return unique_columns, non_unique_columns


def display_column_uniqueness(table_name):
    """
    Check the uniqueness of each column in the provided table and display the results.
    """
    unique_cols, non_unique_cols = check_column_uniqueness(table_name)
    
    print(f"Columns in {table_name}:")
    print_table(["Unique Columns", "Non-unique Columns"], 
                list(zip_longest(unique_cols, non_unique_cols, fillvalue="")))
    print("\n")

def display_column_values_and_counts(table_name, column_name):
    """
    Fetch and display unique values and their counts for a specific column in the given table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT {column_name}, COUNT(*) as count FROM {table_name} GROUP BY {column_name} ORDER BY count DESC;")
    rows = cursor.fetchall()
    
    headers = [column_name, "Count"]
    
    print(f"Unique values and counts for column '{column_name}' in table '{table_name}':")
    print_table(headers, rows)
    
    conn.close()

def display_frequency_distribution(table_name, column_name):
    """
    Fetch and display the frequency distribution for a specific column in the given table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get unique values and their counts for the specified column
    cursor.execute(f"SELECT {column_name}, COUNT(*) as count FROM {table_name} GROUP BY {column_name} ORDER BY count DESC;")
    rows = cursor.fetchall()
    
    headers = [column_name, "Frequency"]
    
    print(f"Frequency distribution for column '{column_name}' in table '{table_name}':")
    print_table(headers, rows)
    
    conn.close()

def display_frequency_of_frequency(table_name, column_name):
    """
    Fetch and display the frequency of frequency for a specific column in the given table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get the frequency of each unique value in the column
    cursor.execute(f"SELECT {column_name}, COUNT(*) as freq FROM {table_name} GROUP BY {column_name};")
    frequencies = [row[1] for row in cursor.fetchall()]
    
    # Calculate the frequency of each frequency
    freq_of_freq = {}
    for freq in frequencies:
        freq_of_freq[freq] = freq_of_freq.get(freq, 0) + 1

    sorted_freq_of_freq = sorted(freq_of_freq.items(), key=lambda x: x[1], reverse=True)
    
    headers = ["Frequency", "Count of Occurrence"]
    
    print(f"Frequency of frequency for column '{column_name}' in table '{table_name}':")
    print_table(headers, sorted_freq_of_freq)
    
    conn.close()

def delete_columns_from_table(table_name, columns_to_delete):
    """
    Delete specified columns from a table.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch existing columns
    cursor.execute(f"PRAGMA table_info({table_name});")
    all_columns = [col[1] for col in cursor.fetchall()]

    # Determine columns to keep
    columns_to_keep = [col for col in all_columns if col not in columns_to_delete]

    # Create a new temporary table without the columns to delete
    columns_str = ', '.join(columns_to_keep)
    cursor.execute(f"CREATE TABLE {table_name}_temp AS SELECT {columns_str} FROM {table_name};")

    # Drop the original table
    cursor.execute(f"DROP TABLE {table_name};")

    # Rename the temporary table to the original table's name
    cursor.execute(f"ALTER TABLE {table_name}_temp RENAME TO {table_name};")

    conn.commit()
    conn.close()

    print(f"Columns {', '.join(columns_to_delete)} deleted from {table_name}.")


def fetch_mixed_addresses():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Define the queries for each criteria
    queries = {
        "Shortest Addresses": "SELECT address FROM address_points ORDER BY LENGTH(address) ASC LIMIT 2;",
        "Longest Addresses": "SELECT address FROM address_points ORDER BY LENGTH(address) DESC LIMIT 2;",
        "Addresses with Dashes": "SELECT address FROM address_points WHERE address LIKE '%-%' LIMIT 2;",
        "Addresses with Slashes": "SELECT address FROM address_points WHERE address LIKE '%/%' LIMIT 2;",
        "Addresses with Letters": "SELECT address FROM address_points WHERE address GLOB '*[a-zA-Z]*' LIMIT 2;"
    }

    # Fetch addresses based on each criteria and collate them
    mixed_addresses = []
    for key, query in queries.items():
        cursor.execute(query)
        results = cursor.fetchall()
        for address in results:
            mixed_addresses.append((key, address[0]))

    conn.close()
    return mixed_addresses

def display_mixed_addresses():
    addresses = fetch_mixed_addresses()
    headers = ["Criteria", "Address"]
    print_table(headers, addresses)

    
if __name__ == "__main__":
    # Uncomment the next two lines if you're importing the shapefiles for the first time
    # unzip_shapefiles()
    # load_shapefiles_into_db()

    # Address Points Section
    print("Address points:")
    print("Address point count:", get_row_count("address_points"))
    print_table_details("address_points")
    display_column_uniqueness("address_points")

    print("Delete legacy columns: FCODE and FCODE_DES")
    delete_columns_from_table("address_points", ["FCODE", "FCODE_DES"])
    print()

    print("GEO_ID: unique geographic identifier")

    print("LINK: geo_id of the primary address")
    # Fetch and display the frequency of frequency for 'link' in 'address_points'
    display_frequency_of_frequency("address_points", "link")

    print("ADDRESS: address number with suffix")
    print("Select address values")
    display_mixed_addresses()

    print("LFNAME: LINEAR_NAME_FULL (Street Name)")
    

    # Fetch and display unique values and their counts for 'maint_stag' in 'address_points'
    display_frequency_distribution("address_points", "maint_stag")

    # Fetch and display unique values and their counts for 'mun_name' in 'address_points'
    display_frequency_distribution("address_points", "mun_name")

    # Fetch and display unique values and their counts for 'ward_name' in 'address_points'
    display_frequency_distribution("address_points", "ward_name")
    
    # Property Boundaries Section
    print("Property boundaries:")
    print("Parcel count:", get_row_count("property_boundaries"))
    print_table_details("property_boundaries")
    display_column_uniqueness("property_boundaries")

    # Fetch and display unique values and their counts for 'f_type' in 'property_boundaries'
    display_column_values_and_counts("property_boundaries", "f_type")