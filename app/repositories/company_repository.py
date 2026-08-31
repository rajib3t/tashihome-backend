from typing import Optional

from sqlalchemy import select, func

from app.models.company_model import Company
from app.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):


    async def get_by_email(
        self,
        email: str,
        flush: bool = False,
    ) -> Optional[Company]:
        query = select(Company).where(func.lower(Company.email) == email.strip().lower())
        return await self._fetch_one(query, flush=flush)

    async def get_by_name(
        self,
        name: str,
        flush: bool = False,
    ) -> Optional[Company]:
        query = select(Company).where(func.lower(Company.name) == name.strip().lower())
        return await self._fetch_one(query, flush=flush)

    async def get_company_by_user_id(
        self,
        user_id: int,
        flush: bool = False,
    ) -> Optional[Company]:
        query = select(Company).where(Company.user_id == user_id)
        return await self._fetch_one(query, flush=flush)
   
    async def get_by_public_id(
            self,
            company_id: int,
            flush: bool = False,
        ) -> Optional[Company]:
            query = select(Company).where(Company.public_id == company_id)
            return await self._fetch_one(query, flush=flush)

    async def get_by_id(
        self,
        company_id: int,
        flush: bool = False,
    ) -> Optional[Company]:
        query = select(Company).where(Company.id == company_id)
        return await self._fetch_one(query, flush=flush)

    async def create(
        self,
        company: Company,
        commit: bool = True,
    ) -> Company:
        self.db.add(company)

        if not commit:
            return company

        await self.db.commit()
        await self.db.refresh(company)
        return company

    async def update(
        self,
        company: Company,
        commit: bool = True,
    ) -> Company:
        if not commit:
            return company

        await self.db.commit()
        await self.db.refresh(company)
        return company