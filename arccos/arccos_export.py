"""Export all your Arccos data straight from the Arccos API.

Needs a token file (default: auth.json) like:
    {"access_token": "...", "user_id": "..."}
Both values are cookies on dashboard.arccosgolf.com once you are logged in
(cookie names: access_token, user_id). The token expires, so grab a fresh
one if you get a 401 error.

Usage:  python arccos_export.py [auth.json] [output_dir]

Writes JSON (raw API responses) and CSV files (rounds, holes, shots, clubs).
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.arccosgolf.com"


def main():
    auth_path = Path(sys.argv[1] if len(sys.argv) > 1 else "auth.json")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "export")
    auth = json.loads(auth_path.read_text())
    token = urllib.parse.unquote(auth["access_token"])
    uid = urllib.parse.unquote(auth["user_id"])
    (out / "rounds").mkdir(parents=True, exist_ok=True)

    def get(path):
        req = urllib.request.Request(
            API + path,
            headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    def save(name, data):
        (out / name).write_text(json.dumps(data, indent=2))
        return data

    user = save("user.json", get(f"/users/{uid}"))
    save("player_profile.json", get(f"/sga/playerProfile/{uid}"))
    save("strokes_gained_last20.json", get(f"/sga/getDashboardAnalysis/{uid}?goalHcp=0&noOfRounds=20"))
    save("smart_distances.json", get(f"/v4/clubs/user/{uid}/smart-distances?numberOfShots=100&units=IMPERIAL"))
    bag = save("bag.json", get(f"/users/{uid}/bags/{user['bagId']}"))

    # Round list (paged)
    rounds, offset = [], 0
    while True:
        page = get(f"/v2/users/{uid}/rounds?limit=50&offSet={offset}&roundType=flagship")
        rounds += page["rounds"]
        offset += 50
        if offset >= page["totalCount"] or not page["rounds"]:
            break
    save("rounds.json", rounds)
    print(f"{len(rounds)} rounds")

    # Full detail for each round (holes + shots), cached on disk
    holes_rows, shot_rows = [], []
    for i, r in enumerate(rounds, 1):
        f = out / "rounds" / f"{r['roundId']}.json"
        if f.exists():
            detail = json.loads(f.read_text())
        else:
            detail = get(f"/users/{uid}/rounds/{r['roundId']}")
            f.write_text(json.dumps(detail, indent=2))
            time.sleep(0.3)  # be polite
        for h in detail.get("holes") or []:
            if not h:
                continue
            holes_rows.append({"roundId": r["roundId"], "date": r["startTime"][:10],
                               "course": r["courseName"],
                               **{k: v for k, v in h.items() if k != "shots"}})
            for s in h.get("shots") or []:
                shot_rows.append({"roundId": r["roundId"], "date": r["startTime"][:10],
                                  "course": r["courseName"], "holeId": h["holeId"], **s})
        print(f"\r{i}/{len(rounds)} rounds downloaded", end="", flush=True)
    print()

    clubs = {c["clubId"]: c for c in bag["clubs"]}
    for s in shot_rows:
        c = clubs.get(s.get("clubId"), {})
        s["clubMake"] = c.get("clubMakeOther")
        s["clubModel"] = c.get("clubModelOther")

    write_csv(out / "rounds.csv", rounds)
    write_csv(out / "holes.csv", holes_rows)
    write_csv(out / "shots.csv", shot_rows)
    write_csv(out / "clubs.csv", bag["clubs"])
    print(f"Done: {len(holes_rows)} holes, {len(shot_rows)} shots -> {out}/")


def write_csv(path, rows):
    if not rows:
        return
    cols = list(dict.fromkeys(k for r in rows for k in r if not isinstance(r[k], (list, dict))))
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
