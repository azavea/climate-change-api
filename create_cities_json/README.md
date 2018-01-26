# create_cities_json.py

`create_cities_json.py` takes a geonames `US.txt`file and a CSV file of city and states (`New York,NY`, `Philadelphia,PA`), and outputs `cities.geojson` which is a GeoJSON file suitable for import into `climate-change-api`.

geonames data can be found at http://download.geonames.org/export/dump/. `US.zip` contains the `US.txt` file required to extract US cities.

## Example Usage

`./create_cities_json.py US.txt iclei_places.csv`
