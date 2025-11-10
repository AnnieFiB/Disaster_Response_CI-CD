"""
FEMA Public Assistance Funded Projects ETL
-------------------------------------------
Features:
 • Extract all records from the OpenFEMA v2 Public Assistance API.
      • Day 1: full dump of all records (paged; $top<=1000).
      • Thereafter: incremental by lastRefresh >= watermark.
            Watermark = max(DB MAX(lastrefresh), today's 00:00Z on first incremental day).
      • Respects POLL_ONCE / POLL_INTERVAL_SEC for scheduling in-container.
 • Handle pagination safely (max $top=1000).
 • Retry politely with exponential backoff and jitter.
 • Load data into Postgres landing (raw JSONB) table keyed by `hash`.
 • Transform typed columns into a flat table for analysis (Power BI).

Environment variables (see docker-compose.yml or .env):
    FEMA_API_URL           API endpoint (default: FEMA v2 URL)
    DB_HOST, DB_PORT,
    DB_NAME, DB_USER,
    DB_PASSWORD            Postgres connection settings
    TABLE_NAME             Landing table (default: fema_pa_projects_v2)
    TABLE_NAME_FLAT        Flat table (default: fema_pa_projects_v2_flat)
    BATCH_SIZE             Desired page size (clamped to 1000)
    LOAD_MODE              upsert | replace (replace truncates tables)
"""

import os
import sys
import time
import json
import random
from datetime import datetime, timezone, timedelta

import requests
from sqlalchemy import create_engine, text

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
FEMA_API_URL  = os.getenv("FEMA_API_URL")

TABLE_LANDING = os.getenv("TABLE_NAME")
TABLE_FLAT    = os.getenv("TABLE_NAME_FLAT")

LOAD_MODE     = os.getenv("LOAD_MODE", "upsert").lower()   # upsert | replace
BATCH_SIZE    = int(os.getenv("BATCH_SIZE", "1000"))
MAX_TOP       = 1000  # OpenFEMA API limit

# Scheduler
POLL_ONCE       = os.getenv("POLL_ONCE", "false").lower() == "true"
POLL_INTERVAL   = int(os.getenv("POLL_INTERVAL_SEC", "86400"))  # default: daily

# Database connection
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
ENGINE  = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    future=True,
)

# HTTP client setup
SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/json",
    "User-Agent": "Promellon-FEMA-ETL/1.0 (ops@promellon.io)"
})
TIMEOUT = (5, 120)  # connect, read
MAX_RETRIES = 5


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def _sleep_backoff(attempt, retry_after=None):
    if retry_after:
        time.sleep(retry_after)
        return
    delay = min(60, (2 ** attempt) + random.uniform(0, 1))
    print(f"[HTTP] backoff {delay:.1f}s", flush=True)
    time.sleep(delay)
    

def http_get(params: dict):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = SESSION.get(FEMA_API_URL, params=params, timeout=TIMEOUT)
            if r.status_code in (429, 503):
                ra = int(r.headers.get("Retry-After", "0") or "0")
                print(f"[HTTP] {r.status_code} retry-after={ra}s", flush=True)
                _sleep_backoff(attempt, ra)
                continue
            if r.status_code >= 500:
                print(f"[HTTP] {r.status_code} server error", flush=True)
                _sleep_backoff(attempt)
                continue
            r.raise_for_status()
            j = r.json()
            return j
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            print(f"[HTTP] attempt {attempt} failed: {e}", flush=True)
            _sleep_backoff(attempt)


# -----------------------------------------------------------------------------
# DB helpers
# -----------------------------------------------------------------------------
def landing_count() -> int:
    with ENGINE.begin() as c:
        return c.exec_driver_sql(f"SELECT COUNT(*) FROM public.{TABLE_LANDING}").scalar()

def db_watermark():
    with ENGINE.begin() as c:
        return c.exec_driver_sql(f"SELECT MAX(lastrefresh) FROM public.{TABLE_LANDING}").scalar()

def truncate_if_replace():
    if LOAD_MODE != "replace":
        return
    print("[ETL] TRUNCATE landing & flat (replace mode)", flush=True)
    with ENGINE.begin() as c:
        c.exec_driver_sql(f"TRUNCATE TABLE public.{TABLE_LANDING};")
        c.exec_driver_sql(f"TRUNCATE TABLE public.{TABLE_FLAT};")


