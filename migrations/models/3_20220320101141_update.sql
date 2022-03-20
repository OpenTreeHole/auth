-- upgrade --
ALTER TABLE `user` DROP COLUMN `refresh_token`;
-- downgrade --
ALTER TABLE `user` ADD `refresh_token` VARCHAR(2000) NOT NULL  DEFAULT '';
