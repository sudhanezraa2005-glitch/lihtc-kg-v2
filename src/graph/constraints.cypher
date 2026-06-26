// Uniqueness constraints for FHFA graph nodes
// These statements are infrastructure specification only.

CREATE CONSTRAINT IF NOT EXISTS FOR (s:State) REQUIRE s.state_fips IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:County) REQUIRE c.county_fips IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (m:MetroArea) REQUIRE m.cbsa_code IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (t:CensusTract) REQUIRE t.tract_fips IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (h:HPISnapshot) REQUIRE h.snapshot_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (l:ConformingLimitSnapshot) REQUIRE l.snapshot_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (f:FMRSnapshot) REQUIRE f.snapshot_id IS UNIQUE;
