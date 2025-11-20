from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.models.prompt import Prompt
from datetime import datetime

class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def create_prompt(self, 
                      name: str, 
                      display_name: str, 
                      description: str, 
                      template: str, 
                      variables_meta: dict, 
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
            template=template,
            variables_meta=variables_meta,
            created_by=created_by,
            is_enabled=True,
            version="v1",
            comment="Initial version"
        )
        self.db.add(new_prompt)
        self.db.commit()
        self.db.refresh(new_prompt)
        return new_prompt

    def update_prompt(self, 
                      prompt_name: str, 
                      template: str, 
                      variables_meta: dict, 
                      version: str | None = None, 
                      comment: str | None = None,
                      created_by: str = "system") -> Prompt:
        
        prompt = self.db.query(Prompt).filter(Prompt.name == prompt_name).first()
        if not prompt:
            raise ValueError(f"Prompt '{prompt_name}' not found.")

        prompt.template = template
        prompt.variables_meta = variables_meta
        if version:
            prompt.version = version
        if comment:
            prompt.comment = comment
        if created_by:
            prompt.created_by = created_by
            
        prompt.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(prompt)
        return prompt

    def list_prompts(self, search: str | None = None, limit: int = 100) -> List[Prompt]:
        query = self.db.query(Prompt).filter(Prompt.is_enabled == True)
        if search:
            query = query.filter(
                or_(
                    Prompt.name.ilike(f"%{search}%"),
                    Prompt.display_name.ilike(f"%{search}%")
                )
            )
        return query.order_by(desc(Prompt.updated_at)).limit(limit).all()

    def get_prompt_details(self, name: str) -> Prompt | None:
        return self.db.query(Prompt).filter(Prompt.name == name).first()

    def delete_prompt(self, name: str) -> bool:
        prompt = self.db.query(Prompt).filter(Prompt.name == name).first()
        if prompt:
            prompt.is_enabled = False
            self.db.commit()
            return True
        return False
