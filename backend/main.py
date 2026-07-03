"""
Logistics Network Digital Twin — Backend
=========================================
FastAPI service that simulates a live stream of shipments moving across a
global network. State lives in memory and is mutated by a background
asyncio task, so every poll of /api/shipments reflects the network "as of
right now" — exactly what a digital twin should do.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Endpoints:
    GET /api/shipments   -> list of all shipments with live status
    GET /api/kpis        -> aggregate counts (total / active / delayed / ...)
    GET /                -> health check
"""

import asyncio
import random
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Logistics Network Digital Twin API", version="1.0.0")

# Wide-open CORS so the static frontend (served from any local port/file)
# can poll this API during development. Tighten this for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Simulation data
# ---------------------------------------------------------------------------

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Rotterdam", "Hamburg", "Singapore", "Shanghai", "Mumbai",
    "Dubai", "London", "Sao Paulo", "Tokyo", "Sydney", "Cape Town",
]

CARRIERS = ["Maersk Line", "FedEx Freight", "DHL Global", "UPS Cargo", "COSCO Shipping"]

STATUSES = ["Pending", "In Transit", "Delayed", "Delivered"]
STATUS_WEIGHTS = [0.10, 0.55, 0.15, 0.20]

NUM_SHIPMENTS = 18
TICK_SECONDS = 3  # how often the background simulator mutates state


class Shipment(BaseModel):
    shipment_id: str
    origin: str
    destination: str
    carrier: str
    status: str          # "Pending" | "In Transit" | "Delayed" | "Delivered"
    progress_pct: int
    created_at: str
    last_updated: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _random_route():
    return random.sample(CITIES, 2)  # (origin, destination), guaranteed distinct


def _new_shipment(numeric_id: int) -> Shipment:
    origin, destination = _random_route()
    now = _now_iso()
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
    return Shipment(
        shipment_id=f"SHP-{numeric_id}",
        origin=origin,
        destination=destination,
        carrier=random.choice(CARRIERS),
        status=status,
        progress_pct=0 if status == "Pending" else random.randint(5, 95),
        created_at=now,
        last_updated=now,
    )


# In-memory "network state" — the single source of truth for the twin.
shipments: List[Shipment] = [_new_shipment(1000 + i) for i in range(NUM_SHIPMENTS)]
_lock = asyncio.Lock()
_next_id = 1000 + NUM_SHIPMENTS


def _advance_shipment(shipment: Shipment) -> None:
    """Move one shipment's state machine forward by one tick."""
    shipment.last_updated = _now_iso()

    if shipment.status == "Pending":
        if random.random() < 0.5:
            shipment.status = "In Transit"
            shipment.progress_pct = random.randint(1, 15)
        return

    if shipment.status == "In Transit":
        shipment.progress_pct = min(100, shipment.progress_pct + random.randint(5, 20))
        if random.random() < 0.12:
            shipment.status = "Delayed"
        elif shipment.progress_pct >= 100:
            shipment.status = "Delivered"
            shipment.progress_pct = 100
        return

    if shipment.status == "Delayed":
        if random.random() < 0.4:
            shipment.status = "In Transit"
        return

    # Delivered shipments hold their state until retired below.


async def _simulate_updates():
    """Background loop: the 'live' part of the digital twin."""
    global _next_id
    while True:
        await asyncio.sleep(TICK_SECONDS)
        async with _lock:
            touched = random.sample(shipments, k=random.randint(3, 7))
            for shipment in touched:
                _advance_shipment(shipment)

            # Occasionally retire a delivered shipment and spawn a fresh one,
            # so the network keeps producing new traffic over time.
            for i, shipment in enumerate(shipments):
                if shipment.status == "Delivered" and random.random() < 0.15:
                    shipments[i] = _new_shipment(_next_id)
                    _next_id += 1


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(_simulate_updates())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/shipments", response_model=List[Shipment])
async def get_shipments():
    """Live snapshot of every shipment currently tracked by the twin."""
    async with _lock:
        return [s.copy() for s in shipments]


@app.get("/api/kpis")
async def get_kpis():
    """Aggregate counts, handy if a client doesn't want to derive them itself."""
    async with _lock:
        total = len(shipments)
        active = sum(1 for s in shipments if s.status == "In Transit")
        delayed = sum(1 for s in shipments if s.status == "Delayed")
        delivered = sum(1 for s in shipments if s.status == "Delivered")
        pending = sum(1 for s in shipments if s.status == "Pending")
    return {
        "total": total,
        "active_transits": active,
        "delayed": delayed,
        "delivered": delivered,
        "pending": pending,
    }


@app.get("/")
async def root():
    return {"message": "Logistics Network Digital Twin API is running", "docs": "/docs"}