# Insert or update rows (raw JSONB from API) into landing table
def upsert_landing(rows):
    if not rows:
        return 0
    payload = []
    for obj in rows:
        h = obj.get("hash")
        if not h:
            continue
        lr = obj.get("lastRefresh")  # ISO string or None
        payload.append({"hash": h, "raw": json.dumps(obj), "lastrefresh": lr})
    if not payload:
        return 0

    sql = text(f"""
        INSERT INTO public.{TABLE_LANDING} (hash, raw, lastrefresh)
        VALUES (:hash, CAST(:raw AS JSONB), NULLIF(:lastrefresh,'')::timestamptz)
        ON CONFLICT (hash) DO UPDATE SET
          raw = EXCLUDED.raw,
          lastrefresh = COALESCE(EXCLUDED.lastrefresh, {TABLE_LANDING}.lastrefresh);
    """)
    with ENGINE.begin() as c:
        c.execute(sql, payload)
    return len(payload)


# Sync flat table( view for analytics) from landing table
def sync_flat_from_landing():
    sql = text(f"""
        INSERT INTO public.{TABLE_FLAT} (
            hash, lastrefresh,
            disasternumber, declarationdate, incidenttype, pwnumber, applicationtitle,
            applicantid, damagecategorycode, damagecategorydesc, projectstatus,
            projectprocessstep, projectsize, county, countycode, stateabbr, statenumbercode,
            projectamount, federalshare, totalobligated, lastobligation, firstobligation,
            mitigationamount, gmprojectid, gmapplicantid, raw
        )
        SELECT
            l.hash,
            l.lastrefresh,
            NULLIF(l.raw->>'disasterNumber','')::smallint,
            NULLIF(l.raw->>'declarationDate','')::date,
            NULLIF(l.raw->>'incidentType','')::text,
            NULLIF(l.raw->>'pwNumber','')::int,
            NULLIF(l.raw->>'applicationTitle','')::text,
            NULLIF(l.raw->>'applicantId','')::text,
            NULLIF(l.raw->>'damageCategoryCode','')::text,
            NULLIF(l.raw->>'damageCategoryDescrip','')::text,
            NULLIF(l.raw->>'projectStatus','')::text,
            NULLIF(l.raw->>'projectProcessStep','')::text,
            NULLIF(l.raw->>'projectSize','')::text,
            NULLIF(l.raw->>'county','')::text,
            NULLIF(l.raw->>'countyCode','')::text,
            NULLIF(l.raw->>'stateAbbreviation','')::text,
            NULLIF(l.raw->>'stateNumberCode','')::text,
            NULLIF(l.raw->>'projectAmount','')::numeric,
            NULLIF(l.raw->>'federalShareObligated','')::numeric,
            NULLIF(l.raw->>'totalObligated','')::numeric,
            NULLIF(l.raw->>'lastObligationDate','')::timestamptz,
            NULLIF(l.raw->>'firstObligationDate','')::timestamptz,
            NULLIF(l.raw->>'mitigationAmount','')::numeric,
            NULLIF(l.raw->>'gmProjectId','')::bigint,
            NULLIF(l.raw->>'gmApplicantId','')::bigint,
            l.raw
        FROM public.{TABLE_LANDING} l
        LEFT JOIN public.{TABLE_FLAT} f ON f.hash = l.hash
        WHERE f.hash IS NULL
           OR (l.lastrefresh IS NOT NULL AND l.lastrefresh > f.lastrefresh)
        ON CONFLICT (hash) DO UPDATE SET
            lastrefresh        = EXCLUDED.lastrefresh,
            disasternumber     = EXCLUDED.disasternumber,
            declarationdate    = EXCLUDED.declarationdate,
            incidenttype       = EXCLUDED.incidenttype,
            pwnumber           = EXCLUDED.pwnumber,
            applicationtitle   = EXCLUDED.applicationtitle,
            applicantid        = EXCLUDED.applicantid,
            damagecategorycode = EXCLUDED.damagecategorycode,
            damagecategorydesc = EXCLUDED.damagecategorydesc,
            projectstatus      = EXCLUDED.projectstatus,
            projectprocessstep = EXCLUDED.projectprocessstep,
            projectsize        = EXCLUDED.projectsize,
            county             = EXCLUDED.county,
            countycode         = EXCLUDED.countycode,
            stateabbr          = EXCLUDED.stateabbr,
            statenumbercode    = EXCLUDED.statenumbercode,
            projectamount      = EXCLUDED.projectamount,
            federalshare       = EXCLUDED.federalshare,
            totalobligated     = EXCLUDED.totalobligated,
            lastobligation     = EXCLUDED.lastobligation,
            firstobligation    = EXCLUDED.firstobligation,
            mitigationamount   = EXCLUDED.mitigationamount,
            gmprojectid        = EXCLUDED.gmprojectid,
            gmapplicantid      = EXCLUDED.gmapplicantid,
            raw                = EXCLUDED.raw;
    """)
    with ENGINE.begin() as c:
        res = c.execute(sql)
    return res.rowcount or 0



