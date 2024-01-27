import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator
import json
import time
import asyncio
from enum import StrEnum

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint, CkEnum
# from .generic_systems import GenericSystems


sse_queue = asyncio.Queue()

class DataStateEnum(StrEnum):
    LOADED = 'done'
    INIT = 'init'
    LOADING = 'loading'
    DONE = 'done'
    ERROR = 'error'
    DATA_STATE = 'data-state'


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

class EnvIni(BaseModel):
    logger: Any = logging.getLogger("EnvIni")  # logging.Logger
    host: str = None
    port: int = None
    username: str = None
    password: str  = None
    main_bp_label: str = None
    tor_bp_label: str = None
    
    @property
    def url(self) -> str:
        if not self.host or not self.port:
            self.logger.warning(f"get_url() {self.host=} {self.port=}")
            return
        return f"https://{self.host}:{self.port}"

    def clear(self):
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.main_bp_label = None
        self.tor_bp_label = None

    def update(self, data=None) -> dict:
        """
        Update the environment variables from the file_content, and return the updated dict.
        """
        # self.clear()
        self.logger.warning(f"update(): cleared: {self.__dict__}, {data=} {type(data)=} {type(data).__name__=}")
        if type(data).__name__ == 'ServerItem':
            self.host = data.host
            self.port = data.port
            self.username = data.username
            self.password = data.password
            self.main_bp_label = data.main_bp_label
            self.tor_bp_label = data.tor_bp_label
            return self
        
        # upload case
        file_content = data
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
        # return_content = {
        #     "host": self.host,
        #     "port": self.port,
        #     "username": self.username,
        #     "password": self.password,
        #     "main_bp_label": self.main_bp_label,
        #     "tor_bp_label": self.tor_bp_label,
        # }
        # return return_content
        return self

