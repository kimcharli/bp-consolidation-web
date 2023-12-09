import strawberry
from typing import List, Annotated, Union
import uuid
import dotenv
import os

from .ck_global import GlobalStore

from ck_apstra_api.apstra_session import CkApstraSession


@strawberry.type
class ApstaServer:
    id: str = strawberry.field(default_factory=lambda: str(uuid.uuid4()))
    host: str
    port: int
    username: str
    password: str
    session: strawberry.Private[CkApstraSession] = None

    def is_onlie(self):
        return self.session.is_online()

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
class ServerQuery:    
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
class ServerMutation:
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
