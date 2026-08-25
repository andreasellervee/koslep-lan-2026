# Koslep LAN 2026

Statistics from our Counter-Strike 2 LAN, and a static site to browse them.

**15 maps · 342 rounds · 10 players · 2 teams**

SVEN took the LAN **10–5** on maps, though the round count (174–168) and the
damage totals were far closer than that suggests — the two teams finished
within 17 damage of each other across the whole event.

## The site

A single static page split into five sections:

| Section      | What's in it                                                                                                                  |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| **Overview** | Final result, headline stats, LAN MVP, K/D podium, and 16 records & oddities                                                    |
| **Teams**    | Head-to-head totals, map records, per-map progression charts, round differential, side balance, best and worst maps            |
| **Players**  | 20-metric ranked comparison, two-stat scatter, multi-select radar, clutch & duel records, weapon specialists, sortable table   |
| **Entry duels** | Opening-kill conversion per map, and per player: rounds won after their entry kill vs. rounds won whenever they were in the opening duel |
| **Matches**  | All 15 maps with scores, halves and starting sides; expand any card for its full scoreboard                                    |

Built with Vue 3 and ECharts loaded from CDN. **No build step and no
`npm install`** — it is plain HTML, CSS and JavaScript.

### Running it locally

Open `site/index.html` directly in a browser, or serve the folder:

```bash
python3 -m http.server 4173 --directory site
```

Then visit <http://localhost:4173>.

### Deploying

**Vercel** — `vercel.json` sets the output directory to `site` with no build
command, so it deploys as-is.

**GitHub Pages** — `.github/workflows/deploy-pages.yml` publishes the `site/`
folder on every push to `main` that touches it. Enable it once under
**Settings → Pages → Build and deployment → Source: GitHub Actions**; branch
deployment is not used, because it can only serve the repo root or `/docs`.
All asset paths are relative, so the site works from a subpath like
`username.github.io/koslep-lan-2026/` without changes.

## Repository layout

```
consolidated_player_stats.json   LAN-wide totals, ~40 stats per player
match_scoreboards/               one file per map (15), per-player scoreboards
entry_stats/                     opening-duel data per map, down to round detail
player_avatars/                  Steam avatars, named <steamid64>.png

site/
  index.html                     markup and Vue templates
  css/styles.css                 stylesheet
  js/data.js                     GENERATED — do not hand-edit
  js/app.js                      Vue app: state, derived stats, chart options
  assets/avatars/                avatars served by the site

tools/
  build_data.py                  regenerates site/js/data.js
```

## Regenerating the data

`site/js/data.js` is derived from `consolidated_player_stats.json`,
`match_scoreboards/*.json` and `entry_stats/de_*.json`. After changing any of
them, run:

```bash
python3 tools/build_data.py
```

It writes a single `const LAN_DATA = {...}`, so the page also works when
opened straight from disk. The generated file **is** committed on purpose:
nothing builds it at deploy time.

## Notes on the data

Every per-map scoreboard total reconciles exactly with the consolidated file —
kills, deaths, assists, utility damage and round counts all match. Two things
are worth knowing:

- The **`rounds_won` field is wrong.** It reads 163–164 for every player,
  which contradicts the 174–168 the scoreboards record. The site uses the
  scoreboard figures throughout.
- **Some stats exist only as LAN-wide totals.** Entries, clutches, accuracy,
  MVP rounds, time alive and weapon splits have no per-map breakdown, so they
  appear as comparisons rather than trends. The per-map series are limited to
  kills, deaths, assists, ADR, headshot % and utility damage.

The **entry-duel numbers come from `entry_stats/`**, which records the opening
kill and opening death of every round. Two rounds (`de_cache` m14 r2,
`de_inferno` m10 r12) have no opening kill on record, so entry percentages use
340 as the denominator rather than 342.

Three derived metrics are worth spelling out, since the raw data doesn't
contain them:

- **Consistency** ("Mr Consistency" / "Most streaky") ranks players by the
  coefficient of variation of their per-map ADR — the standard deviation
  divided by their own average. Ranking on standard deviation alone would
  simply favour players with lower output and therefore less room to vary.
- **LAN MVP** is the ADR leader, which is not the same person as the player
  with the most MVP *rounds*. Both are shown.
- **Entry impact** (`INV→W%`) is rounds won across every opening duel a player
  was in, won or lost — not just the ones they won. Because each duel has one
  killer and one victim and exactly one side takes the round, it is zero-sum
  across the lobby and sits at exactly 50% LAN-wide, so it reads directly as
  above or below par. The companion `EK→W%` counts only their opening kills
  and is measured against the 67.4% LAN average.