class GlobalStore(BaseModel):
    apstra_server: Any = None  #  ApstaServer
    bp: Dict[str, Any] = {}  # main_bp, tor_bp (CkApstraBlueprint)
    # main_bp = None  # ApstaBlueprint
    # tor_bp = None  # ApstaBlueprint
    tor_data: dict = {}  # 
    env_ini: EnvIni = EnvIni()
    logger: Any = logging.getLogger("GlobalStore")  # logging.Logger
    data: dict = {}

    # access_switches: Any = None  # AccessSwitches

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

    def update_env_ini(self, data):  
        self.logger.warning(f"update_env_ini(): {data=}")
        self.env_ini.update(data)
        return
    
    def replace_env_ini(self, env_ini: EnvIni):
        self.env_ini = env_ini

    def login_server(self, server: ServerItem) -> dict:
        self.logger.warning(f"login_server() {server=}")
        self.apstra_server = CkApstraSession(server.host, int(server.port), server.username, server.password)
        self.logger.warning(f"login_server(): {self.apstra_server.__dict__}")
        return { "version": self.apstra_server.version }

    @classmethod
    def logout_server(cls):
        cls.logout_blueprint()
        if cls.apstra_server:
            cls.apstra_server.logout() 
        cls.logger.warning(f"logout_server()")
        cls.apstra_server = None
        return

    def login_blueprint(self, blueprint: BlueprintItem):
        self.logger.warning(f"login_blueprint {blueprint=} {self.apstra_server=}")
        role = blueprint.role
        label = blueprint.label
        bp = CkApstraBlueprint(self.apstra_server, label)
        self.bp[role] = bp
        self.logger.warning(f"login_blueprint {bp=}")
        id = bp.id
        url = f"{self.env_ini.url}/#/blueprints/{id}/staged"
        data = { "id": id, "url": url, "label": label }
        self.logger.warning(f"login_blueprint() return: {data}")
        return data

    @classmethod
    def logout_blueprint(cls):
        cls.bp = {}
        return


    # @classmethod
    # def pull_tor_bp_data(cls):
    #     data = {
    #         'access_switches': [],  # the tor switches { label:, id:, }
    #         'leaf_switches': None,  # the leaf switches <leaf1,2>: { label:, id:, , links: [{ switch_intf:, server_intf}]}
    #         'tor_gs':{'label': None, 'id': None, 'ae_id': None},  # id and ae_id of main_bp
    #         'leaf_gs': {'label': None, 'intfs': [None] * 4},  # label:, intfs[a-48, a-49, b-48, b-49] - the generic system info for the leaf
    #         'peer_link': {},  # <id>: { speed: 100G, system: { <label> : [ <intf> ] } }
    #         'servers': {},  # <server>: { links: {} }
    #         'vnis': [],
    #         'tor_interface_nodes_in_main': None,
    #         'access_interface_nodes_in_main': None,
    #         'switch_pair_spec': None,
    #         }
    #     cls.logger.warning(f"{cls.bp=}")
    #     tor_bp = cls.bp['tor_bp']
    #     main_bp = cls.bp['main_bp']
    #     peer_link_query = "node('link',role='leaf_leaf',  name='link').in_('link').node('interface', name='intf').in_('hosted_interfaces').node('system', name='switch')"
    #     peer_link_nodes = tor_bp.query(peer_link_query)
    #     # cls.logger.warning(f"{peer_link_nodes=}")
    #     temp_access_switches = {}
    #     for link in peer_link_nodes:
    #         # register the switch label for further processing later
    #         switch_label = link['switch']['label']
    #         temp_access_switches[switch_label] = {'label': switch_label}
    #         link_id = link['link']['id']
    #         # peer_link 
    #         if link_id not in data['peer_link']:
    #             data['peer_link'][link_id] = { 'system': {} }
    #         link_data = data['peer_link'][link_id]
    #         # cls.logger.warning(f"{data=} {link_data=}")
    #         link_data['speed'] = link['link']['speed']
    #         # switch_label = link['switch']['label']
    #         # if switch_label not in data['access_switches']:
    #         #     data['access_switches'].append(switch_label)
    #         # cls.logger.warning(f"{data=} {switch_label=}")
    #         if switch_label not in link_data['system']:
    #             link_data['system'][switch_label] = []
    #         switch_data = link_data['system'][switch_label]
    #         switch_intf = link['intf']['if_name']
    #         switch_data.append(switch_intf)
    #     cls.logger.warning(f"{data=}")
    #     data['access_switches'] = sorted(temp_access_switches.items(), key=lambda item: item[0])
    #     access_switch_pair = sorted(temp_access_switches)

    #     #  setup tor_gs label from the name of tor_bp switches
    #     if data['access_switches'][0][0].endswith(('a', 'b')):
    #         data['tor_gs']['label'] = data['access_switches'][0][0][:-1]
    #     elif data['access_switches'][0][0].endswith(('c', 'd')):
    #         data['tor_gs']['label'] = data['access_switches'][0][0][:-1] + 'cd'
    #     else:
    #         logging.critical(f"switch names {data['switches']} does not ends with 'a', 'b', 'c', or 'd'!")

    #     data['servers'] = cls.pull_server_links(tor_bp)

    #     # set new_label per generic systems
    #     for old_label, server_data in data['servers'].items():
    #         server_data['new_label'] = cls.new_label(data['tor_gs']['label'], old_label)                            
        
    #     GenericSystems.pull_generic_systems(cls.bp['main_bp'], cls.bp['tor_bp'], data['tor_gs'], [x[0] for x in data['access_switches']])

    #     # update leaf_gs (the generic system in TOR bp for the leaf)
    #     for server_label, server_data in data['servers'].items():
    #         for group_link in server_data['group_links']:
    #             if group_link['ae_name']:
    #                 for member_link in group_link['links']:
    #                     if member_link['switch_intf'] in ['et-0/0/48', 'et-0/0/49']:
    #                         data['leaf_gs']['label'] = server_label
    #                         if member_link['switch'].endswith(('a', 'c')):  # left tor
    #                             if member_link['switch_intf'] == 'et-0/0/48':
    #                                 data['leaf_gs']['intfs'][0] = 'et-' + member_link['server_intf'].split('-')[1]
    #                             else:
    #                                 data['leaf_gs']['intfs'][1] = 'et-' + member_link['server_intf'].split('-')[1]
    #                         else:
    #                             if member_link['switch_intf'] == 'et-0/0/48':
    #                                 data['leaf_gs']['intfs'][2] = 'et-' + member_link['server_intf'].split('-')[1]
    #                             else:
    #                                 data['leaf_gs']['intfs'][3] = 'et-' + member_link['server_intf'].split('-')[1]


    #     data['vnis'] = [ x['vn']['vn_id'] for x in tor_bp.query("node('virtual_network', name='vn')") ]

    #     # get ct assigment and update the servers
    #     data['ct_table'] = pull_interface_vlan_table(tor_bp, [x[0] for x in data['access_switches']])
    #     for server_label in data['servers']:
    #         server_data = data['servers'][server_label]
    #         # breakpoint()
    #         for ae_data in server_data['group_links']:
    #             if ae_data['ae_name']:
    #                 # breakpoint()
    #                 ae_name = ae_data['ae_name']
    #                 if ae_name in data['ct_table'][CkEnum.REDUNDANCY_GROUP]:
    #                     ae_data[CkEnum.TAGGED_VLANS] = data['ct_table'][CkEnum.REDUNDANCY_GROUP][ae_name][CkEnum.TAGGED_VLANS]
    #                     ae_data[CkEnum.UNTAGGED_VLAN] = data['ct_table'][CkEnum.REDUNDANCY_GROUP][ae_name][CkEnum.UNTAGGED_VLAN]
    #             else:
    #                 # none AE, so it will be a single link
    #                 the_link = ae_data['links'][0]
    #                 the_switch = the_link['switch']
    #                 if the_switch in data['ct_table']:
    #                     the_if_name = the_link['switch_intf']
    #                     if the_if_name == data['ct_table'][the_switch]:
    #                         the_if_data = data['ct_table'][the_switch][the_if_name]
    #                         ae_data[CkEnum.TAGGED_VLANS] = the_if_data[CkEnum.TAGGED_VLANS]
    #                         ae_data[CkEnum.UNTAGGED_VLAN] = the_if_data[CkEnum.UNTAGGED_VLAN]

    #     # get leaf information from main BP
    #     tor_interface_nodes_in_main = main_bp.get_server_interface_nodes(data['tor_gs']['label'])
    #     if len(tor_interface_nodes_in_main):
    #         # tor_gs in main_bp
    #         tor_gs_node = main_bp.query(f"node('system', label='{data['tor_gs']['label']}', name='tor').out().node('interface', if_type='port_channel', name='evpn')")
    #         if len(tor_gs_node):
    #             data['tor_gs']['id'] = tor_gs_node[0]['tor']['id']
    #             data['tor_gs']['ae_id'] = tor_gs_node[0]['evpn']['id']
    #         logging.warning(f"pull_tor_bp_data {data['tor_gs']=} {tor_gs_node=}")
    #         leaf_temp = {
    #             # 'label': { 'label': None, 'id': None, 'links': []},
    #             # 'label': { 'label': None, 'id': None, 'links': []},
    #         }
    #         for member_intf_set in tor_interface_nodes_in_main:
    #             leaf_label = member_intf_set[CkEnum.MEMBER_SWITCH]['label']
    #             if leaf_label not in leaf_temp:
    #                 leaf_temp[leaf_label] = {
    #                     'label': leaf_label, 
    #                     'id': member_intf_set[CkEnum.MEMBER_SWITCH]['id'], 
    #                     'links': []}
    #             leaf_data = leaf_temp[leaf_label]
    #             leaf_data['links'].append({
    #                 'switch_intf': member_intf_set[CkEnum.MEMBER_INTERFACE]['if_name'],
    #                 'server_intf': member_intf_set[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'],
    #                 })
    #             data['tor_gs']['ae_id'] = member_intf_set[CkEnum.EVPN_INTERFACE]['id']
    #         logging.warning(f"pull_tor_bp_data {leaf_temp=}")
    #         data['leaf_switches'] = sorted(leaf_temp.items(), key=lambda item: item[0])

    #         data['switch_pair_spec'] = build_switch_pair_spec(tor_interface_nodes_in_main, data['tor_gs']['label'])
    #         data['tor_interface_nodes_in_main'] = tor_interface_nodes_in_main

    #     # TODO: get data when the access_switches are loaded in main_bp
    #     else:
    #         access_switch_query = f"""
    #             match(
    #                 node('system', system_type='switch', label=is_in({access_switch_pair}), name='ACCESS_SWITCH')
    #                     .out('hosted_interfaces').node('interface', name='ACCESS_INTF')
    #                     .out('link').node('link')
    #                     .in_('link').node('interface', name='LEAF_INTF')
    #                     .in_('hosted_interfaces').node('system', role='leaf', name='LEAF'),
    #                 optional(
    #                     node(name='ACCESS_INTF').in_().node('interface', name='ACCESS_AE')
    #                 )
    #             )
    #         """
    #         # access_switch_nodes = main_bp.query(f"node('system', label=is_in({access_switch_pair}), name='switch')")
    #         access_switch_nodes = main_bp.query(access_switch_query, multiline=True)
    #         access_switches = {x['ACCESS_SWITCH']['label']: {
    #             'label': x['ACCESS_SWITCH']['label'],
    #             'id': x['ACCESS_SWITCH']['id'],
    #             } for x in access_switch_nodes}
    #         data['access_switches'] = sorted(access_switches.items())
    #         leaf_switches = {x['LEAF']['label']: {
    #             'label': x['LEAF']['label'],
    #             'id': x['LEAF']['id'],
    #             } for x in access_switch_nodes}
    #         data['leaf_switches'] = sorted(leaf_switches.items())
    #         access_interface_nodes_in_main = main_bp.get_switch_interface_nodes([x[0] for x in data['access_switches']])
    #         data['access_interface_nodes_in_main'] = access_interface_nodes_in_main

    #     cls.tor_data = data
    #     return data

    
    @classmethod
    def new_label(cls, tor_name, old_label) -> str:
        """
        return new label from old label
        """
        # the maximum length is 32. Prefix 'r5r14-'
        old_patterns = ['_atl_rack_1_000_', '_atl_rack_1_001_', '_atl_rack_5120_001_']
        # get the prefix from tor_name
        prefix = tor_name[len('atl1tor-'):]
        for pattern in old_patterns:
            if old_label.startswith(pattern):
                # replace the string with the prefix
                return f"{prefix}-{old_label[len(pattern):]}"
        # it doesn't starts with the patterns. See if it is too long to prefix
        max_len = 32
        if ( len(old_label) + len(prefix) + 1 ) > max_len:
            # TODO: potential of conflict
            # logging.warning(f"Generic system name {old_label=} is too long to prefix. Keeping original label.")
            return old_label
        # just prefix
        return f"{prefix}-{old_label}"


    # @classmethod
    # def pull_server_links(cls, tor_bp) -> dict:
    #     """
    #     return the server and link data
    #     data = {
    #         <server>:
    #             new_label,
    #             group_links: [
    #                 {
    #                     ae_name: aeN or ''
    #                     speed:,
    #                     CkEnum.TAGGED_VLANS: [],
    #                     CkEnum.UNTAGGED_VLAN:,
    #                     links: [ server_intf:, switch:, switch_intf:]
    #                 }
    #             ]
    #     }
    #     """
    #     data = {}  # <server>: { links: {} }
    #     server_links_query = """
    #         match(
    #         node('system', system_type='server',  name='server').out().node('interface', if_type='ethernet', name='server-intf').out('link').node('link', name='link').in_('link').node('interface', name='switch-intf').in_('hosted_interfaces').node('system', system_type='switch', name='switch'),
    #         optional(
    #             node(name='switch-intf').in_().node('interface', name='ae')
    #             ),
    #         optional(
    #             node(name='ae').in_().node('interface', name='evpn')
    #             )
    #         )
    #         """
    #     servers_link_nodes = tor_bp.query(server_links_query, multiline=True)
    #     for server_link in servers_link_nodes:
    #         server_label = server_link['server']['label']
    #         if server_label not in data:
    #             data[server_label] = {'new_label': None, 'group_links': []}  # <link_id>: {}
    #         server_data = data[server_label]            
    #         ae_name = server_link['ae']['if_name'] if server_link['ae'] else ''
    #         # logging.warning(f"pull_server_links() test1: {dict(server_data)=}")
    #         if ae_name:
    #             # breakpoint()
    #             ae_data = [x for x in server_data['group_links'] if x['ae_name'] == ae_name]
    #             if len(ae_data) == 0:
    #                 server_data['group_links'].append({'ae_name': ae_name, 'speed': server_link['link']['speed'], CkEnum.TAGGED_VLANS: [], CkEnum.UNTAGGED_VLAN: None, 'links': []})  # speed, CTs, member_links
    #                 ae_data = [x for x in server_data['group_links'] if x['ae_name'] == ae_name]
    #             link_data = {}
    #             link_data['switch'] = server_link['switch']['label']
    #             link_data['switch_intf'] = server_link['switch-intf']['if_name']
    #             link_data['server_intf'] = server_link['server-intf']['if_name']            
    #             ae_data[0]['links'].append(link_data)
    #         else:
    #             # breakpoint()
    #             ae_data = { 'ae_name': '', 'speed': server_link['link']['speed'], CkEnum.TAGGED_VLANS: [], CkEnum.UNTAGGED_VLAN: None, 'links': []}
    #             link_data = {}
    #             link_data['switch'] = server_link['switch']['label']
    #             link_data['switch_intf'] = server_link['switch-intf']['if_name']
    #             link_data['server_intf'] = server_link['server-intf']['if_name']            
    #             ae_data['links'].append(link_data)
    #             server_data['group_links'].append(ae_data)
                

    #     return data

    @classmethod
    def remove_old_generic_system_from_main(cls):
        """
        Remove the old generic system from the main blueprint
        remove the connectivity templates assigned to the generic system
        remove the generic system (links)
        """
        logging.warning('remove_old_generic_system_from_main - begin')
        tor_interface_nodes_in_main = cls.tor_data['tor_interface_nodes_in_main']
        tor_ae_id_in_main = cls.tor_data['tor_gs']['ae_id']
        main_bp = cls.bp['main_bp']
        if tor_ae_id_in_main is None:
            logging.warning(f"tor_ae_id_in_main is None")
            return
        
        # remove the connectivity templates assigned to the generic system
        cts_to_remove = main_bp.get_interface_cts(tor_ae_id_in_main)
        logging.warning(f"remove_old_generic_system_from_main - {tor_ae_id_in_main=} {len(cts_to_remove)=}")

        # damping CTs in chunks
        while len(cts_to_remove) > 0:
            throttle_number = 50
            cts_chunk = cts_to_remove[:throttle_number]
            logging.warning(f"Removing Connecitivity Templates on this links: {len(cts_chunk)=}")
            batch_ct_spec = {
                "operations": [
                    {
                        "path": "/obj-policy-batch-apply",
                        "method": "PATCH",
                        "payload": {
                            "application_points": [
                                {
                                    "id": tor_ae_id_in_main,
                                    "policies": [ {"policy": x, "used": False} for x in cts_chunk]
                                }
                            ]
                        }
                    }
                ]
            }
            batch_result = main_bp.batch(batch_ct_spec, params={"comment": "batch-api"})
            del cts_to_remove[:throttle_number]

        # remove the generic system (links)
        link_remove_spec = {
            "operations": [
                {
                    "path": "/delete-switch-system-links",
                    "method": "POST",
                    "payload": {
                        "link_ids": [ x['link']['id'] for x in tor_interface_nodes_in_main ]
                    }
                }
            ]
        }
        batch_result = main_bp.batch(link_remove_spec, params={"comment": "batch-api"})
        logging.debug(f"{link_remove_spec=}")
        while True:
            if_generic_system_present = main_bp.query(f"node('system', label='{cls.tor_data['tor_gs']['label']}')")
            if len(if_generic_system_present) == 0:
                break
            logging.info(f"{if_generic_system_present=}")
            time.sleep(3)
        # the generic system is gone.            

        return

    @classmethod
    def create_new_access_switch_pair(cls):
        ########
        # create new access system pair
        # olg logical device is not useful anymore

        # LD _ATL-AS-Q5100-48T, _ATL-AS-5120-48T created
        # IM _ATL-AS-Q5100-48T, _ATL-AS-5120-48T created
        # rack type _ATL-AS-5100-48T, _ATL-AS-5120-48T created and added
        # ATL-AS-LOOPBACK with 10.29.8.0/22
        
        main_bp = cls.bp['main_bp']
        tor_label = cls.tor_data['tor_gs']['label']
        switch_pair_spec = cls.tor_data['switch_pair_spec']

        REDUNDANCY_GROUP = 'redundancy_group'

        # skip if the access switch pair already exists
        tor_a = cls.tor_data['access_switches'][0][0]
        tor_b = cls.tor_data['access_switches'][1][0]
        if main_bp.get_system_node_from_label(tor_a):
            logging.info(f"{tor_a} already exists in main blueprint")
            return
        
        access_switch_pair_created = main_bp.add_generic_system(switch_pair_spec)
        logging.warning(f"{access_switch_pair_created=}")

        # wait for the new system to be created
        while True:
            new_systems = main_bp.query(f"""
                node('link', label='{access_switch_pair_created[0]}', name='link')
                .in_().node('interface')
                .in_().node('system', name='leaf')
                .out().node('redundancy_group', name='{REDUNDANCY_GROUP}'
                )""", multiline=True)
            # There should be 5 links (including the peer link)
            if len(new_systems) == 2:
                break
            logging.info(f"Waiting for new systems to be created: {len(new_systems)=}")
            time.sleep(3)

        # The first entry is the peer link

        # rename redundancy group with <tor_label>-pair
        main_bp.patch_node_single(
            new_systems[0][REDUNDANCY_GROUP]['id'], 
            {"label": f"{tor_label}-pair" }
            )

        # rename each access switch for the label and hostname
        for leaf in new_systems:
            given_label = leaf['leaf']['label']
            # when the label is <tor_label>1, rename it to <tor_label>a
            if given_label[-1] == '1':
                new_label = tor_a
            # when the labe is <tor_label>2, rename it to <tor_label>b
            elif given_label[-1] == '2':
                new_label = tor_b
            else:
                logging.warning(f"skipp chaning name {given_label=}")
                continue
            main_bp.patch_node_single(
                leaf['leaf']['id'], 
                {"label": new_label, "hostname": new_label }
                )


