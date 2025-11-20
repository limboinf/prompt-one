from jinja2 import Environment, BaseLoader, TemplateSyntaxError
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.prompt import Prompt, PromptVersion
from app.models.schemas import PromptVariableMeta
import logging

# Configure logging
logger = logging.getLogger(__name__)

class PromptRenderService:
    def __init__(self, db: Session):
        self.db = db
        self.env = Environment(loader=BaseLoader(), autoescape=False)

    def get_latest_version(self, prompt_name: str) -> Optional[PromptVersion]:
        prompt = self.db.query(Prompt).filter(Prompt.name == prompt_name).first()
        if not prompt:
            return None
        
        return self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.is_latest == True
        ).first()

    def get_specific_version(self, prompt_name: str, version: str) -> Optional[PromptVersion]:
        prompt = self.db.query(Prompt).filter(Prompt.name == prompt_name).first()
        if not prompt:
            return None
            
        return self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == version
        ).first()

    def validate_variables(self, variables: Dict[str, Any], variables_meta: list[dict]) -> Dict[str, Any]:
        """
        Validate and fill default values based on metadata.
        """
        validated = variables.copy()
        if not variables_meta:
            return validated

        for meta_dict in variables_meta:
            # Convert dict to Pydantic model for easier handling
            try:
                meta = PromptVariableMeta(**meta_dict)
            except Exception as e:
                logger.warning(f"Invalid variable meta: {meta_dict} - {e}")
                continue
                
            if meta.name not in validated:
                if meta.required and meta.default is None:
                     # In a real strict mode we might raise error, 
                     # but for now we just log or let Jinja fail if it's used
                     pass
                elif meta.default is not None:
                    validated[meta.name] = meta.default
        
        return validated

    def render(self, prompt_name: str, variables: Dict[str, Any], version: Optional[str] = None) -> str:
        if version:
            prompt_version = self.get_specific_version(prompt_name, version)
        else:
            prompt_version = self.get_latest_version(prompt_name)

        if not prompt_version:
            raise ValueError(f"Prompt not found: {prompt_name} (version={version})")

        # Validate variables
        final_vars = self.validate_variables(variables, prompt_version.variables_meta or [])

        try:
            template = self.env.from_string(prompt_version.template)
            return template.render(**final_vars)
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error in {prompt_name}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error rendering prompt {prompt_name}: {str(e)}")
