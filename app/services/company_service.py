from typing import Optional

from app.models.company_model import Company
from app.repositories.company_repository import CompanyRepository


class CompanyService:
    def __init__(self, company_repository: CompanyRepository):
        self.company_repository = company_repository

    async def get_by_email(self, email: str, flush: bool = False) -> Optional[Company]:
        return await self.company_repository.get_by_email(email=email, flush=flush)

    async def get_by_name(self, name: str, flush: bool = False) -> Optional[Company]:
        return await self.company_repository.get_by_name(name=name, flush=flush)

    async def update_vendor_company(
        self,
        company: Company,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Company:
        if name is not None:
            company.name = name
        if email is not None:
            company.email = email
        if phone is not None:
            company.phone = phone
        return company


    async def create_vendor_company(
        self,
        company : Company,
        commit: bool = True,
    ) -> Company:
        
        return await self.company_repository.create(company, commit=commit)

    async def create(
        self,
        company: Company,
        commit: bool = True,
    ) -> Company:
        return await self.create_vendor_company(company=company, commit=commit)


    async def update_company(
        self,
        company: Company,
        commit: bool = True,
    ) -> Company:
        
        return await self.company_repository.update(company, commit=commit)

    async def update(
        self,
        company: Company,
        commit: bool = True,
    ) -> Company:
        return await self.update_company(company=company, commit=commit)
