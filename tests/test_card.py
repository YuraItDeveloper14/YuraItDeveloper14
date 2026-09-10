"""The profile card: the map layers agree with each other and the SVGs match their source."""
import json
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
LAYERS = json.loads((ROOT / "data" / "map_layers.json").read_text(encoding="utf-8"))
NAMES = ("base", "region", "city")
SVG = "{http://www.w3.org/2000/svg}"


def cells(layer):
    return {(x, y) for y, row in enumerate(layer) for x, ch in enumerate(row) if ch != " "}


def test_layers_share_one_grid():
    assert len({len(LAYERS[n]) for n in NAMES}) == 1
    assert len({len(row) for n in NAMES for row in LAYERS[n]}) == 1


def test_layers_never_overlap():
    base, region, city = (cells(LAYERS[n]) for n in NAMES)
    assert not base & region
    assert not base & city
    assert not region & city


def neighbours(x, y):
    return {(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)}


def test_the_oblast_is_filled_not_outlined():
    region, city = cells(LAYERS["region"]), cells(LAYERS["city"])
    inside = [c for c in region if neighbours(*c) <= region | city]
    assert len(inside) > len(region) / 2


def test_kyiv_sits_inside_its_oblast():
    region, city = cells(LAYERS["region"]), cells(LAYERS["city"])
    assert city, "the city of Kyiv is drawn"
    for x, y in city:
        assert neighbours(x, y) <= region | city, f"city cell {(x, y)} touches the outside of the oblast"


@pytest.mark.parametrize("script", ["card.py", "typing_line.py"])
def test_svgs_match_their_source(script):
    def snapshot():
        return {p.name: p.read_bytes().replace(b"\r\n", b"\n") for p in (ROOT / "assets").glob("*.svg")}

    before = snapshot()
    subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True, cwd=ROOT,
                   capture_output=True)
    assert snapshot() == before, f"assets are stale: run scripts/{script} and commit"


def test_card_shows_the_four_facts():
    texts = {t.text for t in ET.parse(ROOT / "assets" / "card-dark.svg").iter(SVG + "text")}
    for label in ("Name", "Age", "Location", "Role"):
        assert label in texts
    assert "Handle" not in texts
    assert "Portfolio" not in texts
