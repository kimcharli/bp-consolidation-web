import dotenv
import os
import logging
import uuid
import strawberry


class EnvIni:
    def __init__(self):
        self.logger = logging.getLogger("EnvIni")
        self.logger.warning(f"__init__(): before update: {self.__dict__}")
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.main_bp_label = None
        self.tor_bp_label = None
        self.update()
        self.logger.warning(f"__init__(): after update: {self.__dict__}")
    
    def update(self, file_content=None) -> dict:
        """
        Update the environment variables from the file_content, and return the updated dict.
        """
        self.logger.warning(f"update(): before update: {self.__dict__}, {file_content=}")
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
    main_bp = None  # ApstaBlueprint
    tor_bp = None  # ApstaBlueprint

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



