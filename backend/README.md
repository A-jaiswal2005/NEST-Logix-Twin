# Logistics Digital Twin — Backend

FastAPI service that simulates a live shipment feed in memory and exposes it
over REST. A background task mutates shipment state every few seconds
(status transitions, progress, timestamps), so repeated polling shows real
movement — no database required.

## Run it

```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`.

## Endpoints

| Method | Path             | Description                                   |
|--------|------------------|------------------------------------------------|
| GET    | `/api/shipments` | Full live list of tracked shipments            |
| GET    | `/api/kpis`      | Aggregate counts (total/active/delayed/etc.)   |
| GET    | `/docs`          | Interactive Swagger UI (auto-generated)        |

## Notes

- State is in-memory and resets on restart — this is a simulation, not a
  persistent store.
- CORS is wide open (`allow_origins=["*"]`) to make local frontend
  development painless. Restrict this before deploying anywhere real.
- Tune `NUM_SHIPMENTS` and `TICK_SECONDS` in `main.py` to change fleet size
  and simulation speed.
