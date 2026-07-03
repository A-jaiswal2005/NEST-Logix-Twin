# Logistics Digital Twin — Frontend

Single-file, dependency-free dashboard (`index.html`, vanilla JS + CSS).
Polls the backend's `/api/shipments` endpoint every 3 seconds and renders:

- A KPI strip: total shipments, active transits, delayed, delivered.
- A live fleet table with route, carrier, status chip, progress bar, and
  "time since last update".
- A scrolling event ticker that diffs each poll against the previous one and
  announces status changes as they happen (e.g. `SHP-1004 IN TRANSIT → DELAYED`).

## Run it

1. Make sure the backend is running (see `../backend/README.md`), by default
   at `http://localhost:8000`.
2. Open `index.html` directly in a browser, or serve it statically:

```bash
cd frontend
python -m http.server 5500
# then visit http://localhost:5500
```

## Pointing at a different backend

Edit the `API_BASE` constant near the top of the `<script>` block in
`index.html`:

```js
const API_BASE = "http://localhost:8000"; // change to your backend URL
```

No build step, no npm install — just edit and refresh.
