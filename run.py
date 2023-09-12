from qgis.core import QgsApplication, QgsVectorLayer
import os

import zipfile
import os

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

# Extract the files
extract_zip(address_points_zip, address_points_dir)
extract_zip(property_boundaries_zip, property_boundaries_dir)



# Set environment variable for offscreen mode
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Supply path to qgis install location
QgsApplication.setPrefixPath("/usr/bin/qgis", True)

# Create a reference to the QgsApplication.
# Setting the second argument to False disables the GUI.
qgs = QgsApplication([], False)

# Initialize the QgsApplication
qgs.initQgis()

# Define the path to your first shapefile
property_boundaries_shapefile = "Property Boundaries (wgs84) - shapefile/PROPERTY_BOUNDARIES_WGS84.shp"
# Define the path to your second shapefile
municipal_address_points_shapefile = "Municipal address points (wgs84) - shapefile/ADDRESS_POINT_WGS84.shp"

# Load your first shapefile
layer1 = QgsVectorLayer(property_boundaries_shapefile, "Property Boundaries", "ogr")
# Load your second shapefile
layer2 = QgsVectorLayer(municipal_address_points_shapefile, "Municipal Address Points", "ogr")

if not layer1.isValid():
    print("Failed to load the Property Boundaries!")
    print(layer1.error().message())
else:
    # Extract counts for each F_TYPE value
    print("Property Boundaries:")
    
    feature_count = layer1.featureCount()
    print(f"Number of features (e.g., property boundaries): {feature_count}")

    fields = layer1.fields()
    column_names = [field.name() for field in fields]
    print("Columns:", ", ".join(column_names))
    print("")


    f_type_counts = {}
    for feature in layer1.getFeatures():
        value = feature['F_TYPE']
        f_type_counts[value] = f_type_counts.get(value, 0) + 1

    print("Counts for each F_TYPE value in Property Boundaries")
    for key, value in f_type_counts.items():
        print(f"{key}: {value}")
    print("")

print("")
if not layer2.isValid():
    print("Failed to load the Municipal Address Points!")
    print(layer2.error().message())
else:
    print("Municipal Address Points:")

    feature_count = layer1.featureCount()
    print(f"Number of features (e.g., address points): {feature_count}")


    # List the columns (fields) from the second file
    fields = layer2.fields()
    column_names = [field.name() for field in fields]
    print("Columns:", ", ".join(column_names))
    print("")

    f_type_counts = {}
    for feature in layer2.getFeatures():
        value = feature['MAINT_STAG']
        f_type_counts[value] = f_type_counts.get(value, 0) + 1

    print("Counts for each MAINT_STAG value in Property Boundaries")
    for key, value in f_type_counts.items():
        print(f"{key}: {value}")
    print("")

    # FCODE and FCODE_DES are Unkown

    # Get field indices for the columns you want to remove
    field_ids = []
    fields = layer2.fields()
    for field_name in ["FCODE", "FCODE_DES"]:
        field_id = fields.lookupField(field_name)
        if field_id != -1:  # If the field is found
            field_ids.append(field_id)

    # Start editing the layer
    layer2.startEditing()

    # Remove fields
    layer2.deleteAttributes(field_ids)

    # Commit changes and stop editing
    layer2.commitChanges()

    # Update column names after removing fields
    fields = layer2.fields()
    column_names = [field.name() for field in fields]

    print("\nSaving all records in the second file to test.csv...")

    # Open file for writing
    with open("test.csv", "w") as csvfile:

        # Write headers
        header_str = ",".join(column_names)
        csvfile.write(header_str + "\n")  # Writing the headers to the file

        # Write records
        for feature in layer2.getFeatures():
            values = [str(feature[col]).replace(",", ";") for col in column_names]  # replace commas in the data with semicolons to prevent issues
            csvfile.write(",".join(values) + "\n")  # Writing each row to the file

    print("Data has been saved to test.csv.")


