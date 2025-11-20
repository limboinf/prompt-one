# Prompt One

A model-agnostic, platform-agnostic LLM Prompt Management System designed to decouple Prompt management from the model invocation layer.

## Features

- **Prompt Management**: Centralized CRUD operations for Prompts with version control, stored in MySQL.
- **Jinja2 Templating**: Support for variable interpolation in prompts using Jinja2 syntax.
- **Real-time Preview**: Instant rendering of prompts with variable substitution (Markdown supported).
- **Playground**: Integrated testing environment using LangChain to invoke various LLMs (e.g., OpenAI) and iterate on prompts quickly.
- **Prompt Comparison**: Side-by-side comparison of two prompt versions with real-time LLM responses to evaluate optimization effectiveness.
- **Service-Ready**: Built as a foundation to provide unified Prompt services to other business backends or microservices.

## Tech Stack

- **Frontend**: Streamlit
- **Backend Logic**: Python (Pydantic, SQLAlchemy)
- **Database**: MySQL
- **Templating**: Jinja2
- **LLM Integration**: LangChain

## Prerequisites

- Python 3.11+
- MySQL Server

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root directory based on your configuration:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=prompt_manager

# LLM (Required for Playground)
OPENAI_API_KEY=sk-...
# Optional
# OPENAI_API_BASE=https://api.openai.com/v1
# DEFAULT_MODEL_NAME=gpt-3.5-turbo
```

### 3. Database Initialization

First, ensure you have created the database in your MySQL server:

```sql
CREATE DATABASE prompt_manager;
```

Then, run the initialization script to create the necessary tables:

```bash
python scripts/init_db.py
```

### 4. Run the Application

Start the Streamlit application:

```bash
streamlit run main.py
```

The application will be available at `http://localhost:8501`.

### Available Pages

1. **Home** (`main.py`): Welcome page with project overview
2. **Prompt Manager** (`pages/01_Prompt_Manager.py`): Create, edit, and manage prompts
3. **Prompt Preview** (`pages/02_Prompt_Preview.py`): Preview rendered prompts with variable substitution
4. **Playground** (`pages/03_Playground.py`): Interactive testing with LLM chat interface
5. **Prompt Comparison** (`pages/04_Prompt_Comparison.py`): Side-by-side comparison of prompt versions

For detailed information about the Prompt Comparison feature, see [COMPARISON_FEATURE.md](COMPARISON_FEATURE.md).

## Project Structure

- `app/`: Core application logic
    - `db/`: Database sessions and models
    - `models/`: Pydantic data models
    - `services/`: Business logic services
    - `ui/`: Streamlit UI components
    - `llm/`: LangChain integration
- `pages/`: Streamlit pages (Prompt Manager, Preview, Playground, Prompt Comparison)
- `config/`: Configuration settings
- `scripts/`: Utility scripts
