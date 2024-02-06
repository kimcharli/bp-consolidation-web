import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator
import json
import time
import asyncio
from enum import StrEnum
from datetime import datetime
from dataclasses import dataclass, field

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint, CkEnum
# from .generic_systems import GenericSystems


sse_queue = asyncio.Queue()

def get_timestamp() -> str:
    timestamp = datetime.now().strftime('%Y%m%d %H:%M:%S:%f')
    return timestamp

class DataStateEnum(StrEnum):
    LOADED = 'done'
    INIT = 'init'
    LOADING = 'loading'
    DONE = 'done'
    ERROR = 'error'
    NONE = 'none'
    DISABLED = 'disabled'
    DATA_STATE = 'data-state'

class CtEnum(StrEnum):
    INTERFACE_NODE = 'interface'
    CT_NODE = 'batch'
    SINGLE_VLAN_NODE = 'AttachSingleVLAN'
    VN_NODE = 'virtual_network'
    EPAE_NODE = 'ep_application_instance'


class SseEventEnum(StrEnum):
    DATA_STATE = 'data-state'  # generic system data state
    TBODY_GS = 'tbody-gs'  # create generic system as tbody
    # BUTTION_DISABLE = 'disable-button'
    BUTTON_SYNC_STATE = 'sync'
    BUTTON_MIGRATE_AS = 'migrate-access-switches'
    BUTTON_MIGRATE_GS = 'migrate-generic-systems'
    BUTTON_MIGRATE_VN = 'migrate-virtual-networks'
    BUTTON_MIGRATE_CT = 'migrate-cts'
    BUTTON_COMPARE_CONFIG = 'compare-config'
    CAPTION_GS = 'generic-systems-caption'
    CAPTION_VN = 'virtual-networks-caption'
    TEXT_MAIN_CONFIG = 'main-config-text'
    TEXT_TOR_CONFIG = 'tor-config-text'


class SseEventData(BaseModel):
    id: str
    state: Optional[str] = None
    value: Optional[str] = None
    disabled: Optional[bool] = None  # for disable button
    visibility: Optional[bool] = None # for visable button
    href: Optional[str] = None
    target: Optional[str] = None

    def visible(self):
        self.visibility = 'visible'
        return self
    
    def hidden(self):
        self.visibility = 'hidden'
        return self

    def loading(self):
        self.state = DataStateEnum.LOADING
        return self    

    def done(self):
        self.disabled = False
        self.state = DataStateEnum.DONE
        return self

    def not_done(self):
        self.state = DataStateEnum.INIT
        return self

    def error(self):
        self.state = DataStateEnum.ERROR
        return self

    def disable(self):
        self.disabled = True
        self.state = DataStateEnum.DISABLED
        # logging.warning(f"SseEventData.disable() ######## {self=}")
        return self
    
    def enable(self):
        self.disabled = False
        return self
    
    def set_href(self, href):
        self.href = href
        return self
    
    def set_target(self, target='_blank'):
        self.target = target
        return self

# https://html.spec.whatwg.org/multipage/server-sent-events.html
class SseEvent(BaseModel):
    event: str = SseEventEnum.DATA_STATE     # SseEventEnum.DATA_STATE, SseEventEnum.TBODY_GS, SseEventEnum.BUTTION_DISABLE
    data: SseEventData

    async def send(self):
        await asyncio.sleep(0.05)
        sse_dict = {'event': self.event, 'data': json.dumps(dict(self.data))}
        logging.warning(f"######## SseEvent put {get_timestamp()} {sse_queue.qsize()=} {self=}")        
        await sse_queue.put(sse_dict)


class MigrationStatus(BaseModel):
    """
    Trace and manage the migration status
    The migration button will be controlled by this class
    """
    is_sync_done: bool = False
    is_as_done: bool = False
    is_gs_done: bool = False
    is_vn_done: bool = False
    is_ct_done: bool = False

    async def refresh(self):
        """
        Update all the button status

        """
        if self.is_as_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_AS).done()).send()
            if self.is_gs_done:
                await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_GS).done()).send()
                if self.is_vn_done:
                    await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).done()).send()
                    if self.is_ct_done:
                        await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).done()).send()
                    else:
                        await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).not_done()).send()
                else:
                    # vn not done
                    await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).not_done()).send()
                    await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).disable()).send()
            else:
                # gs not done
                await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_GS).not_done()).send()
                await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).disable()).send()
                await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).disable()).send()

        else:
            # AS is not done
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_AS).not_done().enable()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_GS).not_done().disable()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).not_done().disable()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).not_done().disable()).send()

    async def set_sync_done(self):
        self.is_sync_done = True
        await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_SYNC_STATE).done().enable()).send()
        # GS may be done when sync is done
        # DO NOT DO THIS: await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_AS).enable().not_done()).send()

    async def set_as_done(self, is_as_done: bool):
        """
        Set AS done, and set GS init
        """
        if is_as_done != self.is_as_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_AS).enable().done()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_GS).enable().not_done()).send()

    async def set_gs_done(self, is_gs_done: bool):
        """
        Set GS done, and set VN init
        """
        if is_gs_done != self.is_gs_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_GS).done()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).not_done().enable()).send()

    async def set_vn_done(self, is_vn_done: bool):
        """
        Set VN done, and set CT init
        """
        if is_vn_done != self.is_vn_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).done()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).not_done().enable()).send()

    async def set_ct_done(self, is_ct_done: bool):
        """
        Set VN done, and set CT init
        """
        if is_ct_done != self.is_ct_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).done()).send()
            # await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).done()).send()

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

