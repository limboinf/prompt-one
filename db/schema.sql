CREATE TABLE IF NOT EXISTS `t_prompt` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(128) NOT NULL COMMENT 'Unique identifier',
    `display_name` VARCHAR(128) NOT NULL COMMENT 'Display name',
    `description` VARCHAR(255) COMMENT 'Description',
    `version` VARCHAR(32) NOT NULL DEFAULT 'v1' COMMENT 'Version identifier',
    `template` TEXT NOT NULL COMMENT 'Jinja2 template content',
    `variables_meta` JSON COMMENT 'Variables metadata',
    `is_enabled` TINYINT(1) NOT NULL DEFAULT 1,
    `created_by` VARCHAR(64),
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `comment` VARCHAR(255),
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Prompt definitions';
