# Arccos project notes

Where things stand, so work can pick up in a new session.

## Getting data out of Arccos

- Login: dashboard.arccosgolf.com, "Send Login Link". Opening the emailed link in
  a browser sets cookies `access_token` and `user_id`. Put them in `auth.json`
  (never commit it). Tokens expire; request a new link when calls return 401.
- API base `https://api.arccosgolf.com`, header `Authorization: Bearer <access_token>`.

| What | Endpoint |
| --- | --- |
| User, bag id | `/users/{uid}` |
| Rounds list | `/v2/users/{uid}/rounds?limit=50&offSet=0&roundType=flagship` |
| Round detail (holes, shots, GPS) | `/users/{uid}/rounds/{roundId}` |
| Strokes gained | `/sga/getDashboardAnalysis/{uid}?goalHcp=0&noOfRounds=20` (or `&roundId=`) |
| Player profile | `/sga/playerProfile/{uid}` |
| Club distances | `/v4/clubs/user/{uid}/smart-distances?numberOfShots=100&units=IMPERIAL` |
| Bag | `/users/{uid}/bags/{bagId}` |
| Course | `/courses/{courseId}?courseVersion={v}` |
| Hole map (par, tees, shapes, elevation) | `/courses/{courseId}/holes/{n}?courseVersion={v}` |

Gotchas:
- Hole score = `noOfShots` (shots + penalty strokes).
- Tee `distance` in hole maps is METRES (no API option for yards); multiply by 1.0936 for yards.
- Holed shots have no end GPS; use the pin (`pinLat`/`pinLong` on the hole).
- Round category "handicaps" use negative = regular handicap, positive = plus.
  Averaging them per round is misleading; use the SGA endpoint instead.
- Club type 1 = driver, 12 = putter, 40+ = wedge loft. Irons 5–11 are codes,
  mapping to iron numbers not confirmed.

Map shape types (from the Arccos dashboard's own code): 1 Green, 2 Sand Trap,
3 Sand Trap by green, 4 Water, 5 Water by green, 6 Tee, 7 Fairway,
8 Fairway Center, 9 Trees, 10 Bounding Box, 11 No Shot, 12 Out Of Bounds.
Anything outside the shapes is rough.

Elevation: 512 points per hole on a ~5 m grid in a ~35 m strip down the hole.
Good for a height check, not for terrain.

## Scripts

- `arccos_poc.py`: Crawl4AI proof of concept (login profile + capture JSON).
- `arccos_export.py`: full export to CSV/JSON.
- `arccos_to_opcd.py`: course map to GSPro/OPCD SVG + GeoJSON.
- `analysis/`: Tedesco scripts. Run from a folder holding `export/` and `auth.json`:
  `fetch_holes.py` (hole maps), `tedesco.py` (hole dataset), `ted_analyze.py`,
  `ted2.py` (findings), `ted_export.py` (dashboard tables), `ted_map.py`
  (map shapes + shots for the hole-map viewer).

## Tedesco findings (67 rounds, Apr 2024 – Oct 2026)

- 100–200 yd approaches: 73% of missed greens finish short, average 15 yd short.
- Par 3s: hole 7 plays 219 yd to the pin; clubs hit there average 26 yd too
  short; 13% greens. Holes 3 and 13 finish ~18 yd short.
- 20–40 yd off the green: 15% up and down (62% inside 10 yd).
- Double bogey or worse on 15% of holes = 42% of strokes over par; worst on 16, 15.
- Driver is fine: missed fairway costs ~0.13 strokes; 3% tee penalties.

## Artifacts

- Dashboard: https://claude.ai/artifact/Bft7b4AawT2woNiLCtQ5Y4
- GSPro build plan: https://claude.ai/artifact/Qqft4FVZmSqxZtxoRQD7te
- Build log (scorecard, renders, findings): https://claude.ai/artifact/5NHyUhWuUHzEf1gcJDf2o8

## Next steps (GSPro build)

1. Send the clipped image's EPSG code and extent from QGIS.
2. Re-export the SVG/GeoJSON in that CRS and frame
   (`arccos_to_opcd.py ... <epsg>`; framing to an extent still to add).
3. Export elevation strips as XYZ; build a GreenKeeper sheet (par, tees, pins).
