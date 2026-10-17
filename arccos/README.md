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
