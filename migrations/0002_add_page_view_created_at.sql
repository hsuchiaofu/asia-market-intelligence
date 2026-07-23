ALTER TABLE page_views ADD COLUMN created_at TEXT;
UPDATE page_views SET created_at = updated_at WHERE created_at IS NULL;
