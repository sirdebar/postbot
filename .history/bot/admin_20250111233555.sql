INSERT INTO users (user_id, is_admin)
VALUES (123456789, TRUE)
ON CONFLICT (user_id) DO UPDATE SET is_admin = TRUE;