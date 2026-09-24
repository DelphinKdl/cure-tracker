"""One-off script: seed pour_log.json with sample pours spread across the past 3
months, for the booth demo, so the log reads like an ongoing job history.

Run with: python seed_pour_log.py
Uses the same synthetic reading generator as the app, so seeded data looks
identical to what "Generate sample readings" would produce. Delete
pour_log.json (or re-run this script) to reset before the fair if you don't
want seed data mixed with a live walkthrough.
"""

import random
from datetime import datetime, timedelta

from app import generate_sample_readings
from pour_log import reset_log, save_pour

LOCATIONS_AND_TARGETS = [
    ("Level 3 - Slab, Grid C4-C6", 3000),
    ("Level 5 - Column C12", 4000),
    ("Basement - Footing F22", 5000),
    ("Level 8 - Slab, Grid D1-D3", 3000),
    ("Level 2 - Shear Wall W4", 4000),
    ("Level 10 - Slab, Grid A5-A7", 3000),
    ("Podium - Transfer Beam TB3", 5000),
    ("Level 6 - Column C8", 4000),
    ("Level 4 - Slab, Grid B2-B4", 3000),
    ("Loading Dock - Slab on Grade", 3000),
    ("Level 7 - Slab, Grid A1-A3", 4000),
    ("Level 9 - Column C15", 5000),
    ("Roof - Mechanical Pad", 3000),
    ("Level 1 - Shear Wall W1", 4000),
    ("Basement - Footing F8", 5000),
    ("Level 11 - Slab, Grid D4-D6", 3000),
    ("Level 12 - Column C20", 4000),
    ("Podium - Transfer Beam TB1", 5000),
]

SEED = 7
PAST_DAYS = 90


def main() -> None:
    reset_log()
    rng = random.Random(SEED)
    now = datetime.now().replace(minute=0, second=0, microsecond=0)

    days_ago = sorted(rng.sample(range(1, PAST_DAYS + 1), len(LOCATIONS_AND_TARGETS)), reverse=True)

    for i, ((location, target_psi), days) in enumerate(zip(LOCATIONS_AND_TARGETS, days_ago), start=1):
        pour_dt = now - timedelta(days=days, hours=rng.randint(0, 23))
        pour = {
            "pour_id": f"P-{i:03d}",
            "location": location,
            "target_psi": target_psi,
            "pour_datetime": pour_dt,
        }
        readings = generate_sample_readings(pour_dt)
        save_pour(pour, readings)
    print(f"Seeded {len(LOCATIONS_AND_TARGETS)} pours into pour_log.json, spread over the past {PAST_DAYS} days.")


if __name__ == "__main__":
    main()
