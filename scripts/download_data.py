import os
import json
import requests
import zipfile
import shutil
from io import BytesIO
from typing import Dict, List
from urllib.parse import urlparse, unquote  # Import urlparse and unquote from urllib.parse
from pprint import pprint

API_BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
API_PACKAGE_SHOW_URL = API_BASE_URL + "/api/3/action/package_show"
API_PACKAGE_IDS = ["property-boundaries", "address-points-municipal-toronto-one-address-repository"]

# Flag to decide whether to unzip the downloaded zip files
UNZIP_FILES = False


def get_package(package_id: str) -> Dict:
    """Returns response from Toronto Open Data CKAN API"""
    params = {"id": package_id}
    package = requests.get(API_PACKAGE_SHOW_URL, params=params).json()
    return package


def extract_zip(resource: str, package_id: str):
    """Extracts the contents of a zip file"""
    with open(resource, "rb") as f:
        zip_file = zipfile.ZipFile(BytesIO(f.read()))
        zip_file.extractall(path=package_id)


def download_data(package_ids: List[str], unzip_files: bool = True):
    for package_id in package_ids:
        # Delete the directory for the package if it exists
        if os.path.exists(package_id):
            shutil.rmtree(package_id)
        
        package = get_package(package_id)
        pprint(package)

        # Create a directory for the package if it doesn't exist
        if not os.path.exists(package_id):
            os.makedirs(package_id)

        open_data_response_file_name = os.path.join(package_id, f"{package_id}-open-data-response.json")
        with open(open_data_response_file_name, "w") as json_file:
            json_file.write(json.dumps(package, indent=4))

        resource_response = {}
        for resource in package["result"]["resources"]:
            # Extract the correct file name and extension from the URL
            url_path = urlparse(unquote(resource['url'])).path
            file_name = os.path.basename(url_path)
            file_path = os.path.join(package_id, file_name)  # Save the resource in the package directory
            resource_response[file_path] = requests.get(resource["url"])

        for resource, response in resource_response.items():
            with open(resource, "wb") as f:
                f.write(response.content)

            if unzip_files and resource.endswith(".zip"):
                extract_zip(resource, package_id)  # Extract the zip file contents into the package directory


if __name__ == "__main__":
    download_data(API_PACKAGE_IDS, unzip_files=False)
