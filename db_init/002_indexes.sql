-- Indexes for FEMA PA Projects v2


-- Landing
CREATE INDEX IF NOT EXISTS idx_fema_pa_v2_lastrefresh_btree
  ON public.fema_pa_projects_v2 (lastrefresh);
CREATE INDEX IF NOT EXISTS idx_fema_pa_v2_lastrefresh_brin
  ON public.fema_pa_projects_v2 USING BRIN (lastrefresh);
CREATE INDEX IF NOT EXISTS idx_fema_pa_v2_raw_gin
  ON public.fema_pa_projects_v2 USING GIN (raw jsonb_path_ops);

-- Flat (point lookups + range scans + composites for common slicers)
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_stateabbr
  ON public.fema_pa_projects_v2_flat (stateabbr);
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_incidenttype
  ON public.fema_pa_projects_v2_flat (incidenttype);
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_disasternumber
  ON public.fema_pa_projects_v2_flat (disasternumber);
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_declarationdate_btree
  ON public.fema_pa_projects_v2_flat (declarationdate);
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_declarationdate_brin
  ON public.fema_pa_projects_v2_flat USING BRIN (declarationdate);

-- Useful composites for dashboards
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_state_incident
  ON public.fema_pa_projects_v2_flat (stateabbr, incidenttype);
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_date_state
  ON public.fema_pa_projects_v2_flat (declarationdate, stateabbr);

-- Money filters/sorts
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_federalshare
  ON public.fema_pa_projects_v2_flat (federalshare);
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_totalobligated
  ON public.fema_pa_projects_v2_flat (totalobligated);

-- IDs often used in joins
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_gmprojectid
  ON public.fema_pa_projects_v2_flat (gmprojectid);
CREATE INDEX IF NOT EXISTS idx_fema_pa_flat_gmapplicantid
  ON public.fema_pa_projects_v2_flat (gmapplicantid);
