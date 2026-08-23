# Koslep LAN 2026 — site

This folder is the deployable site: plain HTML, CSS and JavaScript with no
build step. Open `index.html` directly, or serve the folder:

```bash
python3 -m http.server 4173 --directory site
```

`js/data.js` is generated — edit `../tools/build_data.py` and re-run it from
the repo root rather than editing that file by hand:

```bash
python3 tools/build_data.py
```

See the [repository README](../README.md) for the full project documentation,
deployment instructions and notes on the data.
