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

CREATE TABLE IF NOT EXISTS `t_conversation` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `prompt_id` BIGINT NOT NULL COMMENT 'Reference to prompt id',
    `version` VARCHAR(32) NOT NULL COMMENT 'Prompt version used',
    `user_input` TEXT NOT NULL COMMENT 'User input/question',
    `ai_response` TEXT NOT NULL COMMENT 'AI generated response',
    `template_variables` JSON COMMENT 'Variables used to render the prompt template',
    `rendered_prompt` TEXT COMMENT 'Rendered prompt sent to AI',
    `model_name` VARCHAR(64) COMMENT 'AI model used (e.g., gpt-4, claude-3)',
    `temperature` FLOAT COMMENT 'Temperature parameter used',
    `tokens_used` INT COMMENT 'Total tokens consumed',
    `metadata` JSON COMMENT 'Additional metadata (e.g., response time, cost, etc.)',
    `user_id` VARCHAR(64) COMMENT 'User identifier',
    `session_id` VARCHAR(128) COMMENT 'Session identifier for grouping related conversations',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_prompt_id` (`prompt_id`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_prompt_version` (`prompt_id`, `version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Conversation history records';
