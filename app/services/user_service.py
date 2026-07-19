from typing import Optional

from app.models.user_model import User
from app.repositories.user_repository import UserRepository, WithRelations


class UserService:

    def __init__(
            self, 
            user_repository: UserRepository
        ):
        self.user_repository = user_repository

    async def get_user_by_email(
            self, 
            email: str, 
            with_relations: Optional[WithRelations] = None, 
            flush: bool = False
        ) -> Optional[User]:
        # This method retrieves a user by their email address, optionally including related data and controlling whether to flush the session.
        return await self.user_repository.get_by_email(
            email, 
            with_relations=with_relations, 
            flush=flush
        )

    async def get_user_by_public_id(
            self, 
            public_id: str, 
            with_relations: Optional[WithRelations] = None, 
            flush: bool = False
        ) -> Optional[User]:
        # This method retrieves a user by their public ID, optionally including related data and controlling whether to flush the session.
        return await self.user_repository.get_by_public_id(
            public_id, 
            with_relations=with_relations, 
            flush=flush
        )

    async def get_user_by_id(
        self,
        user_id: int,
        with_relations: Optional[WithRelations] = None, 
        flush: bool = False
    ) -> Optional[User]:
        # This method retrieves a user by their ID, optionally including related data and controlling whether to flush the session.
        return await self.user_repository.get_by_id(
            user_id, 
            with_relations=with_relations, 
            flush=flush
        )
