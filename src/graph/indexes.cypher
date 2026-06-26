// Recommended indexes for FHFA graph performance and lookup.
// This file is a mapping specification, not a data load script.

CREATE INDEX IF NOT EXISTS FOR (s:State) ON (s.state_fips);
CREATE INDEX IF NOT EXISTS FOR (s:State) ON (s.state_abbr);
CREATE INDEX IF NOT EXISTS FOR (c:County) ON (c.county_fips);
CREATE INDEX IF NOT EXISTS FOR (c:County) ON (c.state_fips);
CREATE INDEX IF NOT EXISTS FOR (c:County) ON (c.cbsa_number);
CREATE INDEX IF NOT EXISTS FOR (m:MetroArea) ON (m.cbsa_code);
CREATE INDEX IF NOT EXISTS FOR (t:CensusTract) ON (t.tract_fips);
CREATE INDEX IF NOT EXISTS FOR (t:CensusTract) ON (t.county_fips);
CREATE INDEX IF NOT EXISTS FOR (h:HPISnapshot) ON (h.snapshot_id);
CREATE INDEX IF NOT EXISTS FOR (h:HPISnapshot) ON (h.year);
CREATE INDEX IF NOT EXISTS FOR (h:HPISnapshot) ON (h.tract_fips);
// Composite index for efficient snapshot lookups by tract and year
CREATE INDEX IF NOT EXISTS FOR (h:HPISnapshot) ON (h.tract_fips, h.year);
CREATE INDEX IF NOT EXISTS FOR (l:ConformingLimitSnapshot) ON (l.snapshot_id);
CREATE INDEX IF NOT EXISTS FOR (l:ConformingLimitSnapshot) ON (l.year);
CREATE INDEX IF NOT EXISTS FOR (l:ConformingLimitSnapshot) ON (l.county_fips);
// Composite index for efficient snapshot lookups by county and year
CREATE INDEX IF NOT EXISTS FOR (l:ConformingLimitSnapshot) ON (l.county_fips, l.year);
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.snapshot_id);
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.county_fips);
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.state_fips);
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.year);
// Composite index for efficient FMR snapshot lookups by county and year
CREATE INDEX IF NOT EXISTS FOR (f:FMRSnapshot) ON (f.county_fips, f.year);
