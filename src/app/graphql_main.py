import logging
import strawberry
from typing import List, Annotated, Union
from strawberry.asgi import GraphQL
import uuid
import dotenv
import os
from ck_apstra_api.apstra_session import CkApstraSession

logger = logging.getLogger(__name__)


class GlobalStore:
    apstra_server = None  #  ApstaServer
    data = {
    }

    @classmethod
    def set_data(cls, key, value):
        cls.data[key] = value

    @classmethod
    def get_data(cls, key):
        return cls.data.get(key)


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
class ApstaServer:
    id: str = strawberry.field(default_factory=lambda: str(uuid.uuid4()))
    host: str
    port: int
    username: str
    password: str
    session: strawberry.Private[CkApstraSession] = None

@strawberry.type
class ApstraServerSuccess:
    host: str

@strawberry.type
class ApstraServerLoginFail:
    server: str
    error: str

Response = Annotated[
    Union[ApstraServerSuccess, ApstraServerLoginFail],
    strawberry.union("AsptraServerLoginResponse")
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
    
    @strawberry.field
    def server(self, info) -> ApstaServer:
        apstra_server = GlobalStore.apstra_server
        if apstra_server is None:
            dotenv.load_dotenv()
            host = os.getenv("apstra_server_host")
            port = int(os.getenv("apstra_server_port"))
            username = os.getenv("apstra_server_username")
            password = os.getenv("apstra_server_password")        
            apstra_server = ApstaServer(host=host, port=port, username=username, password=password)
            GlobalStore.apstra_server = apstra_server
            # apstra_servers.append(ApstaServer(host=host, port=port, username=username, password=password))
        return apstra_server

@strawberry.type
class Mutation1:
    @strawberry.mutation
    def create_user(self, info, name: str, age: int) -> User:
        return User(name=name, age=age)

@strawberry.type
class Mutation2:
    @strawberry.mutation
    def login_server(self, info, host: str, port: int, username: str, password: str) -> Response:
        apstra_session = CkApstraSession(host, port, username, password)
        GlobalStore.apstra_session = apstra_session
        apstra_server = ApstaServer(host=host, port=port, username=username, password=password)
        GlobalStore.apstra_server = apstra_server
        if apstra_session.token is not None:
            return ApstraServerSuccess(host=host)
        return ApstraServerLoginFail(server=host, error="Login failed")

    @strawberry.mutation
    def logout_server() -> ApstaServer:
        GlobalStore.apstra_session.logout()
        return GlobalStore.apstra_server


@strawberry.type
class Query(Query1, Query2):
    pass

@strawberry.type
class Mutation(Mutation1, Mutation2):
    pass
    # @strawberry.mutation
    # def create_user(self, info, name: str, age: int) -> User:
    #     return User(name=name, age=age)


schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQL(schema)

