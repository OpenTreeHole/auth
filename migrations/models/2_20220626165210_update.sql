-- upgrade --
CREATE TABLE IF NOT EXISTS `shamiremail`
(
    `id`           INT          NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `key`          LONGTEXT     NOT NULL,
    `encrypted_by` VARCHAR(128) NOT NULL,
    `user_id`      INT          NOT NULL,
    CONSTRAINT `fk_shamirem_user_51dcf72a` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
-- downgrade --
DROP TABLE IF EXISTS `shamiremail`;
