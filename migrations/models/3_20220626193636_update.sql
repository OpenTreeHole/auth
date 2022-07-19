-- upgrade --
CREATE TABLE IF NOT EXISTS `deleted_email` (
    `hash` VARCHAR(128) NOT NULL  PRIMARY KEY
) CHARACTER SET utf8mb4;;
CREATE TABLE IF NOT EXISTS `registered_email` (
    `hash` VARCHAR(128) NOT NULL  PRIMARY KEY
) CHARACTER SET utf8mb4;;
ALTER TABLE `shamiremail` RENAME TO `shamir_email`;
ALTER TABLE `shamir_email` MODIFY COLUMN `encrypted_by` VARCHAR(128) NOT NULL;
-- downgrade --
ALTER TABLE `shamir_email` RENAME TO `shamiremail`;
ALTER TABLE `shamir_email` MODIFY COLUMN `encrypted_by` VARCHAR(64) NOT NULL;
DROP TABLE IF EXISTS `deleted_email`;
DROP TABLE IF EXISTS `registered_email`;
