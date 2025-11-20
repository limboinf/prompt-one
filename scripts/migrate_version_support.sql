-- ============================================================
-- 数据库迁移 SQL - 添加版本支持
-- 将现有的 t_prompt 表从单版本模式迁移到多版本模式
-- ============================================================

-- 注意：执行前请先备份数据库！
-- mysqldump -u root -p prompt_manager > backup_$(date +%Y%m%d_%H%M%S).sql

-- ============================================================
-- MySQL / MariaDB
-- ============================================================

-- 1. 删除 name 字段的唯一约束
ALTER TABLE `t_prompt` DROP INDEX `name`;

-- 2. 添加 (name, version) 联合唯一约束
ALTER TABLE `t_prompt`
ADD CONSTRAINT `uq_prompt_name_version` UNIQUE (`name`, `version`);

-- 3. 验证约束是否正确创建
SHOW CREATE TABLE `t_prompt`;

-- ============================================================
-- PostgreSQL
-- ============================================================

-- -- 1. 删除 name 字段的唯一约束（如果存在）
-- ALTER TABLE t_prompt DROP CONSTRAINT IF EXISTS t_prompt_name_key;
--
-- -- 2. 添加 (name, version) 联合唯一约束
-- ALTER TABLE t_prompt
-- ADD CONSTRAINT uq_prompt_name_version UNIQUE (name, version);
--
-- -- 3. 验证约束
-- \d t_prompt

-- ============================================================
-- SQLite
-- ============================================================
-- SQLite 不支持直接删除约束，需要重建表

-- -- 1. 创建新表结构
-- CREATE TABLE t_prompt_new (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     name VARCHAR(128) NOT NULL,
--     display_name VARCHAR(128) NOT NULL,
--     description VARCHAR(255),
--     version VARCHAR(32) NOT NULL DEFAULT 'v1',
--     template TEXT NOT NULL,
--     variables_meta JSON,
--     created_by VARCHAR(64),
--     comment VARCHAR(255),
--     is_enabled BOOLEAN NOT NULL DEFAULT 1,
--     created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
--     UNIQUE (name, version)
-- );
--
-- -- 2. 复制数据
-- INSERT INTO t_prompt_new
-- SELECT * FROM t_prompt;
--
-- -- 3. 删除旧表
-- DROP TABLE t_prompt;
--
-- -- 4. 重命名新表
-- ALTER TABLE t_prompt_new RENAME TO t_prompt;
--
-- -- 5. 重新创建触发器
-- CREATE TRIGGER IF NOT EXISTS update_t_prompt_updated_at
-- AFTER UPDATE ON t_prompt
-- FOR EACH ROW
-- BEGIN
--     UPDATE t_prompt SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
-- END;

-- ============================================================
-- 验证查询
-- ============================================================

-- 检查是否有重复的 (name, version) 组合
SELECT name, version, COUNT(*) as count
FROM t_prompt
GROUP BY name, version
HAVING count > 1;

-- 查看每个提示词的版本数量
SELECT name, COUNT(*) as version_count
FROM t_prompt
WHERE is_enabled = 1
GROUP BY name
ORDER BY version_count DESC;

-- 查看所有提示词及其版本
SELECT
    name,
    version,
    display_name,
    comment,
    created_by,
    created_at,
    updated_at
FROM t_prompt
WHERE is_enabled = 1
ORDER BY name, created_at DESC;
