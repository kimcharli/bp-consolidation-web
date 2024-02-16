import logging
from typing import Optional, Dict, Any, List
import json
import asyncio
from enum import StrEnum
from dataclasses import dataclass, field, asdict
from datetime import datetime

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint, CkEnum


sse_queue = asyncio.Queue()

# def get_timestamp() -> str:
#     timestamp = datetime.now().strftime('%H:%M:%S:%f')
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
    element: Optional[str] = None
    selected: Optional[bool] = None
    do_remove: Optional[bool] = None
    just_value: Optional[bool] = None  # to reset file upload
    add_text: str = '' # to add text to the value

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
        # logging.info(f"SseEventData.disable() ######## {self=}")
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

    def remove(self):
        self.do_remove = True
        return self
  

# https://html.spec.whatwg.org/multipage/server-sent-events.html
@dataclass
class SseEvent:
    data: SseEventData
    # event: str = field(default_factory=SseEventEnum.DATA_STATE)     # SseEventEnum.DATA_STATE, SseEventEnum.TBODY_GS, SseEventEnum.BUTTION_DISABLE
    event: str = 'data-state'    # SseEventEnum.DATA_STATE, SseEventEnum.TBODY_GS, SseEventEnum.BUTTION_DISABLE

    async def send(self):
        await asyncio.sleep(0.05)
        try:
            sse_dict = {'event': self.event, 'data': json.dumps(asdict(self.data))}
        except Exception as e:
            logging.error(f"SseEvent.send() {e=} {self}")
            return
        # logging.info(f"######## SseEvent put {sse_queue.qsize()=} {self=}")        
        await sse_queue.put(sse_dict)
    
    # async def event_box(self, text):
    #     self.data=SseEventData(id='event-box-text').add_text(text + '\n')
    #     await self.send()


async def sse_logging(text, logger=None):
    if logger:
        logger.info(text)
    else:
        logging.info(text)
    await SseEvent(data=SseEventData(id='event-box-text', add_text=f"{datetime.now():%H:%M:%S:%f} {text}\n")).send()

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
    tor_bp: str
    main_bp: str = 'ATLANTA-Master'
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
    tor_id: str  # the id from tor blueprint. for switch href
    main_id: str = None  # the if from main blueprint. for switch href
    # asn: str = field(default_factory='')  # this is not used in 4.1.2

@dataclass
class TorGS:
    """
    The generic system present in the main blueprint to represent the TOR
    """
    label: str  # the label captured by init_leaf_switches
    link_ids: List[str]  # tor_gs links, the link ids captured by init_leaf_switches
    tor_id: str = None  # the old_id and old_ae_id will be updated by the main_bp
    tor_ae_id: str = None
    prefix: str = None

