import os
import uuid
import aiofiles
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import UploadFile
from src.config import get_settings
from src.patterns.models import Pattern
from src.patterns.schemas import PatternCreate, PatternUpdate
from src.claude.client import get_claude_client

settings = get_settings()


class PatternService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = Path(settings.patterns_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def get_patterns(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> tuple[List[Pattern], int]:
        query = select(Pattern).where(Pattern.user_id == user_id)
        if active_only:
            query = query.where(Pattern.is_active == True)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        patterns = list(result.scalars().all())

        # Count total
        count_query = select(func.count()).select_from(Pattern).where(Pattern.user_id == user_id)
        if active_only:
            count_query = count_query.where(Pattern.is_active == True)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return patterns, total

    async def get_pattern(self, pattern_id: int, user_id: int) -> Optional[Pattern]:
        result = await self.db.execute(
            select(Pattern).where(
                Pattern.id == pattern_id,
                Pattern.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def create_pattern(
        self,
        user_id: int,
        pattern_data: PatternCreate,
        image: UploadFile
    ) -> Pattern:
        # Save image
        image_path = await self._save_image(image)

        # Create pattern
        pattern = Pattern(
            user_id=user_id,
            name=pattern_data.name,
            description=pattern_data.description,
            pattern_type=pattern_data.pattern_type.value,
            confidence_threshold=pattern_data.confidence_threshold,
            image_path=image_path
        )
        self.db.add(pattern)
        await self.db.commit()
        await self.db.refresh(pattern)

        return pattern

    async def update_pattern(
        self,
        pattern_id: int,
        user_id: int,
        update_data: PatternUpdate
    ) -> Optional[Pattern]:
        pattern = await self.get_pattern(pattern_id, user_id)
        if not pattern:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        if 'pattern_type' in update_dict and update_dict['pattern_type']:
            update_dict['pattern_type'] = update_dict['pattern_type'].value

        for key, value in update_dict.items():
            setattr(pattern, key, value)

        await self.db.commit()
        await self.db.refresh(pattern)
        return pattern

    async def delete_pattern(self, pattern_id: int, user_id: int) -> bool:
        pattern = await self.get_pattern(pattern_id, user_id)
        if not pattern:
            return False

        # Delete image file
        if pattern.image_path and os.path.exists(pattern.image_path):
            os.remove(pattern.image_path)

        await self.db.delete(pattern)
        await self.db.commit()
        return True

    async def analyze_pattern(self, pattern_id: int, user_id: int) -> Optional[Pattern]:
        pattern = await self.get_pattern(pattern_id, user_id)
        if not pattern:
            return None

        # Analyze with Claude Vision
        claude = get_claude_client()
        analysis = await claude.analyze_pattern(pattern.image_path)

        # Update pattern with analysis
        pattern.claude_analysis = analysis
        if analysis.get('pattern_identified'):
            pattern.pattern_type = analysis['pattern_identified'].lower().replace(' ', '_')

        await self.db.commit()
        await self.db.refresh(pattern)
        return pattern

    async def _save_image(self, image: UploadFile) -> str:
        ext = Path(image.filename).suffix or '.png'
        filename = f"{uuid.uuid4()}{ext}"
        filepath = self.upload_dir / filename

        async with aiofiles.open(filepath, 'wb') as f:
            content = await image.read()
            await f.write(content)

        return str(filepath)
