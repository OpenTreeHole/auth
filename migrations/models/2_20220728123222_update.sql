-- upgrade --
CREATE TABLE IF NOT EXISTS `deleted_email` (
    `hash` VARCHAR(128) NOT NULL  PRIMARY KEY
) CHARACTER SET utf8mb4;;
CREATE TABLE IF NOT EXISTS `permission` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `reason` VARCHAR(100) NOT NULL  DEFAULT '',
    `name` VARCHAR(32) NOT NULL  DEFAULT '',
    `start_time` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `end_time` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `synced` BOOL NOT NULL  DEFAULT 0,
    `made_by_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_permissi_user_1680a777` FOREIGN KEY (`made_by_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_permissi_user_1d9d6834` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;;
CREATE TABLE IF NOT EXISTS `registered_email` (
    `hash` VARCHAR(128) NOT NULL  PRIMARY KEY
) CHARACTER SET utf8mb4;;
ALTER TABLE `user` ADD `roles` JSON NOT NULL;
ALTER TABLE `user` ADD `last_login` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6);
ALTER TABLE `user` DROP COLUMN `silent`;
CREATE TABLE IF NOT EXISTS `shamir_email` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `key` LONGTEXT NOT NULL,
    `encrypted_by` VARCHAR(128) NOT NULL,
    `user_id` INT NOT NULL,
    CONSTRAINT `fk_shamir_e_user_7fa26603` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='shamir secret sharing(SSS) shares of user email';;
DROP TABLE IF EXISTS `punishment`;
-- downgrade --
ALTER TABLE `user` ADD `silent` JSON NOT NULL;
ALTER TABLE `user` DROP COLUMN `roles`;
ALTER TABLE `user` DROP COLUMN `last_login`;
DROP TABLE IF EXISTS `deleted_email`;
DROP TABLE IF EXISTS `permission`;
DROP TABLE IF EXISTS `registered_email`;
DROP TABLE IF EXISTS `shamir_email`;
