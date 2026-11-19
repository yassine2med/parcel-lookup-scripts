"""Load and query a parcel CSV extract."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

REQUIRED = ("parcel_id", "address", "owner", "zoning", "land_use", "lot_sqft", "assessed_value")


@dataclass(frozen=True)
class Parcel:
    """One parcel record."""

    parcel_id: str
    address: str
    owner: str
    zoning: str
    land_use: str
    lot_sqft: int
    assessed_value: int

    @property
    def value_per_sqft(self) -> float:
        """Assessed value divided by lot area."""
        return self.assessed_value / self.lot_sqft


def load(path: str | Path) -> list[Parcel]:
    """Read parcels from a CSV file. Raises ValueError on missing columns or bad numbers."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("missing columns: " + ", ".join(missing))
        parcels = []
        for n, row in enumerate(reader, start=2):
            try:
                parcels.append(Parcel(
                    row["parcel_id"].strip(), row["address"].strip(), row["owner"].strip(),
                    row["zoning"].strip(), row["land_use"].strip(),
                    int(row["lot_sqft"]), int(row["assessed_value"])))
            except (ValueError, AttributeError) as exc:
                raise ValueError(f"line {n}: bad number ({exc})") from exc
    return parcels


def by_id(parcels: list[Parcel], parcel_id: str) -> Parcel | None:
    """Find one parcel by id, ignoring case."""
    wanted = parcel_id.strip().lower()
    return next((p for p in parcels if p.parcel_id.lower() == wanted), None)


def search(parcels: list[Parcel], text: str = "", zoning: str = "",
           min_sqft: int = 0) -> list[Parcel]:
    """Filter by text in address or owner, exact zoning, and minimum lot size."""
    text = text.lower()
    out = []
    for p in parcels:
        if text and text not in p.address.lower() and text not in p.owner.lower():
            continue
        if zoning and p.zoning.lower() != zoning.lower():
            continue
        if p.lot_sqft < min_sqft:
            continue
        out.append(p)
    return out


def summary(parcels: list[Parcel]) -> dict[str, dict[str, float]]:
    """Per zoning district: parcel count, total acres, average value per sqft."""
    result: dict[str, dict[str, float]] = {}
    for p in parcels:
        z = result.setdefault(p.zoning, {"count": 0, "sqft": 0, "value": 0})
        z["count"] += 1
        z["sqft"] += p.lot_sqft
        z["value"] += p.assessed_value
    return {
        k: {"count": v["count"], "acres": v["sqft"] / 43560, "value_per_sqft": v["value"] / v["sqft"]}
        for k, v in sorted(result.items())
    }
