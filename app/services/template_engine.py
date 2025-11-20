from jinja2 import Environment, BaseLoader, TemplateSyntaxError
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.prompt import Prompt
import logging

# Configure logging
logger = logging.getLogger(__name__)

class PromptRenderService:
    def __init__(self, db: Session):
        self.db = db
        self.env = Environment(loader=BaseLoader(), autoescape=False)

    def get_prompt(self, prompt_name: str, version: str | None = None) -> Prompt | None:
        """Get prompt by name and optionally version"""
        query = self.db.query(Prompt).filter(Prompt.name == prompt_name)
        if version:
            query = query.filter(Prompt.version == version)
        else:
            # Get the latest version if no version specified
            from sqlalchemy import desc
            query = query.order_by(desc(Prompt.created_at))
        return query.first()

    def validate_variables(self, variables: Dict[str, Any], variables_meta: Any) -> Dict[str, Any]:
        """
        Validate and fill default values based on metadata (JSON Schema format).
        """
        validated = variables.copy()
        if not variables_meta:
            return validated

        # Handle JSON Schema format (Dict)
        if isinstance(variables_meta, dict):
            properties = variables_meta.get("properties", {})

            for name, schema in properties.items():
                # Apply default if variable is missing
                if name not in validated and "default" in schema:
                    validated[name] = schema["default"]
            return validated

        return validated

    def render(self, prompt_name: str, variables: Dict[str, Any]) -> str:
        """Render prompt by name (gets latest version if multiple exist)"""
        prompt = self.get_prompt(prompt_name)

        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_name}")

        # Validate variables
        final_vars = self.validate_variables(variables, prompt.variables_meta or [])

        try:
            template = self.env.from_string(prompt.template)
            return template.render(**final_vars)
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error in {prompt_name}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error rendering prompt {prompt_name}: {str(e)}")

    def render_by_version(self, prompt_name: str, version: str, variables: Dict[str, Any]) -> str:
        """Render a specific version of a prompt"""
        prompt = self.get_prompt(prompt_name, version)

        if not prompt:
            raise ValueError(f"Prompt '{prompt_name}' version '{version}' not found")

        # Validate variables
        final_vars = self.validate_variables(variables, prompt.variables_meta or [])

        try:
            template = self.env.from_string(prompt.template)
            return template.render(**final_vars)
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error in {prompt_name} v{version}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error rendering prompt {prompt_name} v{version}: {str(e)}")
