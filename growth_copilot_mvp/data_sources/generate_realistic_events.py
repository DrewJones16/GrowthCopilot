import json
import random
from datetime import datetime, timedelta

SOURCES = ["tiktok", "organic", "paid", "referral"]

def generate_events(num_users=120):
    events = []
    base_time = datetime(2026, 5, 20, 10, 0, 0)

    for i in range(num_users):
        user_id = f"u{i}"
        source = random.choices(SOURCES, weights=[0.35, 0.35, 0.2, 0.1])[0]

        t0 = base_time + timedelta(minutes=random.randint(0, 500))

        events.append({
            "user_id": user_id,
            "event_name": "install",
            "timestamp": t0.isoformat(),
            "properties": {"source": source}
        })

        if random.random() > 0.1:
            events.append({
                "user_id": user_id,
                "event_name": "onboarding_start",
                "timestamp": (t0 + timedelta(minutes=1)).isoformat(),
                "properties": {"source": source}
            })

        if source == "tiktok":
            p = 0.45
        elif source == "paid":
            p = 0.70
        else:
            p = 0.60

        if random.random() < p:
            events.append({
                "user_id": user_id,
                "event_name": "onboarding_complete",
                "timestamp": (t0 + timedelta(minutes=3)).isoformat(),
                "properties": {"source": source}
            })

    return events


def save():
    path = "local_events.json"
    with open(path, "w") as f:
        json.dump(generate_events(), f, indent=2)

    print("Generated dataset → local_events.json")


if __name__ == "__main__":
    save()