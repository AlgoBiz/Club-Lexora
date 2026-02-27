-- Fix destination foreign key issue
-- Run: sqlite3 db.sqlite3 < fix_destination.sql

-- Insert default destination with the ID that packages are referencing
INSERT OR IGNORE INTO user_account_destination 
(id, auto_id, name, slug, location, description, is_international, is_active, date_added, date_updated)
VALUES 
('00000000000000000000000000000001', 'DEST001', 'Default Destination', 'default-destination', 
 'To be updated', 'Default destination for existing packages. Please update.', 
 0, 1, datetime('now'), datetime('now'));

-- Verify the fix
SELECT 'Destination created:' as status, id, name FROM user_account_destination WHERE id = '00000000000000000000000000000001';
SELECT 'Packages referencing it:' as status, COUNT(*) as count FROM user_account_package WHERE destination_id = '00000000000000000000000000000001';
