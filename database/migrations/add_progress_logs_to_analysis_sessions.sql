-- Add progress_logs column to analysis_sessions table for real-time UI logging
-- Migration: add_progress_logs_to_analysis_sessions.sql

ALTER TABLE analysis_sessions 
ADD COLUMN IF NOT EXISTS progress_logs JSONB DEFAULT '[]'::jsonb;

-- Add comment to document the purpose
COMMENT ON COLUMN analysis_sessions.progress_logs IS 'Real-time progress logging for UI updates during analysis execution';

-- Optional: Create an index for faster queries on progress logs if needed
-- CREATE INDEX IF NOT EXISTS idx_analysis_sessions_progress_logs 
-- ON analysis_sessions USING gin (progress_logs); 