# Arccos data proof of concept (Crawl4AI)

Pulls your own data from the Arccos web dashboard. You log in once by hand;
the script re-uses that saved browser session. Your password never goes in code.

## Setup (once)

    cd arccos
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    crawl4ai-setup            # installs the browser Crawl4AI uses

## Run

    python arccos_poc.py login    # browser opens: log in to Arccos, then press q in the terminal
    python arccos_poc.py fetch    # loads the dashboard headless and saves data

You can pass specific dashboard pages to `fetch`, e.g.

    python arccos_poc.py fetch https://dashboard.arccosgolf.com/rounds

## Output

- `output/*.md`: readable text of each page
- `output/api/*.json`: every JSON response the dashboard loaded. Your rounds
  and stats should be in here. Check the `url` field in each file to see which
  Arccos API endpoint returned it. Once you know the endpoints, you can call
  them directly later without a browser.

If the `.md` file looks like a login page, your session expired. Run `login` again.

## Faster: export everything straight from the API

Once logged in, the dashboard stores two cookies on dashboard.arccosgolf.com:
`access_token` and `user_id`. Put them in `auth.json`:

    {"access_token": "...", "user_id": "..."}

Then:

    python arccos_export.py auth.json export

This writes `rounds.csv`, `holes.csv`, `shots.csv` (club, distance, GPS
start/end for every shot), `clubs.csv`, plus raw JSON for strokes gained and
smart distances. No browser needed. Never commit `auth.json`.

## Course map to GSPro (OPCD)

`arccos_to_opcd.py` turns Arccos hole maps (`/courses/{id}/holes/{n}?courseVersion={v}`)
into an OPCD-coloured SVG (1 mm = 1 m, UTM, one Inkscape layer per surface),
a GeoJSON of every shape, and the UTM bounds to line it up with Lidar.

    python arccos_to_opcd.py export/holes 6878 4 tedesco opcd 32619

Arccos shape types (from the Arccos dashboard's own lookup): 1 Green, 2/3 Sand
Trap, 4/5 Water, 6 Tee, 7 Fairway, 8 Fairway Center, 9 Trees, 10 Bounding Box,
11 No Shot, 12 Out Of Bounds. Colours follow csites/osm2svg4opcd `styles.json`.
The map data belongs to Arccos: keep builds from it for personal use.
