"""config.py — single source of truth for data source and pipeline settings.

To switch from synthetic to real data:
    1. Set DATA_SOURCE = "firebase"
    2. Set BIGQUERY_PROJECT, BIGQUERY_DATASET to your Firebase export
    3. Edit event_map.py to match your app's event names
    4. Delete data/signal_registry.json to start fresh

Everything else stays the same.
"""

# ---------------------------------------------------------------------------
# Data source
# ---------------------------------------------------------------------------

# "synthetic"  — uses synth_data.py (demo mode)
# "firebase"   — reads from BigQuery Firebase Analytics export
# "csv"        — reads from a local CSV export (intermediate option)
DATA_SOURCE = "synthetic"

# ---------------------------------------------------------------------------
# Synthetic data settings (only used when DATA_SOURCE = "synthetic")
# ---------------------------------------------------------------------------

SYNTHETIC_DAYS           = 90
SYNTHETIC_DAILY_INSTALLS = 120
SYNTHETIC_SEED           = 42

# ---------------------------------------------------------------------------
# Firebase / BigQuery settings (only used when DATA_SOURCE = "firebase")
# ---------------------------------------------------------------------------

BIGQUERY_PROJECT   = ""          # e.g. "my-firebase-project"
BIGQUERY_DATASET   = ""          # e.g. "analytics_123456789"
BIGQUERY_TABLE     = "events_*"  # Firebase exports as events_YYYYMMDD shards
LOOKBACK_DAYS      = 90          # how many days of history to pull

# Service account key path (leave empty to use Application Default Credentials)
GOOGLE_CREDENTIALS_PATH = ""

# ---------------------------------------------------------------------------
# CSV settings (only used when DATA_SOURCE = "csv")
# ---------------------------------------------------------------------------

CSV_PATH = "data/events.csv"
# Expected columns: user_id, event_name, source, timestamp (ISO format)

# ---------------------------------------------------------------------------
# Pipeline settings
# ---------------------------------------------------------------------------

# Minimum installs per day to run detectors (below this → suppress alerts)
MIN_DAILY_INSTALLS = 20

# Maximum missing source rate before confidence penalty applied
MAX_MISSING_SOURCE_RATE = 0.30

# Confidence penalty multiplier when data quality is degraded
DATA_QUALITY_CONFIDENCE_PENALTY = 0.80

# ---------------------------------------------------------------------------
# App metadata (used in briefing header)
# ---------------------------------------------------------------------------

APP_NAME        = "GrowthCopilot"
APP_DESCRIPTION = "synthetic demo data"   # override with e.g. "production · iOS + Android"