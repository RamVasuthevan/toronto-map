import json
import requests
import zipfile
from io import BytesIO
from typing import Dict
from pprint import pprint

LOBBY_ACTIVITY_FILE_NAME = "Lobbyist Registry Activity.zip"
OPEN_DATA_RESPONSE_FILE_NAME = "open-data-response.json"
API_BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
API_PACKAGE_SHOW_URL = API_BASE_URL + "/api/3/action/package_show"
API_PACKAGE_ID = "lobbyist-registry"


def get_package() -> Dict:
    """Returns response from Toronto Open Data CKAN API"""

    params = {"id": API_PACKAGE_ID}
    package = requests.get(API_PACKAGE_SHOW_URL, params=params).json()

    return package


def downdload_data():
    package = get_package()
    pprint(package)

    with open(OPEN_DATA_RESPONSE_FILE_NAME, "w") as json_file:
        json_file.write(json.dumps(package, indent=4))

    resource_response = {}
    for resource in package["result"]["resources"]:
        resource_response[
            f"{resource['name']}.{resource['format'].lower()}"
        ] = requests.get(resource["url"])

    for resource, response in resource_response.items():
        with open(resource, "wb") as f:
            f.write(response.content)

    lobbyactivity_zip = zipfile.ZipFile(
        BytesIO(resource_response[LOBBY_ACTIVITY_FILE_NAME].content)
    )
    lobbyactivity_zip.extractall()


if __name__ == "__main__":
    downdload_data()