import logging
import strawberry
from typing import List
from strawberry.asgi import GraphQL
import uuid
import dotenv
import os
from ck_apstra_api.apstra_session import CkApstraSession

logger = logging.getLogger(__name__)

class AppData:
    # session = None
    def __init__(self):
        pass

    def add_session(self, session):
        self.session = session


app_data = AppData()

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
    host: str
    port: int
    username: str
    password: str

apstra_servers = []

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
        logger.warning(f"SERVER: server begin")
        if len(apstra_servers) == 0:
            logger.warning(f"SERVER: no-server begin")
            dotenv.load_dotenv()
            host = os.getenv("apstra_server_host")
            port = int(os.getenv("apstra_server_port"))
            username = os.getenv("apstra_server_username")
            password = os.getenv("apstra_server_password")        
            logger.warning(f"SERVER: {host=}, {port=}, {username=}, {password=}")
            apstra_servers.append(ApstaServer(host=host, port=port, username=username, password=password))
        logger.warning(f"SERVER: server end {apstra_servers[0]=}")
        return apstra_servers[0]

@strawberry.type
class Mutation1:
    @strawberry.mutation
    def create_user(self, info, name: str, age: int) -> User:
        return User(name=name, age=age)

@strawberry.type
class Mutation2:
    @strawberry.mutation
    def login_server(self, info, host: str, port: int, username: str, password: str) -> ApstaServer:
        session = CkApstraSession(host, port, username, password)
        if session.token is not None:
            session_id = str(uuid.uuid4())       
            app_data.add_session(session)
            return ApstaServer(host=host, port=port, username=username, password=password)
        return None


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

