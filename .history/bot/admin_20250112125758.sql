INSERT INTO users (user_id, is_admin)
VALUES (1083294848, TRUE)
ON CONFLICT (user_id) DO UPDATE SET is_admin = TRUE;