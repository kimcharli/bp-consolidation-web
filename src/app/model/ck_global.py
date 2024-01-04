import dotenv
import os
import logging
import uuid
import strawberry
from pydantic import BaseModel

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint

class ServerItem(BaseModel):
    host: str
    port: str
    username: str
    password: str

class BlueprintItem(BaseModel):    
    label: str
    role: str

class EnvIni:
    def __init__(self):
        self.logger = logging.getLogger("EnvIni")
        # self.logger.warning(f"__init__(): before update: {self.__dict__}")
        self.clear()
        self.update()
        # self.logger.warning(f"__init__(): after update: {self.__dict__}")
    
    def clear(self):
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.main_bp_label = None
        self.tor_bp_label = None

    def update(self, file_content=None) -> dict:
        """
        Update the environment variables from the file_content, and return the updated dict.
        """
        # self.logger.warning(f"update(): before update: {self.__dict__}, {file_content=}")
        self.clear()
        # self.logger.warning(f"update(): cleared: {self.__dict__}, {file_content=}")
        lines = file_content.decode('utf-8').splitlines() if file_content else []
        for line in lines:
            name_value = line.split("=")
            if len(name_value) != 2:
                self.logger.warning(f"update(): invalid line: {line}")
                continue
            if name_value[0] == "apstra_server_host":
                self.host = name_value[1]
            elif name_value[0] == "apstra_server_port":
                self.port = int(name_value[1])
            elif name_value[0] == "apstra_server_username":
                self.username = name_value[1]
            elif name_value[0] == "apstra_server_password":
                self.password = name_value[1]
            elif name_value[0] == "main_bp":
                self.main_bp_label = name_value[1]
            elif name_value[0] == "tor_bp":
                self.tor_bp_label = name_value[1]
            else:
                self.logger.warning(f"update(): invalid name: {name_value}")        
        self.logger.warning(f"update(): after update: {self.__dict__}")
        return_content = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "main_bp_label": self.main_bp_label,
            "tor_bp_label": self.tor_bp_label,
        }
        return return_content

class GlobalStore:
    apstra_server = None  #  ApstaServer
    bp = {}  # main_bp, tor_bp
    # main_bp = None  # ApstaBlueprint
    # tor_bp = None  # ApstaBlueprint

    env_ini = EnvIni()
    
    logger = logging.getLogger("GlobalStore")
    data = {
    }

    @classmethod
    def get_blueprints(cls):
        cls.logger.warning(f"get_blueprints(): {cls.main_bp=} {cls.tor_bp=}")
        return [cls.main_bp, cls.tor_bp]

    @classmethod
    def set_data(cls, key, value):
        cls.logger.warning(f"set_data(): {key=} {value=}")
        cls.data[key] = value

    @classmethod
    def get_data(cls, key):
        cls.logger.warning(f"get_data(): {key=} {cls.data.get(key)=}")
        return cls.data.get(key)

    @classmethod
    def update_env_ini(cls):
        cls.logger.warning(f"update_env_ini(): {cls.env_ini.__dict__}")
        cls.env_ini.update()

    @classmethod
    def login_server(cls, server: ServerItem) -> dict:
        cls.apstra_server = CkApstraSession(server.host, int(server.port), server.username, server.password)
        cls.logger.warning(f"login_server(): {cls.apstra_server.__dict__}")
        return { "version": cls.apstra_server.version }

    @classmethod
    def logout_server(cls):
        cls.logout_blueprint()
        cls.apstra_server.logout() 
        cls.logger.warning(f"logout_server()")
        cls.apstra_server = None
        return

    @classmethod
    def login_blueprint(cls, blueprint: BlueprintItem):
        cls.bp[blueprint.role] = CkApstraBlueprint(cls.apstra_server, blueprint.label)
        id = cls.bp[blueprint.role].id
        cls.logger.warning(f"login_blueprint(): {cls.bp[blueprint.role]}, {id}")
        return { "id": id }

    @classmethod
    def logout_blueprint(cls):
        cls.bp = {}
        return


# @strawberry.interface
# class Node:
#     nodes = {}  # 
#     # id: strawberry.ID
#     id: str = strawberry.field(default_factory=lambda: str(uuid.uuid4()))

#     def __init__(self):
#         self.logger = logging.getLogger("Node")
#         # self.id = strawberry.field(default_factory=lambda: str(uuid.uuid4()))
#         Node.nodes[id] = self
#         self.logger.warning(f"__init__(): {self.__dict__}")



