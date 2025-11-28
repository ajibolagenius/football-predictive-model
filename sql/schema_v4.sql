-- Add missing columns for Player Analytics

ALTER TABLE players ADD COLUMN IF NOT EXISTS position VARCHAR(20);

ALTER TABLE player_season_stats
ADD COLUMN IF NOT EXISTS xg_chain FLOAT;

ALTER TABLE player_season_stats
ADD COLUMN IF NOT EXISTS xg_buildup FLOAT;

ALTER TABLE player_season_stats
ADD COLUMN IF NOT EXISTS minutes_played INT;