# class EnvIni(BaseModel):
#     logger: Any = logging.getLogger("EnvIni")  # logging.Logger
#     host: str = None
#     port: int = None
#     username: str = None
#     password: str  = None
#     main_bp_label: str = None
#     tor_bp_label: str = None
    
#     @property
#     def url(self) -> str:
#         if not self.host or not self.port:
#             self.logger.warning(f"get_url() {self.host=} {self.port=}")
#             return
#         return f"https://{self.host}:{self.port}"

#     def clear(self):
#         self.host = None
#         self.port = None
#         self.username = None
#         self.password = None
#         self.main_bp_label = None
#         self.tor_bp_label = None

#     def update(self, data=None) -> dict:
#         """
#         Update the environment variables from the file_content, and return the updated dict.
#         """
#         # self.clear()
#         self.logger.warning(f"update(): cleared: {self.__dict__}, {data=} {type(data)=} {type(data).__name__=}")
#         if type(data).__name__ == 'ServerItem':
#             self.host = data.host
#             self.port = data.port
#             self.username = data.username
#             self.password = data.password
#             self.main_bp_label = data.main_bp_label
#             self.tor_bp_label = data.tor_bp_label
#             return self
        
#         # upload case
#         file_content = data
#         lines = file_content.decode('utf-8').splitlines() if file_content else []
#         for line in lines:
#             name_value = line.split("=")
#             if len(name_value) != 2:
#                 self.logger.warning(f"update(): invalid line: {line}")
#                 continue
#             if name_value[0] == "apstra_server_host":
#                 self.host = name_value[1]
#             elif name_value[0] == "apstra_server_port":
#                 self.port = int(name_value[1])
#             elif name_value[0] == "apstra_server_username":
#                 self.username = name_value[1]
#             elif name_value[0] == "apstra_server_password":
#                 self.password = name_value[1]
#             elif name_value[0] == "main_bp":
#                 self.main_bp_label = name_value[1]
#             elif name_value[0] == "tor_bp":
#                 self.tor_bp_label = name_value[1]
#             else:
#                 self.logger.warning(f"update(): invalid name: {name_value}")        
#         # self.logger.warning(f"update(): after update: {self.__dict__}")
#         # return_content = {
#         #     "host": self.host,
#         #     "port": self.port,
#         #     "username": self.username,
#         #     "password": self.password,
#         #     "main_bp_label": self.main_bp_label,
#         #     "tor_bp_label": self.tor_bp_label,
#         # }
#         # return return_content
#         return self

@dataclass
class LinkLldp:
    neighbor_interface_name: str
    neighbor_system_id: str
    interface_name: str
@dataclass
class BpTarget:
    main_bp: str = 'ATLANTA-Master'
    tor_bp: str = 'AZ-1_1-R5R15'
    tor_im_new: str = '_ATL-AS-5120-48T'
    cabling_maps_yaml_file: str = 'tests/fixtures/sample-cabling-maps.yaml'


@dataclass
class ApstraServer:
    host: str
    port: str
    username: str
    password: str
    logging_level: str = 'DEBUG'
    apstra_server: Any = None  # CkApstraSession

@dataclass
class GlobalStore:
    apstra: ApstraServer
    target: BpTarget
    lldp: Dict[str, List[LinkLldp]]  # leaf: []

    apstra_server: Any = None  #  ApstaServer
    bp: Dict[str, Any] = field(default_factory=dict)  # main_bp, tor_bp (CkApstraBlueprint)
    # main_bp = None  # ApstaBlueprint
    # tor_bp = None  # ApstaBlueprint
    tor_data: dict = field(default_factory=dict)  # 
    # env_ini: EnvIni = EnvIni()
    logger: Any = logging.getLogger("GlobalStore")  # logging.Logger
    data: dict = field(default_factory=dict)
    migration_status: MigrationStatus = field(default_factory=MigrationStatus)
    access_switches: Any = None  # created by main.py::sync() AccessSwitches
    generic_systems: Any = None  # created by access_switches GenericSystems
    

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

    @property
    def access_switch_pair(self):
        return sorted(self.access_switches.access_switches)

    # def update_env_ini(self, data):  
    #     self.logger.warning(f"update_env_ini(): {data=}")
    #     self.env_ini.update(data)
    #     return
    
    # def replace_env_ini(self, env_ini: EnvIni):
    #     self.env_ini = env_ini

    def login_server(self) -> str:
        self.logger.warning(f"login_server()")
        self.apstra_server = CkApstraSession(self.apstra['host'], int(self.apstra['port']), self.apstra['username'], self.apstra['password'])
        self.logger.warning(f"login_server(): {self.apstra_server=}")
        return self.apstra_server.version

    def logout_server(self):
        # self.logout_blueprint()
        if self.apstra_server:
            self.apstra_server.logout() 
        self.apstra_server = None
        return

    async def login_blueprint(self):
        self.logger.warning(f"login_blueprint")
        for role in ['main_bp', 'tor_bp']:
            label = self.target[role]
        # role = blueprint.role
        # label = blueprint.label
            bp = CkApstraBlueprint(self.apstra_server, label)
            self.bp[role] = bp
            self.logger.warning(f"login_blueprint {bp=}")
            id = bp.id
            apstra_url = self.apstra_server.url_prefix[:-4]
            value = f'<a href="{apstra_url}/#/blueprints/{id}/staged" target="_blank">{label}</a>'
            # data = { "id": id, "url": url, "label": label }
            await SseEvent(data=SseEventData(id=role, value=value).done()).send()
            self.logger.warning(f"login_blueprint() end")
        return
    
    # @classmethod
    # def logout_blueprint(cls):
    #     cls.bp = {}
    #     return


