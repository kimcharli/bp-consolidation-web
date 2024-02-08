import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator
import json
import time
import asyncio
from enum import StrEnum
from datetime import datetime
from dataclasses import dataclass, field, asdict

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint, CkEnum
# from .generic_systems import GenericSystems


sse_queue = asyncio.Queue()

# def get_timestamp() -> str:
#     timestamp = datetime.now().strftime('%Y%m%d %H:%M:%S:%f')
#     return timestamp

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
    UPDATE_VN = 'update-vn'  # generic system data state
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


@dataclass
class SseEventData:
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

    def init(self):
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
@dataclass
class SseEvent:
    data: SseEventData
    # event: str = field(default_factory=SseEventEnum.DATA_STATE)     # SseEventEnum.DATA_STATE, SseEventEnum.TBODY_GS, SseEventEnum.BUTTION_DISABLE
    event: str = 'data-state'    # SseEventEnum.DATA_STATE, SseEventEnum.TBODY_GS, SseEventEnum.BUTTION_DISABLE

    async def send(self):
        await asyncio.sleep(0.05)
        sse_dict = {'event': self.event, 'data': json.dumps(asdict(self.data))}
        # logging.warning(f"######## SseEvent put {sse_queue.qsize()=} {self=}")        
        await sse_queue.put(sse_dict)

@dataclass
class MigrationStatus:
    """
    Trace and manage the migration status
    The migration button will be controlled by this class
    """
    is_sync_done: bool = False
    is_as_done: bool = False
    is_gs_done: bool = False
    is_vn_done: bool = False
    is_ct_done: bool = False

    async def set_sync_done(self):
        self.is_sync_done = True
        await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_SYNC_STATE).done().enable()).send()
        # GS may be done when sync is done
        # DO NOT DO THIS: await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_AS).enable().init()).send()

    async def set_as_done(self, is_as_done: bool):
        """
        Set AS done, and set GS init
        """
        if is_as_done != self.is_as_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_AS).enable().done()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_GS).enable().init()).send()

    async def set_gs_done(self, is_gs_done: bool):
        """
        Set GS done, and set VN init
        """
        if is_gs_done != self.is_gs_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_GS).done()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).init().enable()).send()

    async def set_vn_done(self, is_vn_done: bool):
        """
        Set VN done, and set CT init
        """
        if is_vn_done != self.is_vn_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).done()).send()
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).init().enable()).send()

    async def set_ct_done(self, is_ct_done: bool):
        """
        Set VN done, and set CT init
        """
        if is_ct_done != self.is_ct_done:
            await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).done()).send()
            # await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).done()).send()

# @dataclass
# class ServerItem:
#     id: Optional[int] = None
#     host: str
#     port: int
#     username: str
#     password: str
#     main_bp_label: Optional[str] = None
#     tor_bp_label: Optional[str] = None

#     @field_validator('id', 'port', mode='before')
#     def convert_str_to_int(cls, value) -> int:
#         return int(value)

# class BlueprintItem(BaseModel):    
#     label: str
#     role: str

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
class LeafLink():
    leaf_intf: str
    tor_name: str
    leaf_intf_id: str = None
    tor_gs_name: str = None
    tor_gs_id: str = None
@dataclass
class LeafSwitch():
    label: str
    id: str
    links: Dict[str, LeafLink]  # a48, a49, b48, b49 : LeafLink

@dataclass
class AccessSwitch:
    label: str
    tor_id: str # for switch href
    main_id: str = None
    # asn: str = field(default_factory='')  # this is not used in 4.1.2

@dataclass
class TorGS:
    """
    The generic system present in the main blueprint to represent the TOR
    """
    label: str  # the label captured by init_leaf_switches
    link_ids: List[str]
    tor_id: str = None  # the old_id and old_ae_id will be updated by the main_bp
    tor_ae_id: str = None
    prefix: str = None

@dataclass
class GlobalStore:
    apstra: ApstraServer
    target: BpTarget
    lldp: Dict[str, List[LinkLldp]]  # leaf: []

    apstra_server: Any = None  #  ApstaServer
    bp: Dict[str, Any] = field(default_factory=dict)  # main_bp, tor_bp (CkApstraBlueprint)
    tor_data: dict = field(default_factory=dict)  # 
    logger: Any = logging.getLogger("GlobalStore")  # logging.Logger
    data: dict = field(default_factory=dict)
    migration_status: MigrationStatus = field(default_factory=MigrationStatus)

    accssSwitchWorker: Any = None
    access_switches: Dict[str, AccessSwitch] = None  # created by GenericSystemWorker::sync_tor_generic_systems

    genericSystemWorker: Any = None
    generic_systems: Any = None  # created by GenericSystemWorker::sync_tor_generic_systems

    virtualNetworks: Any = None
    virtual_networks: Any = None

    tor_gs: TorGS = None  # created by GenericSystemWorker::sync_tor_generic_systems, updated by init_leaf_switches
    leaf_switches: Dict[str, LeafSwitch] = None  # created by GenericSystemWorker::init_leaf_switches
    ctWorker: Any = None

    @property
    def bound_to(self):
        return f"{self.tor_gs.label}-pair"

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
        return sorted(self.access_switches)

    @property
    def leaf_switch_pair(self):
        return sorted(self.leaf_switches)

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
    
global_store: GlobalStore = None  # initialized by main.py
