"""Turn an Arccos course map into files for a GSPro (OPCD) course build.

Input: the hole files saved from the Arccos API
    (/courses/{courseId}/holes/{n}?courseVersion={v}), one JSON per hole,
    named {courseId}_{version}_{hole}.json.

Output (in out_dir):
    <name>_opcd.svg      surfaces as filled shapes, one Inkscape layer per
                         surface, OPCD colours, 1 SVG mm = 1 metre, north up
    <name>_shapes.geojson every shape in WGS84 with hole, Arccos type and
                         OPCD class (for lining up with Lidar in QGIS)
    <name>_bounds.json   UTM bounds of the SVG, to match your Lidar/GeoTIFF

Usage:
    python arccos_to_opcd.py holes_dir course_id version name out_dir [epsg]

Default projection is UTM zone 19N (EPSG:32619), right for eastern
Massachusetts. Use the EPSG your Lidar tiles are in.

Colours follow csites/osm2svg4opcd styles.json (the OPCD colour scheme).
"""

import glob
import json
import sys
from pathlib import Path

from pyproj import Transformer

# Arccos feature types, from the Arccos web dashboard's own lookup table
ARCCOS = {
    1: "Green", 2: "Sand Trap", 3: "Sand Trap (by green)", 4: "Water",
    5: "Water (by green)", 6: "Tee", 7: "Fairway", 8: "Fairway Center",
    9: "Trees", 10: "Bounding Box", 11: "No Shot", 12: "Out Of Bounds",
}
# Arccos type -> OPCD class, fill colour, stacking order (low draws first)
OPCD = {
    7: ("golf.fairway", "#43E561", 60),
    6: ("golf.tee", "#A0E5B8", 70),
    9: ("natural.wood", "#164B20", 80),
    1: ("golf.green", "#BCE5A4", 90),
    2: ("golf.bunker", "#E5E5AA", 100),
    3: ("golf.bunker", "#E5E5AA", 100),
    4: ("golf.water_hazard", "#0000C0", 110),
    5: ("golf.water_hazard", "#0000C0", 110),
}
ROUGH = ("leisure.golf_course", "#278438")  # base layer under everything
MARGIN_M = 40  # rough around the outermost shapes


def main():
    holes_dir, course_id, version, name, out_dir = sys.argv[1:6]
    epsg = int(sys.argv[6]) if len(sys.argv) > 6 else 32619
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    to_utm = Transformer.from_crs(4326, epsg, always_xy=True)

    shapes = []
    for f in sorted(glob.glob(f"{holes_dir}/{course_id}_{version}_*.json"),
                    key=lambda p: int(Path(p).stem.split("_")[-1])):
        hole = json.loads(Path(f).read_text())
        for i, feat in enumerate(hole["features"]):
            t = feat["featureId"]
            ll = [(c["longitude"], c["latitude"]) for c in feat["coordinates"]]
            if len(ll) < 3:
                continue
            shapes.append({
                "hole": hole["holeId"], "par": hole.get("mensPar"), "index": i, "type": t,
                "lonlat": ll, "utm": [to_utm.transform(x, y) for x, y in ll],
            })
    if not shapes:
        sys.exit("No hole files found")

    # GeoJSON of everything, including types OPCD doesn't need
    gj = {"type": "FeatureCollection", "features": []}
    for s in shapes:
        cls = OPCD.get(s["type"])
        ring = s["lonlat"] + [s["lonlat"][0]]
        gj["features"].append({
            "type": "Feature",
            "properties": {"hole": s["hole"], "par": s["par"], "arccos_type": s["type"],
                           "arccos_name": ARCCOS.get(s["type"], "Unknown"),
                           "opcd_class": cls[0] if cls else None, "fill": cls[1] if cls else None},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })
    (out / f"{name}_shapes.geojson").write_text(json.dumps(gj))

    # SVG: 1 unit = 1 m, x = easting, y = northing flipped so north is up
    used = [s for s in shapes if s["type"] in OPCD]
    xs = [x for s in used for x, _ in s["utm"]]
    ys = [y for s in used for _, y in s["utm"]]
    minx, maxx = min(xs) - MARGIN_M, max(xs) + MARGIN_M
    miny, maxy = min(ys) - MARGIN_M, max(ys) + MARGIN_M
    w, h = maxx - minx, maxy - miny

    def path(s):
        pts = [f"{x - minx:.2f},{maxy - y:.2f}" for x, y in s["utm"]]
        return "M" + " L".join(pts) + " Z"

    layers = {}
    for s in used:
        cls, fill, z = OPCD[s["type"]]
        layers.setdefault((z, cls, fill), []).append(s)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
        f'width="{w:.2f}mm" height="{h:.2f}mm" viewBox="0 0 {w:.2f} {h:.2f}">',
        f'<!-- {name}: from Arccos course {course_id} v{version}. EPSG:{epsg}. '
        f'Top-left = ({minx:.2f} E, {maxy:.2f} N). 1 unit = 1 m. -->',
        f'<g inkscape:groupmode="layer" id="layer-rough" inkscape:label="{ROUGH[0]}">',
        f'<rect id="{ROUGH[0]}-0" x="0" y="0" width="{w:.2f}" height="{h:.2f}" fill="{ROUGH[1]}" stroke="none"/>',
        "</g>",
    ]
    for (z, cls, fill), group in sorted(layers.items()):
        lines.append(f'<g inkscape:groupmode="layer" id="layer-{cls}" inkscape:label="{cls}">')
        for s in group:
            lines.append(f'<path id="{cls}-hole{s["hole"]}-{s["index"]}" d="{path(s)}" '
                         f'fill="{fill}" stroke="none" fill-rule="evenodd"/>')
        lines.append("</g>")
    lines.append("</svg>")
    (out / f"{name}_opcd.svg").write_text("\n".join(lines))

    (out / f"{name}_bounds.json").write_text(json.dumps({
        "epsg": epsg, "min_easting": minx, "max_easting": maxx, "min_northing": miny, "max_northing": maxy,
        "width_m": w, "height_m": h, "svg_units": "1 mm = 1 m", "margin_m": MARGIN_M,
    }, indent=2))

    counts = {}
    for s in used:
        counts[OPCD[s["type"]][0]] = counts.get(OPCD[s["type"]][0], 0) + 1
    print(f"{len(used)} shapes in SVG ({w:.0f} x {h:.0f} m):", counts)
    print("skipped types:", sorted({ARCCOS.get(s['type']) for s in shapes if s['type'] not in OPCD}))


if __name__ == "__main__":
    main()
