-- Add Unique Constraint to match_stats.match_id for ON CONFLICT support
ALTER TABLE match_stats
ADD CONSTRAINT match_stats_match_id_key UNIQUE (match_id);