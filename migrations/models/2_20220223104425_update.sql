-- upgrade --
ALTER TABLE `user` ALTER COLUMN `refresh_token` SET DEFAULT '';
-- downgrade --
ALTER TABLE `user` ALTER COLUMN `refresh_token` DROP DEFAULT;