# def pull_interface_vlan_table(the_bp, switch_label_pair: list) -> dict:
#     """
#     Pull the single vlan cts for the switch pair

#     The return data
#     <system_label>:
#         <if_name>:
#             CkEnum.TAGGED_VLANS: []
#             CkEnum.UNTAGGED_VLAN: None
#     redundancy_group:
#         <ae_id>:
#             CkEnum.TAGGED_VLANS: []
#             CkEnum.UNTAGGED_VLAN: None
#     """
#     interface_vlan_table = {
#         CkEnum.REDUNDANCY_GROUP: {
#         }

#     }

#     INTERFACE_NODE = 'interface'
#     CT_NODE = 'batch'
#     SINGLE_VLAN_NODE = 'AttachSingleVLAN'
#     VN_NODE = 'virtual_network'

#     interface_vlan_query = f"""
#         match(
#             node('ep_endpoint_policy', policy_type_name='batch', name='{CT_NODE}')
#                 .in_().node('ep_application_instance', name='ep_application_instance')
#                 .out('ep_affected_by').node('ep_group')
#                 .in_('ep_member_of').node(name='{INTERFACE_NODE}'),
#             node(name='ep_application_instance')
#                 .out('ep_nested').node('ep_endpoint_policy', policy_type_name='AttachSingleVLAN', name='{SINGLE_VLAN_NODE}')
#                 .out('vn_to_attach').node('{VN_NODE}', name='virtual_network'),
#             optional(
#                 node(name='{INTERFACE_NODE}')
#                 .out('composed_of').node('interface', name='ae')
#                 ),
#             optional(
#                 node(name='{INTERFACE_NODE}')
#                 .in_('hosted_interfaces').node('system', system_type='switch', label=is_in({switch_label_pair}), name='switch')
#                 )            
#         )
#     """

#     interface_vlan_nodes = the_bp.query(interface_vlan_query, multiline=True)
#     logging.warning(f"pull_interface_vlan_table(): {the_bp.label=} {interface_vlan_query=} {len(interface_vlan_nodes)=}")

#     for nodes in interface_vlan_nodes:
#         if nodes['ae']:
#             # INTERFACE_NODE is AE
#             ae_name = nodes['ae']['if_name']
#             if ae_name not in interface_vlan_table[CkEnum.REDUNDANCY_GROUP]:
#                 interface_vlan_table[CkEnum.REDUNDANCY_GROUP][ae_name] = {
#                     CkEnum.TAGGED_VLANS: [],
#                     CkEnum.UNTAGGED_VLAN: None,
#                 }
#             this_evpn_interface_data = interface_vlan_table[CkEnum.REDUNDANCY_GROUP][ae_name]

#         else:
#             system_label = nodes['switch']['label']
#             if system_label not in interface_vlan_table:
#                 interface_vlan_table[system_label] = {}
#             if_name = nodes[INTERFACE_NODE]['if_name']
#             if if_name not in interface_vlan_table[system_label]:
#                 interface_vlan_table[system_label][if_name] = {
#                     CkEnum.TAGGED_VLANS: [],
#                     CkEnum.UNTAGGED_VLAN: None,
#                 }
#             this_interface_data = interface_vlan_table[system_label][if_name]

#         vnid = int(nodes[VN_NODE]['vn_id'] )
#         is_tagged = 'vlan_tagged' in nodes[SINGLE_VLAN_NODE]['attributes']
#         if is_tagged:
#             if vnid not in this_evpn_interface_data[CkEnum.TAGGED_VLANS]:
#                 this_evpn_interface_data[CkEnum.TAGGED_VLANS].append(vnid)
#         else:
#             this_evpn_interface_data[CkEnum.UNTAGGED_VLAN] = vnid

#     summary = [f"{x}:{len(interface_vlan_table[x])}" for x in interface_vlan_table.keys()]
#     logging.warning(f"BP:{the_bp.label} {summary=}")

#     return interface_vlan_table

global_store: GlobalStore = None  # initialized by main.py
