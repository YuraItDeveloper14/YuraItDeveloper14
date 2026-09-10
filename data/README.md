# Map data

`map_layers.json` is the ASCII map the card is drawn from: three layers of the same
grid — the country, the Kyiv oblast and the city of Kyiv. It is a rendering of
OpenStreetMap data, © OpenStreetMap contributors, available under the Open Database
Licence: https://www.openstreetmap.org/copyright

- oblast outlines: `UA_FULL_Ukraine.geojson` from github.com/EugeneBorshch/ukraine_geojson
- the city of Kyiv: OSM relation 421866, fetched from Nominatim

To rebuild the layers, download both files and run

```
python scripts/card.py --oblasts UA_FULL_Ukraine.geojson --city kyiv.geojson
```

Rebuilding needs Pillow; drawing the SVGs from the layers needs nothing beyond Python.
