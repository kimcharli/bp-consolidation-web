import logging
import strawberry
from typing import List, Annotated, Union
from strawberry.asgi import GraphQL
import uuid
import dotenv
import os
from ck_apstra_api.apstra_session import CkApstraSession

logger = logging.getLogger(__name__)

from .model.ck_global import GlobalStore


@strawberry.type
class User:
    name: str
    age: int

users = [
    User(name="Patrick", age=100),
    User(name="Terry", age=101),
    User(name="John", age=102),
]


@strawberry.type
class Query1:
    @strawberry.field
    def user(self, info) -> User:
        return User(name="Patrick", age=100)
    
    @strawberry.field
    def users(self, info) -> List[User]:
        return users

    @strawberry.field
    def get_name(self) -> str:
        return "Users sss"
    
@strawberry.type
class Query2:
    @strawberry.field
    def hello(self, info) -> str:
        return "Hello world!"
    
@strawberry.type
class Mutation1:
    @strawberry.mutation
    def create_user(self, info, name: str, age: int) -> User:
        return User(name=name, age=age)


from .model.ck_server import ServerMutation, ServerQuery

@strawberry.type
class Query(Query1, Query2, ServerQuery):
    pass

@strawberry.type
class Mutation(Mutation1, ServerMutation):
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQL(schema)

