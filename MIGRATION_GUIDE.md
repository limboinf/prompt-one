# 数据库迁移指南 - 版本对比功能

## 概述

此迁移将数据库结构从单一提示词（每个名称一个版本）更新为支持多版本提示词（每个名称可以有多个版本）。

## 变更内容

1. **数据模型变更**：
   - 移除 `name` 字段的唯一约束
   - 添加 `(name, version)` 的联合唯一约束
   - 允许同一个提示词名称有多个版本记录

2. **新增功能**：
   - 支持创建同名提示词的不同版本
   - 对比页面可以对比同名提示词的不同版本
   - 新增版本管理相关的 API

## 迁移步骤

### 前置条件

1. 确保已安装所有依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 确保数据库配置正确（`.env` 文件）：
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=prompt_manager
   ```

### 执行迁移

1. **备份数据库**（重要！）：
   ```bash
   # MySQL 示例
   mysqldump -u root -p prompt_manager > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **运行迁移脚本**：
   ```bash
   python scripts/migrate_add_version_unique_constraint.py
   ```

3. **验证迁移**：
   - 检查数据库表结构
   - 确认 `name` 字段不再有唯一约束
   - 确认存在 `uq_prompt_name_version` 约束

### 验证示例（MySQL）

```sql
-- 查看表结构
DESCRIBE t_prompt;

-- 查看约束
SHOW CREATE TABLE t_prompt;

-- 应该看到类似这样的约束：
-- UNIQUE KEY `uq_prompt_name_version` (`name`,`version`)
```

## 使用新功能

### 创建新版本的提示词

```python
from app.services.prompt_service import PromptService

# 创建第一个版本
prompt_service.create_prompt(
    name="my_prompt",
    display_name="我的提示词",
    description="测试提示词",
    template="Hello {{name}}",
    variables_meta={"type": "object", "properties": {"name": {"type": "string"}}},
    version="v1"
)

# 创建第二个版本
prompt_service.create_new_version(
    name="my_prompt",
    template="Hi {{name}}, welcome!",
    variables_meta={"type": "object", "properties": {"name": {"type": "string"}}},
    version="v2",
    comment="添加了欢迎语"
)
```

### 在对比页面使用版本对比

1. 访问 "提示词效果对比" 页面
2. 选择要对比的提示词名称
3. 在左侧选择一个版本（优化前）
4. 在右侧选择另一个版本（优化后）
5. 配置变量并进行对比测试

## 回滚

如果迁移出现问题，可以从备份恢复：

```bash
# MySQL 示例
mysql -u root -p prompt_manager < backup_YYYYMMDD_HHMMSS.sql
```

## 注意事项

1. **数据兼容性**：现有的提示词会保留其当前的 `version` 值（通常是 "v1"）
2. **命名规范**：建议使用语义化版本号（如 v1, v2, v1.1 等）
3. **版本管理**：每次重大更新建议创建新版本，而不是直接修改现有版本
4. **测试建议**：在生产环境运行前，请在测试环境充分测试

## 故障排除

### 问题：迁移脚本报错 "unique constraint violation"

**解决方案**：检查是否有重复的 (name, version) 组合：

```sql
SELECT name, version, COUNT(*) as count
FROM t_prompt
GROUP BY name, version
HAVING count > 1;
```

### 问题：对比页面提示 "只有 1 个版本"

**解决方案**：为该提示词创建新版本：

1. 在 Prompt Manager 页面创建同名但不同版本的提示词
2. 或使用 API 调用 `create_new_version` 方法

## 技术支持

如有问题，请查看：
- 项目 README
- 代码中的注释和文档字符串
- GitHub Issues
