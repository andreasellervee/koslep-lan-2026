# Koslep LAN 2026

Static stat site for the CS2 LAN. No build step, no `npm install`: it is plain
HTML, CSS and JavaScript, so you can open it or deploy it as-is.

## Run it locally

Because the page fetches nothing over `fetch()`, you can just open
`site/index.html` in a browser. To serve it properly instead:

```bash
python3 -m http.server 4173 --directory site
```

Then visit <http://localhost:4173>.

## Layout

```
site/
  index.html          markup + Vue templates for all four sections
  css/styles.css      the whole stylesheet (broadcast dark theme)
  js/data.js          GENERATED — do not hand-edit
  js/app.js           Vue app: state, computed stats, ECharts options
  assets/avatars/     Steam avatars, named <steamid64>.png
tools/
  build_data.py       regenerates js/data.js from the raw JSON
```

## Regenerating the data

`site/js/data.js` is generated from `consolidated_player_stats.json` and
`match_scoreboards/*.json` in the repo root. After changing either, run:

```bash
python3 tools/build_data.py
```

It emits a single `const LAN_DATA = {...}` so the page works from `file://`
as well as over HTTP.

## Dependencies

Vue 3 and ECharts load from jsDelivr in `index.html`. To vendor them instead so
the site works with no network at all:

```bash
mkdir -p site/vendor && curl -L -o site/vendor/vue.global.prod.js https://cdn.jsdelivr.net/npm/vue@3.5.13/dist/vue.global.prod.js && curl -L -o site/vendor/echarts.min.js https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js
```

Then swap the two `<script src="https://cdn.jsdelivr.net/...">` tags at the
bottom of `index.html` for `vendor/vue.global.prod.js` and
`vendor/echarts.min.js`.

## Deploying

**Vercel** — point a project at this repo and set the output directory to
`site`. There is no build command. A `vercel.json` is included that does this
for you.

**GitHub Pages** — either set Pages to serve the `site/` folder from your
default branch, or move the contents of `site/` to the repo root. All asset
paths are relative, so it works from a subpath like
`username.github.io/repo/` without changes.

## Data notes

Every per-map scoreboard total reconciles exactly with the consolidated file
(kills, deaths, assists, utility damage, round counts). Two things to know:

- The `rounds_won` field in `consolidated_player_stats.json` reads 163–164 for
  every player, which contradicts the 174–168 the scoreboards record. The site
  uses the scoreboard figures.
- Entries, clutches, accuracy, MVPs and weapon splits exist only as LAN-wide
  totals, so they appear as comparisons rather than per-map trends. The
  per-map series are limited to K, D, A, ADR, HS% and utility damage.