@dataclass
class GlobalStore:
    apstra: ApstraServer
    target: BpTarget
    lldp: Dict[str, List[LinkLldp]]  # leaf: []

    stop_signal: bool = True  # True on load, enable on start of work, to cancel the tasks. set by disconnect and reset_tor_data
    apstra_server: Any = None  #  ApstaServer
    bp: Dict[str, Any] = field(default_factory=dict)  # main_bp, tor_bp (CkApstraBlueprint)
    tor_data: dict = field(default_factory=dict)  # 
    logger: Any = logging.getLogger("GlobalStore")  # logging.Logger
    data: dict = field(default_factory=dict)
    migration_status: MigrationStatus = None  # set by post_init

    accessSwitchWorker: Any = None
    access_switches: Dict[str, AccessSwitch] = None  # created by GenericSystemWorker::sync_tor_generic_systems

    genericSystemWorker: Any = None # initiated by main.py::sync, can be reset by main.py::login_tor_bp
    generic_systems: Any = None  # created by GenericSystemWorker::sync_tor_generic_systems

    virtualNetworks: Any = None  # initiated by main.py::sync, can be reset by main.py::login_tor_bp
    virtual_networks: Any = None

    tor_gs: TorGS = None  # created by GenericSystemWorker::sync_tor_generic_systems, updated by init_leaf_switches
    leaf_switches: Dict[str, LeafSwitch] = None  # created by GenericSystemWorker::init_leaf_switches
    ctWorker: Any = None

    @property
    def bound_to(self):
        return f"{self.tor_gs.label}-pair"

    @property
    def access_switch_pair(self):
        return sorted(self.access_switches)

    @property
    def leaf_switch_pair(self):
        return sorted(self.leaf_switches)

    @property
    def apstra_url(self):
        return f"https://{self.apstra['host']}:{self.apstra['port']}"

    async def sse_logging(self, text):
        await sse_logging(text, self.logger)

    async def post_init(self):
        self.migration_status = MigrationStatus()

    async def login_server(self) -> str:
        await self.sse_logging(f"login_server()")
        self.apstra_server = CkApstraSession(self.apstra['host'], int(self.apstra['port']), self.apstra['username'], self.apstra['password'])
        await self.sse_logging(f"login_server(): {self.apstra_server=}")
        return self.apstra_server.version

    def logout_server(self):
        # self.logout_blueprint()
        self.stop_signal = True
        if self.apstra_server:
            self.apstra_server.logout() 
        self.apstra_server = None
        return

    async def login_blueprint(self):
        await self.sse_logging(f"login_blueprint")
        for role in ['main_bp', 'tor_bp']:
            label = self.target[role]
        # role = blueprint.role
        # label = blueprint.label
            bp = CkApstraBlueprint(self.apstra_server, label)
            self.bp[role] = bp
            await self.sse_logging(f"login_blueprint {bp=}")
            id = bp.id
            # apstra_url = self.apstra_server.url_prefix[:-4]
            value = f'<a href="{self.apstra_url}/#/blueprints/{id}/staged" target="_blank">{label}</a>'
            # data = { "id": id, "url": url, "label": label }
            await SseEvent(data=SseEventData(id=role, value=value).done()).send()
            await SseEvent(data=SseEventData(id=role).done()).send()
            await self.sse_logging(f"login_blueprint() end")
        return

    #
    # compare configuration
    # 
    async def compare_config(self):
        access_switches = self.access_switches
        main_bp = self.bp['main_bp']
        tor_bp = self.bp['tor_bp']

        switch_configs = { 'main': {}, 'tor': {} }
        for index, (switch) in enumerate(access_switches.values()):
            main_confg = main_bp.get_item(f"nodes/{switch.main_id}/config-rendering")['config']
            switch_main_href = f"{self.apstra_url}/#/blueprints/{main_bp.id}/staged/physical/selection/node-preview/{switch.main_id}"
            await SseEvent(data=SseEventData(
                id=f"main-config-text-{index}", value=main_confg)).send()
            await SseEvent(
                           data=SseEventData(id=f"main-config-caption-{index}").set_href(switch_main_href)).send()
            
            switch_tor_href = f"{self.apstra_url}/#/blueprints/{tor_bp.id}/staged/physical/selection/node-preview/{switch.tor_id}"
            tor_confg = tor_bp.get_item(f"nodes/{switch.tor_id}/config-rendering")['config']
            await SseEvent(data=SseEventData(
                id=f"tor-config-text-{index}", value=tor_confg)).send()
            await SseEvent(
                           data=SseEventData(id=f"tor-config-caption-{index}").set_href(switch_tor_href).set_target()).send()

        await SseEvent(data=SseEventData(id='compare-config').done()).send()


    #
    # Tor blueprint selection
    #    
    async def tor_bp_selection(self):
        blueprints = self.apstra_server.get_items('blueprints')
        for bp in blueprints['items']:
            label = bp['label']
            if bp['design'] == 'two_stage_l3clos':
                if label == self.target['tor_bp']:
                    await SseEvent(data=SseEventData(id='tor_bp_select', element='option', value=label, selected=True)).send()
                else:
                    await SseEvent(data=SseEventData(id='tor_bp_select', element='option', value=label)).send()
        # self.logger.info(f"tor_bp_selection(): {blueprints['items'][0]=}")        
        return

    async def reset_tor_data(self):
        await self.sse_logging(f"reset_tor_data() begin")
        await SseEvent(data=SseEventData(id='main-config-text-0', value='')).send()
        await SseEvent(data=SseEventData(id='tor-config-text-0', value='')).send()
        await SseEvent(data=SseEventData(id='main-config-text-1', value='')).send()
        await SseEvent(data=SseEventData(id='tor-config-text-1', value='')).send()

        if self.virtualNetworks:
            await self.virtualNetworks.remove()
            self.virtual_networks = None
            self.virtualNetworks = None

        if self.genericSystemWorker:
            await self.genericSystemWorker.remove()
            self.generic_systems = None
            self.genericSystemWorker = None

        if self.accessSwitchWorker:
            await self.accessSwitchWorker.remove()
            self.access_switches = None
            self.accessSwitchWorker = None

        await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_SYNC_STATE).init()).send()
        await SseEvent(data=SseEventData(id='connect').init()).send()

        self.tor_gs = None
        self.leaf_switches = None
        self.ctWorker = None
        self.tor_data = {}
        self.migration_status = MigrationStatus()

        await self.sse_logging(f"reset_tor_data() end")
        pass

    async def login_tor_blueprint(self, tor_bp_label: str):
        await self.sse_logging(f"login_tor_blueprint {tor_bp_label=}")
        self.stop_signal = True
        self.target['tor_bp'] = tor_bp_label
        self.bp['tor_bp'] = CkApstraBlueprint(self.apstra_server, tor_bp_label)
        # self.logger.info(f"login_tor_blueprint {self.bp['tor_bp']=}")
        # id = self.bp['tor_bp'].id
        # value = f'<a href="{self.apstra_url}/#/blueprints/{id}/staged" target="_blank">{tor_bp_label}</a>'
        # await SseEvent(data=SseEventData(id='tor_bp', value=value).done()).send()
        await SseEvent(data=SseEventData(id='tor_bp').done()).send()
        return

global_store: GlobalStore = None  # initialized by main.py
