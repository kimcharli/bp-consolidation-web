import logging
from typing import Optional
from pydantic import BaseModel, field_validator

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint

class ServerItem(BaseModel):
    id: Optional[int] = None
    host: str
    port: int
    username: str
    password: str
    main_bp_label: Optional[str] = None
    tor_bp_label: Optional[str] = None

    @field_validator('id', 'port', mode='before')
    def convert_str_to_int(cls, value) -> int:
        return int(value)

class BlueprintItem(BaseModel):    
    label: str
    role: str

class EnvIni:
    def __init__(self, data = None):
        self.logger = logging.getLogger(f"EnvIni __init__() {data}")
        if data:
            self.host = data.host
            self.port = data.port
            self.username = data.username
            self.password = data.password
            self.main_bp_label = data.main_bp_label
            self.tor_bp_label = data.tor_bp_label
        else:
            self.clear()
            self.update()
    
    def clear(self):
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.main_bp_label = None
        self.tor_bp_label = None

    def get_url(self) -> str:
        if not self.host or not self.port:
            self.logger.warning(f"get_url() {self.host=} {self.port=}")
            return
        return f"https://{self.host}:{self.port}"

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
        # self.logger.warning(f"update(): after update: {self.__dict__}")
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
    def update_env_ini(cls, data):        
        cls.logger.warning(f"update_env_ini(): {data=}")
        cls.env_ini = EnvIni(data)
        return

    @classmethod
    def login_server(cls, server: ServerItem) -> dict:
        cls.logger.warning(f"login_server() {server=}")
        cls.apstra_server = CkApstraSession(server.host, int(server.port), server.username, server.password)
        cls.logger.warning(f"login_server(): {cls.apstra_server.__dict__}")
        return { "version": cls.apstra_server.version }

    @classmethod
    def logout_server(cls):
        cls.logout_blueprint()
        if cls.apstra_server:
            cls.apstra_server.logout() 
        cls.logger.warning(f"logout_server()")
        cls.apstra_server = None
        return

    @classmethod
    def login_blueprint(cls, blueprint: BlueprintItem):
        cls.logger.warning(f"login_blueprint {blueprint=} {cls.apstra_server=}")
        role = blueprint.role
        label = blueprint.label
        bp = CkApstraBlueprint(cls.apstra_server, label)
        cls.bp[role] = bp
        cls.logger.warning(f"login_blueprint {bp=}")
        id = bp.id
        url = f"{cls.env_ini.get_url()}/#/blueprints/{id}/staged"
        data = { "id": id, "url": url, "label": label }
        cls.logger.warning(f"login_blueprint() return: {data}")
        return data

    @classmethod
    def logout_blueprint(cls):
        cls.bp = {}
        return


    @classmethod
    def pull_tor_bp_data(cls):
        data = {
            'switches': [],
            'peer_link': {},  # <id>: { speed: 100G, system: { <label> : [ <intf> ] } }
            'servers': {},  # <server>: { links: {} }
            'vnis': [],
        }
        cls.logger.warning(f"{cls.bp=}")
        tor_bp = cls.bp['tor_bp']
        peer_link_query = "node('link',role='leaf_leaf',  name='link').in_('link').node('interface', name='intf').in_('hosted_interfaces').node('system', name='switch')"
        peer_link_nodes = tor_bp.query(peer_link_query)
        # cls.logger.warning(f"{peer_link_nodes=}")
        for link in peer_link_nodes:
            link_id = link['link']['id']
            # cls.logger.warning(f"{data=} {link_id=}")
            if link_id not in data['peer_link']:
                data['peer_link'][link_id] = { 'system': {} }
            link_data = data['peer_link'][link_id]
            # cls.logger.warning(f"{data=} {link_data=}")
            link_data['speed'] = link['link']['speed']
            switch_label = link['switch']['label']
            if switch_label not in data['switches']:
                data['switches'].append(switch_label)
            # cls.logger.warning(f"{data=} {switch_label=}")
            if switch_label not in link_data['system']:
                link_data['system'][switch_label] = []
            switch_data = link_data['system'][switch_label]
            switch_intf = link['intf']['if_name']
            switch_data.append(switch_intf)
        cls.logger.warning(f"{data=}")

        data['servers'] = cls.pull_server_links(tor_bp)

        data['vnis'] = [ x['vn']['vn_id'] for x in tor_bp.query("node('virtual_network', name='vn')") ]

        return data

    @classmethod
    def pull_server_links(cls, tor_bp):
        data = {}  # <server>: { links: {} }
        server_links_query = """
            match(
            node('system', system_type='server',  name='server').out().node('interface', if_type='ethernet', name='server-intf').out('link').node('link', name='link').in_('link').node('interface', name='switch-intf').in_('hosted_interfaces').node('system', system_type='switch', name='switch'),
            optional(
                node(name='switch-intf').in_().node('interface', name='ae')
                ),
            optional(
                node(name='ae').in_().node('interface', name='evpn')
                )
            )
            """
        servers_link_nodes = tor_bp.query(server_links_query, multiline=True)
        # for server_link in servers_link_nodes:
        #     server_label = server_link['server']['label']
        #     if server_label not in data:
        #         data[server_label] = { 'links': {} }  # <link_id>: {}
        #     server_data = data[server_label] 
        #     link_id = server_link['link']['id']
        #     if link_id not in server_data['links']:
        #         server_data['links'][link_id] = {}
        #     link_data = server_data['links'][link_id]
        #     link_data['speed'] = server_link['link']['speed']
        #     link_data['ae'] = server_link['ae']['if_name'] if server_link['ae'] else None
        #     link_data['switch'] = server_link['switch']['label']
        #     link_data['switch_intf'] = server_link['switch-intf']['if_name']
        #     link_data['server'] = server_link['server']['label']
        #     link_data['server_intf'] = server_link['server-intf']['if_name']            

        for server_link in servers_link_nodes:
            server_label = server_link['server']['label']
            if server_label not in data:
                data[server_label] = {}  # <link_id>: {}
            server_data = data[server_label]
            ae_name = server_link['ae']['if_name'] if server_link['ae'] else 'no-ae'
            if ae_name not in server_data:
                server_data[ae_name] = {'speed': server_link['link']['speed'], 'cst': [], 'links': []}  # speed, CTs, member_links
            ae_data = server_data[ae_name]
            link_data = {}
            link_data['switch'] = server_link['switch']['label']
            link_data['switch_intf'] = server_link['switch-intf']['if_name']
            link_data['server_intf'] = server_link['server-intf']['if_name']            
            ae_data['links'].append(link_data)

        return data
