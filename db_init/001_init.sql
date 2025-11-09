-- DisasterResponseAnalytics/db_init/001_init.sql
-- Create FEMA Public Assistance Funded Projects Details v2 tables


-- Landing: raw JSON + watermark
CREATE TABLE IF NOT EXISTS public.fema_pa_projects_v2 (
  hash         TEXT PRIMARY KEY,
  raw          JSONB NOT NULL,
  lastrefresh  TIMESTAMPTZ NULL
);

COMMENT ON TABLE public.fema_pa_projects_v2 IS 'OpenFEMA v2 landing (raw JSONB + watermark).';

-- Flat: BI-friendly columns 
CREATE TABLE IF NOT EXISTS public.fema_pa_projects_v2_flat (
  hash               TEXT PRIMARY KEY,
  lastrefresh        TIMESTAMPTZ,
  disasternumber     SMALLINT,
  declarationdate    DATE,
  incidenttype       TEXT,
  pwnumber           INTEGER,
  applicationtitle   TEXT,
  applicantid        TEXT,
  damagecategorycode TEXT,
  damagecategorydesc TEXT,
  projectstatus      TEXT,
  projectprocessstep TEXT,
  projectsize        TEXT,
  county             TEXT,
  countycode         TEXT,
  stateabbr          TEXT,
  statenumbercode    TEXT,
  projectamount      NUMERIC,
  federalshare       NUMERIC,
  totalobligated     NUMERIC,
  lastobligation     TIMESTAMPTZ,
  firstobligation    TIMESTAMPTZ,
  mitigationamount   NUMERIC,
  gmprojectid        BIGINT,
  gmapplicantid      BIGINT,
  raw                JSONB NOT NULL
);

COMMENT ON TABLE public.fema_pa_projects_v2_flat IS 'Flattened snapshot populated from landing during ETL sync.';
