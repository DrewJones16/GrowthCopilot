"""data_connector.py — abstract data connector with three implementations.

Usage:
    from growth_copilot_mvp.data_connector import get_connector
    from growth_copilot_mvp.config import DATA_SOURCE

    connector = get_connector(DATA_SOURCE)
    events    = connector.fetch_events()

    # events is a list of dicts:
    # [{"user": str, "event": str, "source": str, "day": date}, ...]
    # This is the same format synth_data.py already produces.

The detector engine, aggregations, and everything downstream is unchanged.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class DataConnector(ABC):
    """All connectors must return events in the canonical format."""

    @abstractmethod
    def fetch_events(self) -> List[Dict[str, Any]]:
        """Return list of event dicts: {user, event, source, day}."""
        ...

    @abstractmethod
    def data_quality_report(self) -> Dict[str, Any]:
        """Return data quality metrics for the telemetry health panel."""
        ...


# ---------------------------------------------------------------------------
# Synthetic connector (current demo mode)
# ---------------------------------------------------------------------------

class SyntheticConnector(DataConnector):
    """Wraps synth_data.generate_events() — zero config required."""

    def __init__(self, days: int = 90, daily_installs: int = 120,
                 seed: int = 42, archetype=None):
        self.days            = days
        self.daily_installs  = daily_installs
        self.seed            = seed
        self.archetype       = archetype

    def fetch_events(self) -> List[Dict[str, Any]]:
        from growth_copilot_mvp.synth_data import generate_events
        arch = self.archetype
        daily = self.daily_installs
        if arch is not None:
            daily = arch.get("daily_installs", self.daily_installs)
        return generate_events(
            days           = self.days,
            daily_installs = daily,
            seed           = self.seed,
            archetype      = arch,
        )

    def data_quality_report(self) -> Dict[str, Any]:
        return {
            "source":                "synthetic",
            "completeness":          1.0,
            "missing_source_rate":   0.0,
            "event_delay_detected":  False,
            "daily_install_floor_ok": True,
            "confidence_penalty":    1.0,
            "warnings":              [],
        }


# ---------------------------------------------------------------------------
# CSV connector (intermediate option — export from Firebase/Mixpanel)
# ---------------------------------------------------------------------------

class CSVConnector(DataConnector):
    """Reads events from a CSV file exported from Firebase or any analytics tool.

    Expected CSV columns:
        user_id     — unique user identifier
        event_name  — raw event name (will be translated via EVENT_MAP)
        source      — acquisition source (utm_source, etc.)
        timestamp   — ISO datetime or date string

    Example CSV row:
        u_abc123, first_open, tiktok, 2026-05-01
    """

    def __init__(self, csv_path: str):
        self.csv_path = csv_path

    def fetch_events(self) -> List[Dict[str, Any]]:
        import csv
        from growth_copilot_mvp.event_map import canonical, DEFAULT_SOURCE

        events = []
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        raw_date = row.get("timestamp", row.get("date", ""))
                        if "T" in raw_date:
                            day = date.fromisoformat(raw_date.split("T")[0])
                        else:
                            day = date.fromisoformat(raw_date[:10])
                        events.append({
                            "user":   row.get("user_id", ""),
                            "event":  canonical(row.get("event_name", "")),
                            "source": row.get("source", DEFAULT_SOURCE) or DEFAULT_SOURCE,
                            "day":    day,
                        })
                    except Exception:
                        continue
        except FileNotFoundError:
            raise FileNotFoundError(
                f"CSV file not found: {self.csv_path}\n"
                f"Export your Firebase events to CSV and place it at this path."
            )
        return events

    def data_quality_report(self) -> Dict[str, Any]:
        events   = self.fetch_events()
        total    = len(events)
        missing  = sum(1 for e in events if not e.get("source") or e["source"] == "unknown")
        miss_rate = round(missing / total, 3) if total else 0.0
        warnings  = []
        if miss_rate > 0.30:
            warnings.append(f"High missing source rate ({miss_rate*100:.0f}%) — cohort analysis may be unreliable.")
        if total < 500:
            warnings.append(f"Low event volume ({total} events) — consider extending the lookback window.")
        return {
            "source":               "csv",
            "total_events":         total,
            "missing_source_rate":  miss_rate,
            "event_delay_detected": False,
            "daily_install_floor_ok": total > 0,
            "confidence_penalty":   0.80 if miss_rate > 0.30 else 1.0,
            "warnings":             warnings,
        }


# ---------------------------------------------------------------------------
# Firebase / BigQuery connector
# ---------------------------------------------------------------------------

class FirebaseConnector(DataConnector):
    """Reads events from Firebase Analytics BigQuery export.

    Prerequisites:
        1. Enable Firebase Analytics BigQuery export in Firebase Console
           → Project Settings → Integrations → BigQuery → Link
        2. Wait 24-48h for first data to appear
        3. Install: pip install google-cloud-bigquery
        4. Authenticate: gcloud auth application-default login
           OR set GOOGLE_CREDENTIALS_PATH in config.py

    BigQuery table format:
        {project}.{dataset}.events_YYYYMMDD
        Firebase exports one table per day, named events_YYYYMMDD.

    The connector queries across shards using wildcard: events_*
    """

    def __init__(
        self,
        project:          str,
        dataset:          str,
        lookback_days:    int  = 90,
        credentials_path: str  = "",
    ):
        self.project          = project
        self.dataset          = dataset
        self.lookback_days    = lookback_days
        self.credentials_path = credentials_path
        self._events_cache    = None
        self._quality_cache   = None

    def _get_client(self):
        try:
            from google.cloud import bigquery
        except ImportError:
            raise ImportError(
                "google-cloud-bigquery not installed.\n"
                "Run: pip install google-cloud-bigquery"
            )
        if self.credentials_path:
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            return bigquery.Client(project=self.project, credentials=creds)
        return bigquery.Client(project=self.project)

    def _build_query(self) -> str:
        from growth_copilot_mvp.event_map import EVENT_MAP, SOURCE_PROPERTY
        today      = date.today()
        start_date = today - timedelta(days=self.lookback_days)
        start_str  = start_date.strftime("%Y%m%d")
        end_str    = today.strftime("%Y%m%d")

        # Build event name filter from EVENT_MAP values
        event_names = list(EVENT_MAP.values())
        event_filter = ", ".join(f"'{e}'" for e in event_names)

        return f"""
        SELECT
            user_pseudo_id                                    AS user_id,
            event_name,
            PARSE_DATE('%Y%m%d', event_date)                 AS event_date,
            (
                SELECT ep.value.string_value
                FROM UNNEST(event_params) ep
                WHERE ep.key = '{SOURCE_PROPERTY}'
                LIMIT 1
            )                                                 AS source
        FROM
            `{self.project}.{self.dataset}.events_*`
        WHERE
            _TABLE_SUFFIX BETWEEN '{start_str}' AND '{end_str}'
            AND event_name IN ({event_filter})
        ORDER BY
            event_date, user_pseudo_id
        """

    def fetch_events(self) -> List[Dict[str, Any]]:
        if self._events_cache is not None:
            return self._events_cache

        from growth_copilot_mvp.event_map import canonical, DEFAULT_SOURCE

        client  = self._get_client()
        query   = self._build_query()
        results = client.query(query).result()

        events = []
        for row in results:
            source = row.source or DEFAULT_SOURCE
            events.append({
                "user":   str(row.user_id),
                "event":  canonical(row.event_name),
                "source": source.lower().strip() or DEFAULT_SOURCE,
                "day":    row.event_date,
            })

        self._events_cache = events
        return events

    def data_quality_report(self) -> Dict[str, Any]:
        if self._quality_cache is not None:
            return self._quality_cache

        events    = self.fetch_events()
        total     = len(events)
        missing   = sum(1 for e in events if e["source"] == "unknown")
        miss_rate = round(missing / total, 3) if total else 0.0

        # Check for event delay (no events in last 2 days)
        if events:
            latest     = max(e["day"] for e in events)
            delay_days = (date.today() - latest).days
            delay      = delay_days >= 2
        else:
            delay = True

        # Daily install counts
        from collections import Counter
        daily_counts = Counter(
            e["day"] for e in events if e["event"] == "install"
        )
        min_daily = min(daily_counts.values()) if daily_counts else 0

        warnings = []
        if miss_rate > 0.30:
            warnings.append(f"High missing source rate ({miss_rate*100:.0f}%) — check SOURCE_PROPERTY in event_map.py.")
        if delay:
            warnings.append(f"Event delay detected — last data is {delay_days} days old. Check BigQuery export.")
        if min_daily < 20:
            warnings.append(f"Some days have fewer than 20 installs — detectors may not fire reliably.")
        if total < 1000:
            warnings.append(f"Low total event volume ({total}) — extend LOOKBACK_DAYS in config.py.")

        self._quality_cache = {
            "source":               "firebase_bigquery",
            "total_events":         total,
            "missing_source_rate":  miss_rate,
            "event_delay_detected": delay,
            "daily_install_floor_ok": min_daily >= 20,
            "confidence_penalty":   0.80 if miss_rate > 0.30 else 1.0,
            "warnings":             warnings,
        }
        return self._quality_cache




# ---------------------------------------------------------------------------
# Streamlit session state connector (for uploaded CSV data)
# ---------------------------------------------------------------------------

class StreamlitUploadConnector(DataConnector):
    """Uses events already processed and stored in st.session_state.
    
    Called from briefing.py when user has connected their own data
    via the Connect page. No file I/O needed — events are already
    parsed and in the canonical format.
    """

    def __init__(self, events: list):
        self._events = events

    def fetch_events(self):
        return self._events

    def data_quality_report(self):
        events    = self._events
        total     = len(events)
        missing   = sum(1 for e in events if not e.get("source") or e["source"] == "unknown")
        miss_rate = round(missing / total, 3) if total else 0.0
        warnings  = []
        if miss_rate > 0.30:
            warnings.append(f"High missing source rate ({miss_rate*100:.0f}%) — cohort analysis may be less reliable.")
        if total < 500:
            warnings.append(f"Low event volume ({total} events) — consider uploading more history.")
        # Check date range
        days = set(e["day"] for e in events)
        date_range = (max(days) - min(days)).days + 1 if days else 0
        if date_range < 30:
            warnings.append(f"Only {date_range} days of data — detectors work best with 60+ days.")
        return {
            "source":               "csv_upload",
            "total_events":         total,
            "date_range_days":      date_range,
            "missing_source_rate":  miss_rate,
            "event_delay_detected": False,
            "daily_install_floor_ok": total > 0,
            "confidence_penalty":   0.85 if miss_rate > 0.30 else 1.0,
            "warnings":             warnings,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_connector(source: str = None, **kwargs) -> DataConnector:
    """Return the appropriate connector based on config."""
    from growth_copilot_mvp.config import (
        DATA_SOURCE, SYNTHETIC_DAYS, SYNTHETIC_DAILY_INSTALLS, SYNTHETIC_SEED,
        CSV_PATH, BIGQUERY_PROJECT, BIGQUERY_DATASET, LOOKBACK_DAYS,
        GOOGLE_CREDENTIALS_PATH,
    )

    src = source or DATA_SOURCE

    if src == "synthetic":
        return SyntheticConnector(
            days           = kwargs.get("days",            SYNTHETIC_DAYS),
            daily_installs = kwargs.get("daily_installs",  SYNTHETIC_DAILY_INSTALLS),
            seed           = kwargs.get("seed",            SYNTHETIC_SEED),
            archetype      = kwargs.get("archetype",       None),
        )
    elif src == "csv":
        return CSVConnector(
            csv_path = kwargs.get("csv_path", CSV_PATH),
        )
    elif src == "firebase":
        if not BIGQUERY_PROJECT or not BIGQUERY_DATASET:
            raise ValueError(
                "BIGQUERY_PROJECT and BIGQUERY_DATASET must be set in config.py "
                "before using the Firebase connector."
            )
        return FirebaseConnector(
            project          = BIGQUERY_PROJECT,
            dataset          = BIGQUERY_DATASET,
            lookback_days    = kwargs.get("lookback_days", LOOKBACK_DAYS),
            credentials_path = GOOGLE_CREDENTIALS_PATH,
        )
    else:
        raise ValueError(f"Unknown DATA_SOURCE: '{src}'. Must be 'synthetic', 'csv', or 'firebase'.")