def build_access_switch_fabric_links_dict(a_link_nodes:dict) -> dict:
    '''
    Build each "links" data from tor_interface_nodes_in_main
    It is assumed that the generic system interface names are in et-0/0/48-b format
    '''
    # logging.debug(f"{len(a_link_nodes)=}, {a_link_nodes=}")

    translation_table = {
        "et-0/0/48-a": { 'system_peer': 'first', 'system_if_name': 'et-0/0/48' },
        "et-0/0/48-b": { 'system_peer': 'second', 'system_if_name': 'et-0/0/48' },
        "et-0/0/49-a": { 'system_peer': 'first', 'system_if_name': 'et-0/0/49' },
        "et-0/0/49-b": { 'system_peer': 'second', 'system_if_name': 'et-0/0/49' },

        "et-0/0/48a": { 'system_peer': 'first', 'system_if_name': 'et-0/0/48' },
        "et-0/0/48b": { 'system_peer': 'second', 'system_if_name': 'et-0/0/48' },
        "et-0/0/49a": { 'system_peer': 'first', 'system_if_name': 'et-0/0/49' },
        "et-0/0/49b": { 'system_peer': 'second', 'system_if_name': 'et-0/0/49' },
    }

    tor_intf_name = a_link_nodes[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name']
    if tor_intf_name not in translation_table:
        logging.warning(f"a_link_nodes[{CkEnum.GENERIC_SYSTEM_INTERFACE}]['if_name']: {tor_intf_name}, none of {[x for x in translation_table.keys()]}")
        return None
    link_candidate = {
            "lag_mode": "lacp_active",
            "system_peer": translation_table[tor_intf_name]['system_peer'],
            "switch": {
                "system_id": a_link_nodes[CkEnum.MEMBER_SWITCH]['id'],
                "transformation_id": 2,
                "if_name": a_link_nodes[CkEnum.MEMBER_INTERFACE]['if_name']
            },
            "system": {
                "system_id": None,
                "transformation_id": 1,
                "if_name": translation_table[tor_intf_name]['system_if_name']
            }
        }
    return link_candidate

def build_switch_pair_spec(tor_interface_nodes_in_main, tor_label) -> dict:
    '''
    Build the switch pair spec from the links query
    '''
    switch_pair_spec = {
        "links": [build_access_switch_fabric_links_dict(x) for x in tor_interface_nodes_in_main],
        "new_systems": None
    }

    # TODO: 
    with open('./tests/fixtures/fixture-switch-system-links-5120.json', 'r') as file:
        sample_data = json.load(file)

    switch_pair_spec['new_systems'] = sample_data['new_systems']
    switch_pair_spec['new_systems'][0]['label'] = tor_label

    return switch_pair_spec


def pull_interface_vlan_table(the_bp, switch_label_pair: list) -> dict:
    """
    Pull the single vlan cts for the switch pair

    The return data
    <system_label>:
        <if_name>:
            CkEnum.TAGGED_VLANS: []
            CkEnum.UNTAGGED_VLAN: None
    redundancy_group:
        <ae_id>:
            CkEnum.TAGGED_VLANS: []
            CkEnum.UNTAGGED_VLAN: None
    """
    interface_vlan_table = {
        CkEnum.REDUNDANCY_GROUP: {
        }

    }

    INTERFACE_NODE = 'interface'
    CT_NODE = 'batch'
    SINGLE_VLAN_NODE = 'AttachSingleVLAN'
    VN_NODE = 'virtual_network'

    interface_vlan_query = f"""
        match(
            node('ep_endpoint_policy', policy_type_name='batch', name='{CT_NODE}')
                .in_().node('ep_application_instance', name='ep_application_instance')
                .out('ep_affected_by').node('ep_group')
                .in_('ep_member_of').node(name='{INTERFACE_NODE}'),
            node(name='ep_application_instance')
                .out('ep_nested').node('ep_endpoint_policy', policy_type_name='AttachSingleVLAN', name='{SINGLE_VLAN_NODE}')
                .out('vn_to_attach').node('{VN_NODE}', name='virtual_network'),
            optional(
                node(name='{INTERFACE_NODE}')
                .out('composed_of').node('interface', name='ae')
                ),
            optional(
                node(name='{INTERFACE_NODE}')
                .in_('hosted_interfaces').node('system', system_type='switch', label=is_in({switch_label_pair}), name='switch')
                )            
        )
    """

    interface_vlan_nodes = the_bp.query(interface_vlan_query, multiline=True)
    logging.warning(f"pull_interface_vlan_table(): {the_bp.label=} {interface_vlan_query=} {len(interface_vlan_nodes)=}")

    for nodes in interface_vlan_nodes:
        if nodes['ae']:
            # INTERFACE_NODE is AE
            ae_name = nodes['ae']['if_name']
            if ae_name not in interface_vlan_table[CkEnum.REDUNDANCY_GROUP]:
                interface_vlan_table[CkEnum.REDUNDANCY_GROUP][ae_name] = {
                    CkEnum.TAGGED_VLANS: [],
                    CkEnum.UNTAGGED_VLAN: None,
                }
            this_evpn_interface_data = interface_vlan_table[CkEnum.REDUNDANCY_GROUP][ae_name]

        else:
            system_label = nodes['switch']['label']
            if system_label not in interface_vlan_table:
                interface_vlan_table[system_label] = {}
            if_name = nodes[INTERFACE_NODE]['if_name']
            if if_name not in interface_vlan_table[system_label]:
                interface_vlan_table[system_label][if_name] = {
                    CkEnum.TAGGED_VLANS: [],
                    CkEnum.UNTAGGED_VLAN: None,
                }
            this_interface_data = interface_vlan_table[system_label][if_name]

        vnid = int(nodes[VN_NODE]['vn_id'] )
        is_tagged = 'vlan_tagged' in nodes[SINGLE_VLAN_NODE]['attributes']
        if is_tagged:
            if vnid not in this_evpn_interface_data[CkEnum.TAGGED_VLANS]:
                this_evpn_interface_data[CkEnum.TAGGED_VLANS].append(vnid)
        else:
            this_evpn_interface_data[CkEnum.UNTAGGED_VLAN] = vnid

    summary = [f"{x}:{len(interface_vlan_table[x])}" for x in interface_vlan_table.keys()]
    logging.warning(f"BP:{the_bp.label} {summary=}")

    return interface_vlan_table

global_store = GlobalStore()
