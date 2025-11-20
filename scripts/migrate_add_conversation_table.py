#!/usr/bin/env python3
"""
Migration script to add t_conversation table.
This script adds a new table to store conversation history with prompt_id and version references.
"""
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text

def migrate():
    """Add t_conversation table to the database."""
    create_table_sql = """
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
    """

    print("Starting migration: Adding t_conversation table...")

    try:
        with engine.connect() as connection:
            connection.execute(text(create_table_sql))
            connection.commit()
            print("✓ Successfully created t_conversation table")
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        sys.exit(1)

    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
