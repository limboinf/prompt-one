-- ============================================================
-- 提示词表 - 支持多版本
-- ============================================================

-- MySQL / MariaDB
-- ============================================================
CREATE TABLE IF NOT EXISTS `t_prompt` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(128) NOT NULL COMMENT '提示词标识符（可以有多个版本）',
    `display_name` VARCHAR(128) NOT NULL COMMENT '显示名称',
    `description` VARCHAR(255) DEFAULT NULL COMMENT '描述',
    `version` VARCHAR(32) NOT NULL DEFAULT 'v1' COMMENT '版本标识',
    `template` TEXT NOT NULL COMMENT 'Jinja2 模板内容',
    `variables_meta` JSON DEFAULT NULL COMMENT '变量元数据',
    `created_by` VARCHAR(64) DEFAULT NULL COMMENT '创建者',
    `comment` VARCHAR(255) DEFAULT NULL COMMENT '版本备注',
    `is_enabled` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uq_prompt_name_version` (`name`, `version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='提示词表';

-- PostgreSQL
-- ============================================================
-- CREATE TABLE IF NOT EXISTS t_prompt (
--     id BIGSERIAL PRIMARY KEY,
--     name VARCHAR(128) NOT NULL,
--     display_name VARCHAR(128) NOT NULL,
--     description VARCHAR(255) DEFAULT NULL,
--     version VARCHAR(32) NOT NULL DEFAULT 'v1',
--     template TEXT NOT NULL,
--     variables_meta JSONB DEFAULT NULL,
--     created_by VARCHAR(64) DEFAULT NULL,
--     comment VARCHAR(255) DEFAULT NULL,
--     is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
--     created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     CONSTRAINT uq_prompt_name_version UNIQUE (name, version)
-- );
--
-- -- PostgreSQL 更新时间触发器
-- CREATE OR REPLACE FUNCTION update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = CURRENT_TIMESTAMP;
--     RETURN NEW;
-- END;
-- $$ language 'plpgsql';
--
-- CREATE TRIGGER update_t_prompt_updated_at BEFORE UPDATE
--     ON t_prompt FOR EACH ROW
--     EXECUTE FUNCTION update_updated_at_column();

-- SQLite
-- ============================================================
-- CREATE TABLE IF NOT EXISTS t_prompt (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name VARCHAR(128) NOT NULL,
--     display_name VARCHAR(128) NOT NULL,
--     description VARCHAR(255) DEFAULT NULL,
--     version VARCHAR(32) NOT NULL DEFAULT 'v1',
--     template TEXT NOT NULL,
--     variables_meta JSON DEFAULT NULL,
--     created_by VARCHAR(64) DEFAULT NULL,
--     comment VARCHAR(255) DEFAULT NULL,
--     is_enabled BOOLEAN NOT NULL DEFAULT 1,
--     created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     UNIQUE (name, version)
-- );
--
-- -- SQLite 更新时间触发器
-- CREATE TRIGGER IF NOT EXISTS update_t_prompt_updated_at
-- AFTER UPDATE ON t_prompt
-- FOR EACH ROW
-- BEGIN
--     UPDATE t_prompt SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
-- END;

-- ============================================================
-- 示例数据
-- ============================================================

-- 创建第一个版本的提示词
-- INSERT INTO t_prompt (name, display_name, description, version, template, variables_meta, created_by, comment)
-- VALUES (
--     'greeting',
--     '欢迎语',
--     '用户欢迎提示词',
--     'v1',
--     'Hello {{name}}!',
--     '{"type": "object", "properties": {"name": {"type": "string", "description": "用户名称"}}}',
--     'admin',
--     'Initial version'
-- );

-- 创建第二个版本的提示词
-- INSERT INTO t_prompt (name, display_name, description, version, template, variables_meta, created_by, comment)
-- VALUES (
--     'greeting',
--     '欢迎语',
--     '用户欢迎提示词',
--     'v2',
--     'Hi {{name}}, welcome to our platform!',
--     '{"type": "object", "properties": {"name": {"type": "string", "description": "用户名称"}}}',
--     'admin',
--     'Added platform welcome message'
-- );
