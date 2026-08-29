from typing import Optional

from sqlalchemy import select

from app.models.cancellation_policy_model import CancellationPolicy, CancellationPolicyStatus
from app.repositories.base_repository import BaseRepository


class CancellationPolicyRepository(BaseRepository[CancellationPolicy]):
    async def create(self, policy: CancellationPolicy, commit: bool = True) -> CancellationPolicy:
        self.db.add(policy)
        if commit:
            await self.db.commit()
            await self.db.refresh(policy)
        return policy

    async def get_by_id(self, policy_id: int, flush: bool = False) -> Optional[CancellationPolicy]:
        query = select(CancellationPolicy).where(CancellationPolicy.id == policy_id)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(self, public_id: str, flush: bool = False) -> Optional[CancellationPolicy]:
        query = select(CancellationPolicy).where(CancellationPolicy.public_id == public_id)
        return await self._fetch_one(query, flush=flush)

    async def update(self, policy: CancellationPolicy, commit: bool = True) -> CancellationPolicy:
        self.db.add(policy)
        if commit:
            await self.db.commit()
            await self.db.refresh(policy)
        return policy

