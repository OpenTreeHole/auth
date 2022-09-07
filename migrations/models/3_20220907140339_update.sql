-- upgrade --
ALTER TABLE `user` ADD `config` JSON NOT NULL;
-- downgrade --
ALTER TABLE `user` DROP COLUMN `config`;
