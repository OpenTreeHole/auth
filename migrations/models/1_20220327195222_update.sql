-- upgrade --
ALTER TABLE `user` ADD `is_active` BOOL NOT NULL  DEFAULT 1;
-- downgrade --
ALTER TABLE `user` DROP COLUMN `is_active`;
