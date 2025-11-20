from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.models.prompt import Prompt, PromptVersion
from app.models.schemas import PromptSchema, PromptVersionSchema
from datetime import datetime

class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def create_prompt(self, 
                      name: str, 
                      display_name: str, 
                      description: str, 
                      template: str, 
                      variables_meta: list, 
                      created_by: str = "system") -> Prompt:
        
        # Check if exists
        existing = self.db.query(Prompt).filter(Prompt.name == name).first()
        if existing:
            raise ValueError(f"Prompt with name '{name}' already exists.")

        # Create Prompt
        new_prompt = Prompt(
            name=name,
            display_name=display_name,
            description=description,
            is_enabled=True
        )
        self.db.add(new_prompt)
        self.db.flush() # Get ID

        # Create Initial Version (v1)
        initial_version = PromptVersion(
            prompt_id=new_prompt.id,
            version="v1",
            template=template,
            variables_meta=variables_meta,
            is_latest=True,
            created_by=created_by,
            comment="Initial version"
        )
        self.db.add(initial_version)
        self.db.commit()
        self.db.refresh(new_prompt)
        return new_prompt

    def create_new_version(self, 
                           prompt_name: str, 
                           template: str, 
                           variables_meta: list, 
                           version: str, 
                           comment: str = None,
                           created_by: str = "system") -> PromptVersion:
        
        prompt = self.db.query(Prompt).filter(Prompt.name == prompt_name).first()
        if not prompt:
            raise ValueError(f"Prompt '{prompt_name}' not found.")

        # Check if version exists
        existing_version = self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.version == version
        ).first()
        if existing_version:
            raise ValueError(f"Version '{version}' already exists for prompt '{prompt_name}'.")

        # Unset previous latest
        self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt.id,
            PromptVersion.is_latest == True
        ).update({"is_latest": False})

        # Create new version
        new_ver = PromptVersion(
            prompt_id=prompt.id,
            version=version,
            template=template,
            variables_meta=variables_meta,
            is_latest=True,
            created_by=created_by,
            comment=comment
        )
        self.db.add(new_ver)
        
        # Update prompt updated_at
        prompt.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(new_ver)
        return new_ver

    def list_prompts(self, search: str = None, limit: int = 100) -> List[Prompt]:
        query = self.db.query(Prompt).filter(Prompt.is_enabled == True)
        if search:
            query = query.filter(
                or_(
                    Prompt.name.ilike(f"%{search}%"),
                    Prompt.display_name.ilike(f"%{search}%")
                )
            )
        return query.order_by(desc(Prompt.updated_at)).limit(limit).all()

    def get_prompt_details(self, name: str) -> Optional[Prompt]:
        return self.db.query(Prompt).filter(Prompt.name == name).first()

    def delete_prompt(self, name: str) -> bool:
        prompt = self.db.query(Prompt).filter(Prompt.name == name).first()
        if prompt:
            prompt.is_enabled = False
            self.db.commit()
            return True
        return False

    def get_versions(self, prompt_name: str) -> List[PromptVersion]:
        prompt = self.db.query(Prompt).filter(Prompt.name == prompt_name).first()
        if not prompt:
            return []
        return self.db.query(PromptVersion).filter(
            PromptVersion.prompt_id == prompt.id
        ).order_by(desc(PromptVersion.created_at)).all()
