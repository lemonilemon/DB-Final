-- Migration: Simplify role system to single role per user
-- Date: 2025-12-07
-- Description: Replace user_role junction table with a single role column in user table

BEGIN;

-- Step 1: Create ENUM type for user roles
CREATE TYPE user_role_enum AS ENUM ('User', 'Admin');

-- Step 2: Add role column to user table (nullable initially for migration)
ALTER TABLE "user" ADD COLUMN role user_role_enum;

-- Step 3: Migrate data from user_role to user table
-- Priority: Admin > User (if user has both roles, make them Admin)
UPDATE "user" u
SET role = CASE
    WHEN EXISTS (
        SELECT 1 FROM user_role ur
        WHERE ur.user_id = u.user_id AND ur.role = 'Admin'
    ) THEN 'Admin'::user_role_enum
    ELSE 'User'::user_role_enum
END;

-- Step 4: Make role NOT NULL with default value
ALTER TABLE "user" ALTER COLUMN role SET DEFAULT 'User'::user_role_enum;
ALTER TABLE "user" ALTER COLUMN role SET NOT NULL;

-- Step 5: Drop the old user_role table
DROP TABLE IF EXISTS user_role CASCADE;

-- Step 6: Create index on role for faster queries
CREATE INDEX idx_user_role ON "user"(role);

COMMIT;

-- Verification queries
SELECT 'Migration completed successfully!' AS status;
SELECT role, COUNT(*) as user_count FROM "user" GROUP BY role;