# -----------------------------------------------------------------------------
# Main ETL logic
# -----------------------------------------------------------------------------
def full_dump():
    """
    Fetch ALL rows (no filter), paging by $skip/$top.
    """
    total, skip = 0, 0
    while True:
        params = {"$skip": skip, "$top": min(BATCH_SIZE, MAX_TOP)}
        print(f"[FULL] request skip={skip} top={params['$top']}", flush=True)
        j = http_get(params)
        rows = j.get("PublicAssistanceFundedProjectsDetails", j if isinstance(j, list) else [])
        if not rows:
            break
        n = upsert_landing(rows)
        total += n
        skip += len(rows)
        print(f"[FULL] upserted +{n} (total {total})", flush=True)
        if len(rows) < min(BATCH_SIZE, MAX_TOP):
            break
    return total

def incremental_from(watermark_iso: str):
    """
    Pull where lastRefresh >= 'watermark_iso'.
    watermark_iso MUST be quoted ISO (e.g., '2025-11-09T00:00:00Z').
    """
    total, skip = 0, 0
    while True:
        params = {
            "$skip": skip,
            "$top": min(BATCH_SIZE, MAX_TOP),
            "$orderby": "lastRefresh",
            "$filter": f"lastRefresh ge {watermark_iso}",
        }
        print(f"[INCR] request skip={skip} filter={params['$filter']}", flush=True)
        j = http_get(params)
        rows = j.get("PublicAssistanceFundedProjectsDetails", j if isinstance(j, list) else [])
        if not rows:
            break
        n = upsert_landing(rows)
        total += n
        skip += len(rows)
        print(f"[INCR] upserted +{n} (total {total})", flush=True)
        if len(rows) < min(BATCH_SIZE, MAX_TOP):
            break
    return total


# -----------------------------------------------------------------------------
# Orchestration
# -----------------------------------------------------------------------------
def today_midnight_iso_quoted():
    t0 = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return f"'{t0.isoformat().replace('+00:00','Z')}'"

def run_cycle():
    """
    One cycle: full once if empty; then incremental from max(DB watermark, today@00:00Z).
    """
    if LOAD_MODE == "replace":
        truncate_if_replace()

    empty = (landing_count() == 0)
    if empty:
        print("[ETL] Landing empty: running FULL dump once...", flush=True)
        full_dump()
    else:
        print("[ETL] Landing has data: skipping full dump.", flush=True)

    # Decide incremental watermark
    db_wm = db_watermark()  # datetime or None
    today_q = today_midnight_iso_quoted()
    if db_wm:
        # use DB watermark, but don’t go earlier than today midnight
        db_iso_q = f"'{db_wm.isoformat().replace('+00:00','Z')}'"
        wm_q = max(db_iso_q, today_q)  # string comparison works since both quoted ISO (same length)
    else:
        wm_q = today_q

    print(f"[ETL] Incremental watermark = {wm_q}", flush=True)
    incremental_from(wm_q)

    changed = sync_flat_from_landing()
    print(f"[ETL] flat sync updated {changed} rows — {datetime.utcnow().isoformat()}Z", flush=True)


def main():
    while True:
        try:
            run_cycle()
        except Exception as e:
            print(f"[ETL] ERROR: {e}", file=sys.stderr, flush=True)
        if POLL_ONCE:
            break
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()