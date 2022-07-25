-- upgrade --
ALTER TABLE `permission` ADD `synced` BOOL NOT NULL  DEFAULT 0;
-- downgrade --
ALTER TABLE `permission` DROP COLUMN `synced`;
