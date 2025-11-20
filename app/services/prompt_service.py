from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
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
                      version: str = "v1",
                      created_by: str = "system") -> Prompt:

        # Check if this specific version exists
        existing = self.db.query(Prompt).filter(
            Prompt.name == name,
            Prompt.version == version
        ).first()
        if existing:
            raise ValueError(f"Prompt '{name}' version '{version}' already exists.")

        # Create Prompt
        new_prompt = Prompt(
            name=name,
            display_name=display_name,
            description=description,
            template=template,
            variables_meta=variables_meta,
            created_by=created_by,
            is_enabled=True,
            version=version,
            comment="Initial version" if version == "v1" else f"Version {version}"
        )
        self.db.add(new_prompt)
        self.db.commit()
        self.db.refresh(new_prompt)
        return new_prompt

    def create_new_version(self,
                          name: str,
                          template: str,
                          variables_meta: dict,
                          version: str,
                          comment: str | None = None,
                          created_by: str = "system") -> Prompt:
        """Create a new version of an existing prompt"""
        # Get the base prompt to copy display_name and description
        base_prompt = self.db.query(Prompt).filter(
            Prompt.name == name
        ).order_by(desc(Prompt.created_at)).first()

        if not base_prompt:
            raise ValueError(f"No existing prompt found with name '{name}'")

        # Check if this version already exists
        existing = self.db.query(Prompt).filter(
            Prompt.name == name,
            Prompt.version == version
        ).first()
        if existing:
            raise ValueError(f"Version '{version}' already exists for prompt '{name}'")

        # Create new version
        new_version = Prompt(
            name=name,
            display_name=base_prompt.display_name,
            description=base_prompt.description,
            template=template,
            variables_meta=variables_meta,
            version=version,
            comment=comment or f"Version {version}",
            created_by=created_by,
            is_enabled=True
        )
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        return new_version

    def update_prompt(self,
                      prompt_name: str,
                      template: str,
                      variables_meta: dict,
                      version: str = "v1",
                      comment: str | None = None,
                      created_by: str = "system") -> Prompt:
        """Update a specific version of a prompt"""
        prompt = self.db.query(Prompt).filter(
            Prompt.name == prompt_name,
            Prompt.version == version
        ).first()
        if not prompt:
            raise ValueError(f"Prompt '{prompt_name}' version '{version}' not found.")

        prompt.template = template
        prompt.variables_meta = variables_meta
        if comment:
            prompt.comment = comment
        if created_by:
            prompt.created_by = created_by

        prompt.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(prompt)
        return prompt

    def list_prompts(self, search: str | None = None, limit: int = 100) -> List[Prompt]:
        """List all prompts (all versions)"""
        query = self.db.query(Prompt).filter(Prompt.is_enabled == True)
        if search:
            query = query.filter(
                or_(
                    Prompt.name.ilike(f"%{search}%"),
                    Prompt.display_name.ilike(f"%{search}%")
                )
            )
        return query.order_by(desc(Prompt.updated_at)).limit(limit).all()

    def list_prompt_names(self, search: str | None = None) -> List[str]:
        """List unique prompt names (for version selection)"""
        query = self.db.query(Prompt.name).filter(Prompt.is_enabled == True).distinct()
        if search:
            query = query.filter(Prompt.name.ilike(f"%{search}%"))
        return [row[0] for row in query.all()]

    def list_versions_by_name(self, name: str) -> List[Prompt]:
        """List all versions of a specific prompt name"""
        return self.db.query(Prompt).filter(
            Prompt.name == name,
            Prompt.is_enabled == True
        ).order_by(desc(Prompt.created_at)).all()

    def get_prompt_details(self, name: str, version: str | None = None) -> Prompt | None:
        """Get a specific prompt by name and optionally version"""
        query = self.db.query(Prompt).filter(Prompt.name == name)
        if version:
            query = query.filter(Prompt.version == version)
        else:
            # If no version specified, get the latest one
            query = query.order_by(desc(Prompt.created_at))
        return query.first()

    def delete_prompt(self, name: str, version: str | None = None) -> bool:
        """Delete a prompt (soft delete). If version is None, delete all versions."""
        query = self.db.query(Prompt).filter(Prompt.name == name)
        if version:
            query = query.filter(Prompt.version == version)

        prompts = query.all()
        if prompts:
            for prompt in prompts:
                prompt.is_enabled = False
            self.db.commit()
            return True
        return False
