# from pydantic import BaseModel
from typing import Optional, List, Dict, Any, ClassVar
import logging
from enum import Enum, StrEnum, auto
import time
from dataclasses import dataclass, field

from ck_apstra_api.apstra_blueprint import CkEnum
from .ck_global import DataStateEnum, sse_queue, SseEvent, SseEventEnum, SseEventData, global_store, TorGS, AccessSwitch, LeafSwitch, LeafLink
from .vlan_cts import CtData
# TODO: consolidate
# TODO: catch AE creation delay
# TODO: generic systems done update


@dataclass
class _Memberlink():
    switch: str
    switch_intf: str
    old_tags: List[str] = None
    old_server_intf: str = ''  # DO NOT USE None
    # from main_bp
    new_tags: List[str] = None
    new_server_intf: str = ''  # DO NOT USE NONE
    new_link_id: Optional[str] = None   # main_id
    new_switch_intf_id: str = ''
    new_server_intf_id: str = ''

    def is_link_done(self) -> bool:
        if not self.new_switch_intf_id or self.old_tags != self.new_tags or self.old_server_intf != self.new_server_intf:
            return False
        return True
     
    def reset_to_tor_data(self):
        self.new_tags = []
        self.new_server_intf = ''
        self.new_link_id = None

    def interface_name_spec(self) -> dict:
        """
        Fix interface name. 
        """
        access_switches = global_store.access_switches
        if self.new_server_intf != self.old_server_intf:
            return {
                'id': self.new_link_id,
                'endpoints': [
                    {
                        'interface': {
                            'id': self.new_server_intf_id,
                            'if_name': self.old_server_intf
                        }
                    },
                    {
                        'interface': {
                            'id': self.new_switch_intf_id
                        }
                    }
                ]
            }
        return None

    def tr(self, is_leaf_gs) -> str:
        trs = []
        # The above code is not doing anything. It only contains the word "tags" and "
        tags_buttons_list = []        
        for i in self.old_tags:
            if i in self.new_tags:
                tags_buttons_list.append(f'<button type="button" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{i}</button>')
            else:
                tags_buttons_list.append(f'<button type="button" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{i}</button>')
        for i in self.new_tags:
            if i not in self.old_tags:
                tags_buttons_list.append(f'<button type="button" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.ERROR}">{i}</button>')
        tags_buttons = ''.join(tags_buttons_list)
        trs.append(f'<td data-cell="tags">{tags_buttons}</td>')
        # breakpoint()
        if is_leaf_gs:
            trs.append(f'<td data-cell="server_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.NONE}">{self.old_server_intf}</td>')
        elif self.new_link_id and self.old_server_intf == self.new_server_intf:
            trs.append(f'<td data-cell="server_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.old_server_intf}</td>')
        else:
            trs.append(f'<td data-cell="server_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.old_server_intf}</td>')
        if is_leaf_gs:
            trs.append(f'<td data-cell="switch" >{self.switch}</td>')
            trs.append(f'<td data-cell="switch_intf" >{self.switch_intf}</td>')
        elif self.new_link_id:
            trs.append(f'<td data-cell="switch" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.switch}</td>')
            trs.append(f'<td data-cell="switch_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.switch_intf}</td>')
        else:
            trs.append(f'<td data-cell="switch" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.switch}</td>')
            trs.append(f'<td data-cell="switch_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.switch_intf}</td>')
        return ''.join(trs)

    def add_old_tag(self, tag):
        # breakpoint()
        if tag  not in self.old_tags:
            self.old_tags.append(tag)

    def add_new_tag(self, tag):
        if tag not in self.new_tags:
            self.new_tags.append(tag)

    def add_tags(self) -> bool:
        """
        Do tagging. Retrun True if changed
        """        
        main_bp = global_store.bp['main_bp']
        if sorted(self.old_tags) != sorted(self.new_tags):
            main_bp.post_tagging( 
                [self.new_link_id], 
                tags_to_add = [x for x in self.old_tags if x not in self.new_tags],
                tags_to_remove = [x for x in self.new_tags if x not in self.old_tags]
                )
            return True
        return False


@dataclass
class _GroupLink():
    old_ae_id: str  # to use for ct_id
    speed: str
    old_ae_name: str = '' # the ae in the tor blueprint
    # cts: List[CtData] = []
    old_tagged_vlans: Dict[int, CtData] = None
    old_untagged_vlan: Dict[int, CtData] = None  # one entry at most
    links: Dict[str, _Memberlink] = None  # <member interface id from tor>: _Memberlink
    # from main_bp
    new_ae_name: str = ''  # the ae in the main blueprint
    new_ae_id: str = None  # the id of the ae link
    # new_tagged_vlans: Dict[int, CtData] = {}
    # new_untagged_vlan: Dict[int, CtData] = {}  # one entry at most
    # new_cts: Optional[List[int]] = []  # the connectivity templates in main blueprint  
    new_speed: str = None

    @property
    def rowspan(self) -> int:
        return len(self.links)

    @property
    def cts_cell_id(self) -> str:
        return f"ct-{self.old_ae_id}"

    @property
    def is_old_cts_absent(self) -> bool:
        return len(self.old_tagged_vlans) == 0 and len(self.old_untagged_vlan) == 0

    @property
    def count_of_old_cts(self) -> int:
        return len(self.old_tagged_vlans) + len(self.old_untagged_vlan)

    @property
    def count_of_new_cts(self) -> int:
        tagged_cts = [vn_id for vn_id, ct_data in self.old_tagged_vlans.items() if ct_data.new_ct_id is not None]
        untagged_cts = [vn_id for vn_id, ct_data in self.old_untagged_vlan.items() if ct_data.new_ct_id is not None]
        return len(tagged_cts) + len(untagged_cts)

    @property
    def is_ct_done(self) -> bool:
        tagged_cts_not_done = [vn_id for vn_id, ct_data in self.old_tagged_vlans.items() if ct_data.new_ct_id is None]
        untagged_cts_not_done = [vn_id for vn_id, ct_data in self.old_untagged_vlan.items() if ct_data.new_ct_id is None]
        is_is_ct_done =len(tagged_cts_not_done) == 0 and len(untagged_cts_not_done) == 0
        # logging.warning(f"is_ct_done {self.old_ae_id=} {is_is_ct_done=} {tagged_cts_not_done=} {untagged_cts_not_done=}")
        # if not is_is_ct_done:
        #     breakpoint()
        return is_is_ct_done

    def cts(self, is_leaf_gs):
        if is_leaf_gs:
            state_attribute = f'class="cts"'
        elif self.is_old_cts_absent:
            state_attribute = f'class="{DataStateEnum.DATA_STATE} cts" {DataStateEnum.DATA_STATE}="{DataStateEnum.NONE}"'
        elif self.is_ct_done:
            state_attribute = f'class="{DataStateEnum.DATA_STATE} cts" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}"'
        else:
            state_attribute = f'class="{DataStateEnum.DATA_STATE} cts" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}"'
        return f'<td rowspan={self.rowspan} id="{self.cts_cell_id}" data-cell="cts" {state_attribute}>{self.count_of_new_cts}/{self.count_of_old_cts}</td>'

    def is_ae_done(self) -> bool:
        if self.speed != self.new_speed:
            return False
        if self.new_ae_name != self.old_ae_name:
            return False
        for _, link in self.links.items():
            if not link.is_link_done():
                return False
        return True

    def reset_to_tor_data(self):
        self.new_ae_name = ''
        self.new_ae_id = None
        self.new_speed = None
        for _, ct_data in self.old_tagged_vlans.items():
            ct_data.reset()
        for _, ct_data in self.old_untagged_vlan.items():
            ct_data.reset()
        # self.old_untagged_vlan = {}
        # self.old_tagged_vlans
        # self.new_cts = []
        # self.new_tagged_vlans = {}
        # self.new_untagged_vlan = {}
        for _, link in self.links.items():
            link.reset_to_tor_data()

    def build_lag_spec(self):
        """
        Build LAG spec for each link if new_ae_id is absent
        """
        lag_spec = {}
        if self.old_ae_name != '' and not self.new_ae_id:
            lag_spec = {link.new_link_id: {
                'group_label': self.old_ae_name,
                'lag_mode': 'lacp_active'
            } for _, link in self.links.items()}
            self.new_ae_name = self.old_ae_name
        # breakpoint()
        return lag_spec        

    def add_tags(self):
        """
        Do tagging. Retrun True if changed
        """
        main_bp = global_store.bp['main_bp']
        changed = False
        for _, link in self.links.items():
            if link.add_tags():
                changed = True
        return changed


    def tr(self, is_leaf_gs) -> list:
        row0_head_list = []
        if is_leaf_gs or (self.old_ae_name == '' and self.new_ae_name == ''):
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="ae" class="{DataStateEnum.DATA_STATE} ae" {DataStateEnum.DATA_STATE}="{DataStateEnum.NONE}">{self.old_ae_name}</td>')
        elif self.old_ae_name == self.new_ae_name:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="ae" class="{DataStateEnum.DATA_STATE} ae" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.old_ae_name}</td>')
        else:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="ae" class="{DataStateEnum.DATA_STATE} ae" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.old_ae_name}</td>')
        row0_head_list.append(self.cts(is_leaf_gs))
        if is_leaf_gs:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="speed" class="speed">{self.speed}</td>')
        elif self.speed == self.new_speed:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="speed" class="{DataStateEnum.DATA_STATE} speed" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.speed}</td>')
        else:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="speed" class="{DataStateEnum.DATA_STATE} speed" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.speed}</td>')
        row0_head = ''.join(row0_head_list)
        trs = []
        for index, link_id in enumerate(self.links):
            link = self.links[link_id]
            if index == 0:
                trs.append(row0_head + link.tr(is_leaf_gs))
            else:
                trs.append(link.tr(is_leaf_gs))
        return trs


@dataclass
class _GenericSystem():
    old_label: str  # the generic system label in the tor blueprint
    new_label: str  # the generic system label in the main blueprint (renamed)
    index: int = 0
    is_leaf_gs: bool = False
    group_links: Dict[str, _GroupLink] = None  # <evpn/member interface id from tor>: _GroupLink    
    # set by main_bp
    message: str = None  # creation message
    new_gs_id: str = None  # the generic system id on main blueprint

    logger: Any = logging.getLogger('_GenericSystem')

    @property
    def tbody_id(self):
        return f"gs-{self.new_label}"

    @property
    def rowspan(self):
        return sum([v.rowspan for k, v in self.group_links.items()])

    @property
    def port_channel_id_min(self) -> int:
        ae_names = [x.old_ae_name[2:] for k, x in self.group_links.items() if x.old_ae_name.startswith('ae')]
        if len(ae_names):
            return int(min(ae_names))
        return 0

    @property
    def port_channel_id_max(self) -> int:
        ae_names = [x.old_ae_name[2:] for k, x in self.group_links.items() if x.old_ae_name.startswith('ae')]
        if len(ae_names):
            return int(max(ae_names))
        return 0

    @property
    def is_ct_done(self) -> bool:
        if self.is_leaf_gs:
            return True
        ct_not_done_list = [ ae_id for ae_id, ae_data in self.group_links.items() if not ae_data.is_ct_done]
        # breakpoint()
        return len(ct_not_done_list) == 0

    def is_gs_done(self) -> bool:
        if self.is_leaf_gs:
            return True
        if not self.new_gs_id:
            # self.logger.warning(f"is_gs_done {self.new_label=} {self.new_gs_id=}")
            return False
        for _, ae in self.group_links.items():
            if not ae.is_ae_done():
                # self.logger.warning(f"is_gs_done {self.new_label=}")
                return True
        return True

    def reset_to_tor_data(self):
        self.new_gs_id = None
        for _, ae_link in self.group_links.items():
            ae_link.reset_to_tor_data()

    def add_tags(self):
        """
        Do tagging. Refresh if changed.
        """
        main_bp = global_store.bp['main_bp']
        changed =False
        for _, ae in self.group_links.items():
            if ae.add_tags():
                changed = True
        if changed:
            self.refresh()
        return

    async def sse_tbody(self):
        """
        render the tbody by SSE
        """
        message_attr = f' data-message="{self.message}" ' if self.message else ''
        row0_head_list = []
        row0_head_list.append(f'<td rowspan={self.rowspan}>{self.index}</td>')
        row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="label" class="system-label">{self.label}</td>')
        if self.is_leaf_gs:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.NONE}" {message_attr}>{self.new_label}</td>')
        elif self.is_gs_done():
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}" {message_attr}>{self.new_label}</td>')
        else:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}" {message_attr}>{self.new_label}</td>')
        row0_head = ''.join(row0_head_list)       

        tbody_lines = []
        for k, ae_link in self.group_links.items():
            for links in ae_link.tr(self.is_leaf_gs):
                if len(tbody_lines):
                    tbody_lines.append(f'<tr>{links}</tr>')
                else:                    
                    tbody_lines.append(f'<tr>{row0_head}{links}</tr>')
        await SseEvent(
            event=SseEventEnum.TBODY_GS,
            data=SseEventData(
                id=self.tbody_id,
                value=''.join(tbody_lines))).send()  

    def form_lag(self):
        """
        Build LAG on each LAG links
        """
        main_bp = global_store.bp['main_bp']
        # logging.warning(f"form_lag begin {self.new_label=}")
        lag_spec = {
            'links': {}
        }
        for _, ae_link in self.group_links.items():
            for link, link_spec in ae_link.build_lag_spec().items():
                lag_spec['links'][link] = link_spec
        # logging.warning(f"form_lag {self.new_label=} {lag_spec=}")
        if len(lag_spec['links']):
            lag_updated = main_bp.patch_leaf_server_link_labels(lag_spec)
            # self.logger.warning(f"form_lag {lag_updated=} for {self.new_label=}")
            self.refresh()


    def refresh(self, server_links = None):
        """
        Refresh generic systesms with the new data from main blueprint given by server_links
        """
        # get server_links from main_bp
        main_bp = global_store.bp['main_bp']
        if server_links is None:
            # TODO: check task instead of sleep
            # may be too early. wait for 3 x 10
            self.reset_to_tor_data()

            server_links = {}
            # it was that 18+ seconds delay. wait for 3 x 10 
            max_retry = 10
            # in case of immediately following generic system creation, may need to wait
            for i in range(max_retry):
                server_links = main_bp.get_server_interface_nodes(self.new_label)
                if len(server_links):
                    break
                self.logger.warning(f"refresh() waiting - {len(server_links)=} {i}/{max_retry} for {self.new_label}")
                time.sleep(3)

        # server_links = main_bp.get_server_interface_nodes(self.new_label)
        for server_link in server_links:
            new_server_id = server_link[CkEnum.GENERIC_SYSTEM]['id']
            new_link_id = server_link[CkEnum.LINK]['id']
            new_ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            new_speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            new_switch_intf_id = server_link[CkEnum.MEMBER_INTERFACE]['id']
            new_ae_id = server_link[CkEnum.EVPN_INTERFACE]['id'] if server_link[CkEnum.EVPN_INTERFACE] else None
            new_server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or ''
            new_server_intf_id = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['id']
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            self.new_gs_id = new_server_id
            for _, ae_data in self.group_links.items():
                for _, link_data in ae_data.links.items():
                    if link_data.switch == switch and link_data.switch_intf == switch_intf:
                        # found the matching link
                        if tag:
                            link_data.add_new_tag(tag)
                        link_data.new_link_id = new_link_id
                        ae_data.new_ae_name = new_ae_name
                        ae_data.new_speed = new_speed
                        ae_data.new_ae_id = new_ae_id
                        link_data.new_server_intf = new_server_intf
                        link_data.new_switch_intf_id = new_switch_intf_id
                        link_data.new_server_intf_id = new_server_intf_id

        # logging.warning(f"GS refresh end {self.new_label=} {self=}")

        return

    def create_generic_system(self):
        """
        Create its generic system and refresh data. Called by migration.
        """
        main_bp = global_store.bp['main_bp']
        access_switches = global_store.access_switches.access_switches
        server_links = main_bp.get_server_interface_nodes(self.new_label)

        # generic system present
        if len(server_links):
            self.refresh()
            return

        # if len([x.id for x in access_switches.values()]) == 2:
        #     logging.warning(f"create_generic_system() May not proceed: {self.new_label=} {access_switches=}")
        #     return

        # geneirc system absent. creating
        generic_system_spec = {
            'links': [],
            'new_systems': [],
        }
    
        for _, ae_link in self.group_links.items():
            for _, member_link in ae_link.links.items():
                switch_label = member_link.switch
                switch_intf = member_link.switch_intf
                trasnsformation_id = main_bp.get_transformation_id(switch_label, switch_intf , ae_link.speed)
                # logging.warning(f"create_generic_system() {trasnsformation_id=}")
                switch_intf_id = access_switches[switch_label].id
                if not switch_intf_id:
                    logging.warning(f"create_generic_system() ERROR: {switch_label=} {switch_intf=} {switch_intf_id=}")
                    return
                generic_system_spec['links'].append({
                    'lag_mode': None,
                    'system': {
                        'system_id': None,
                        # 'if_name': member_link.server_intf,  ### MUST NOT HAVE THIS. THIS WILL FAIL
                    },
                    'switch': {
                        'system_id': switch_intf_id,
                        'transformation_id': trasnsformation_id,
                        'if_name': switch_intf,
                    }                
                })
        new_system = {
            'system_type': 'server',
            'label': self.new_label,
            # 'hostname': None, # hostname should not have '_' in it
            'port_channel_id_min': self.port_channel_id_min,
            'port_channel_id_max': self.port_channel_id_max,
            'logical_device': {
                'display_name': f"auto-{ae_link.speed}x{self.rowspan}",
                'id': f"auto-{ae_link.speed}x{self.rowspan}",
                'panels': [
                    {
                        'panel_layout': {
                            'row_count': 1,
                            'column_count': self.rowspan,
                        },
                        'port_indexing': {
                            'order': 'T-B, L-R',
                            'start_index': 1,
                            'schema': 'absolute'
                        },
                        'port_groups': [
                            {
                                'count': self.rowspan,
                                'speed': {
                                    'unit': ae_link.speed[-1:],
                                    'value': int(ae_link.speed[:-1])
                                },
                                'roles': [
                                    'leaf',
                                    'access'
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        # breakpoint()
        generic_system_spec['new_systems'].append(new_system)
        # TODO: catch error message
        # it returns the link id(s)
        generic_system_created = main_bp.add_generic_system(generic_system_spec)
        self.message = generic_system_created
        self.logger.warning(f"migrate() {generic_system_created=}")

        self.refresh()
        return


    def patch_interface_names(self):
        main_bp = global_store.bp['main_bp']
        link_name_spec = {
            'links': []
        }        
        for ae_link in self.group_links.values():
            for link in ae_link.links.values():
                new_item = link.interface_name_spec()
                if new_item:
                    link_name_spec['links'].append(new_item)
        if len(link_name_spec['links']):
            cable_map_patched = main_bp.patch_cable_map(link_name_spec)
            self.logger.warning(f"patch_interface_names {cable_map_patched=}")
            # TODO: wait for the finish the task
            self.refresh()
        return


    async def migrate(self) -> bool:
        """
        Migrate the generic system and its links
        Return True if changed
        """
        main_bp = global_store.bp['main_bp']
        # skip if this is leaf_gs
        if self.is_leaf_gs:
            return False

        self.create_generic_system()

        self.form_lag()

        self.patch_interface_names()

        self.add_tags()

        await self.sse_tbody()

        return True



# @dataclass
# class LeafGS():
#     label: str = None
#     a_48: str = None
#     a_49: str = None
#     b_48: str = None
#     b_49: str = None

class GenericSystemWorker():
    # generic_systems: Dict[str, _GenericSystem] = None  # init by sync_tor_generic_systems. <tbody-id>: { GenericSystem }
    # leaf_gs: LeafGS = None  # set from sync_tor_generic_systems 
    # main_servers = {}
    # tor_ae1 = None
    # tor_gs = None  # {'label': <>, 'id': None, 'ae_id': None},  # id and ae_id of main_bp
    logger: Any = logging.getLogger('GenericSystemWorker')
    # given by AccessSwitch
    # access_switches: Any  # moved to global_store. coming from access switches. <label>: _AccessSwitch
    # main_bp: Any
    # tor_bp: Any
    # tor_gs_label: str

    @property
    def access_switch_pair(cls):
        global global_store
        return global_store.access_switch_pair


    @property
    async def is_ct_done(self) -> bool:
        ct_not_done_list = [ tbody_id for tbody_id, gs in self.generic_systems.items() if not gs.is_ct_done]
        await global_store.migration_status.set_ct_done(len(ct_not_done_list) == 0)
        return len(ct_not_done_list) == 0


    @classmethod
    def guess_tor_gs_label(cls, tor_switch_label):
        name_prefix = 'atl1tor-'
        if tor_switch_label.startswith(name_prefix):
            if tor_switch_label.endswith(('a', 'b')):
                return tor_switch_label[len(name_prefix):-1]
            elif tor_switch_label.endswith(('c', 'c')):
                return f"{tor_switch_label[len(name_prefix):-1]}cd"
        cls.logger.error(f"guess_tor_gs_label() irregular label: {tor_switch_label=}")
        return None

        return global_store.tor_gs_label

    @classmethod
    async def sync_tor_generic_systems(cls, global_store):
        """
        Pull the generic systems data from tor blueprint and rebuild generic_systems and leaf_gs
        the 1st call
        does not render the web page (TODO: maybe render the page ?)

        From the tor_bp links, build generic_systems, leaf_switches, tor_label, and leaf_gs
        Sync main_bp leaf links:
            1. if tor_gs present, delete it.
            2. if access switches absent, create one.
            3. fix the generic systems under the access switches
            
        """
        # global global_store

        cls.logger.warning(f"sync_tor_generic_systems() begin {global_store=}")

        if global_store.generic_systems is not None or global_store.access_switches is not None:
            cls.logger.error(f"sync_tor_generic_systems() called twice - generic_systems or access_switches not None {global_store.generic_systems=} {global_store.access_switches=}")
            return
        
        generic_systems = global_store.generic_systems = {}
        access_switches = global_store.access_switches = {}
        leaf_gs_label = None  # this will not be used elsewhere
        tor_gs = None  # create at the first data and update global_store.tor_gs
        tor_bp = global_store.bp['tor_bp']

        # build generic_systems data from tor_bp. set the variables 'old-'
        for server_link in tor_bp.get_switch_interface_nodes():
            switch_label = server_link[CkEnum.MEMBER_SWITCH]['label']  # tor switch which will be access switch
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            switch_id = server_link[CkEnum.MEMBER_SWITCH]['id']
            if tor_gs is None:
                guessed_label = cls.guess_tor_gs_label(switch_label)
                cls.logger.warning(f"sync_tor_generic_systems() {guessed_label=}")
                tor_gs = global_store.tor_gs = TorGS(label=guessed_label, link_ids=[])
                # tor_gs.label = cls.guess_tor_gs_label(switch_label)
                if tor_gs.label is None:
                    cls.logger.error(f"sync_tor_generic_systems() irregular label: {switch_label=}")
                    return
                tor_gs.prefix = tor_gs.label[len('atl1tor-'):]
            access_switches.setdefault(switch_label, AccessSwitch(label=switch_label, tor_id=switch_id))
            old_server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            new_label = make_new_label(global_store, old_server_label)
            tbody_id = f"gs-{new_label}"
            # link_id = server_link[CkEnum.LINK]['id']
            old_switch_intf_id = server_link[CkEnum.MEMBER_INTERFACE]['id']
            old_ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            old_ae_id = server_link[CkEnum.EVPN_INTERFACE]['id'] if server_link[CkEnum.EVPN_INTERFACE] else old_switch_intf_id
            speed = server_link[CkEnum.LINK]['speed']
            old_server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or ''
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            server_data = generic_systems.setdefault(tbody_id, _GenericSystem(old_label=old_server_label, new_label=new_label, group_links={}))
            # check if leaf_gs
            if switch_intf in ['et-0/0/48', 'et-0/0/49']:
                server_data.is_leaf_gs = True
                # server_data.new_label = server_label  # do not rename leaf_gs
                leaf_gs_label = old_server_label
                # if switch_label.endswith(('a', 'c')):  # left tor
                #     if switch_intf == 'et-0/0/48':
                #         leaf_gs.a_48 = 'et-' + old_server_intf.split('-')[1]
                #     else:
                #         leaf_gs.a_49 = 'et-' + old_server_intf.split('-')[1]
                # else:
                #     if switch_intf == 'et-0/0/48':
                #         leaf_gs.b_48 = 'et-' + old_server_intf.split('-')[1]
                #     else:
                #         leaf_gs.b_49 = 'et-' + old_server_intf.split('-')[1]

            # breakpoint()
            ae_data = server_data.group_links.setdefault(old_ae_id, _GroupLink(old_ae_name=old_ae_name, old_ae_id=old_ae_id, speed=speed, links={}))
            link_data = ae_data.links.setdefault(old_switch_intf_id, _Memberlink(switch=switch_label, switch_intf=switch_intf, old_server_intf=old_server_intf, old_tags=[]))
            if tag:
                link_data.add_old_tag(tag)
                # self.logger.warning(f"sync_tor_generic_systems {tag=} {server_label=} {tbody_id=}")            
        # set index number for each generic system
        for index, v in enumerate(generic_systems.values()):
            v.index = index + 1

        # render leaf_gs
        await SseEvent(data=SseEventData(id='leaf-gs-label', value=leaf_gs_label)).send()
        # await SseEvent(data=SseEventData(id='leafgs-48a', value=leaf_gs.a_48)).send()
        # await SseEvent(data=SseEventData(id='leafgs-48b', value=leaf_gs.b_48)).send()
        # await SseEvent(data=SseEventData(id='leafgs-49a', value=leaf_gs.a_49)).send()
        # await SseEvent(data=SseEventData(id='leafgs-49b', value=leaf_gs.b_49)).send()
        # await SseEvent(data=SseEventData(id='leaf-gs-box').done()).send()

        await SseEvent(data=SseEventData(id='tor1-label', value=global_store.access_switch_pair[0])).send()
        await SseEvent(data=SseEventData(id='tor2-label', value=global_store.access_switch_pair[1])).send()
        await SseEvent(data=SseEventData(id='tor1-box').done()).send()
        await SseEvent(data=SseEventData(id='tor2-box').done()).send()

        cls.logger.warning(f"sync_tor_generic_systems end {len(generic_systems)=}")
    
        return


    @classmethod
    async def init_leaf_switches(cls, global_store):
        """
        Init leaf switches data from the access switches labels
        """
        tor_gs = global_store.tor_gs
        leaf_switches = global_store.leaf_switches = {}        
        access_switches = global_store.access_switches
        leaf_intf_temp = set()  # to captuer the leaf interface names
        lldp = global_store.lldp
        ab = ['a', 'b']
        for tor_index, tor_switch_label in enumerate(sorted(access_switches)):
            for leaf_label, leaf_data in lldp.items():
                for link in leaf_data:
                    # - neighbor_interface_name: et-0/0/48
                    #     neighbor_system_id: atl1tor-r5r15a  
                    #     interface_name: et-0/0/16  
                    if link['neighbor_system_id'] == tor_switch_label:
                        leaf_link_key = f"{ab[tor_index]}{link['neighbor_interface_name'][-2:]}"
                        leaf_intf = link['interface_name']
                        leaf_intf_temp.add(leaf_intf)  # just to add key
                        leaf_sw_data = leaf_switches.setdefault(leaf_label, LeafSwitch(label=leaf_label, id=None, links={}))
                        leaf_sw_data.links[leaf_link_key] = LeafLink(leaf_intf=leaf_intf, tor_name=tor_switch_label)
                        # this_leaf = leaf_switches.setdefault(leaf_label, LeafSwitch(label=leaf_label, id=None, links=[]))
                        # this_leaf.links.append(LeafLink(leaf_intf=link['interface_name'], other_intf=link['neighbor_interface_name']))
                        await SseEvent(data=SseEventData(id=f"leafgs-{leaf_link_key}", value=leaf_intf)).send()
                        await SseEvent(data=SseEventData(id=f"leafsw-{leaf_link_key}", value=leaf_intf)).send()

        await SseEvent(data=SseEventData(id='leaf1-label', value=sorted(leaf_switches)[0])).send()
        await SseEvent(data=SseEventData(id='leaf2-label', value=sorted(leaf_switches)[1])).send()
        # for leaf_label in sorted(leaf_switches):

        # await SseEvent(data=SseEventData(id='leafgs-48a', value=leaf_gs.a_48)).send()
        # await SseEvent(data=SseEventData(id='leafgs-48b', value=leaf_gs.b_48)).send()
        # await SseEvent(data=SseEventData(id='leafgs-49a', value=leaf_gs.a_49)).send()
        # await SseEvent(data=SseEventData(id='leafgs-49b', value=leaf_gs.b_49)).send()
        await SseEvent(data=SseEventData(id='leaf-gs-box').done()).send()

        #
        # sync leaf switches links
        #
        main_bp = global_store.bp['main_bp']
        leaf_link_query = f"""
            node('system', label=is_in({sorted(leaf_switches)}), name='leaf')
                .out().node('interface', if_name=is_in({sorted(leaf_intf_temp)}), name='leaf_intf')
                .out().node('link').in_().node('interface', name='tor_intf')
                .in_().node('system', role=not_in(['leaf']), name='tor')
        """
        leaf_link_nodes = main_bp.query(leaf_link_query)
        # cls.logger.warning(f"init_leaf_switches() {leaf_link_nodes=}")
        for nodes in leaf_link_nodes:
            leaf_data = leaf_switches[nodes['leaf']['label']]
            leaf_data.id = nodes['leaf']['id']
            leaf_link_data = [x for x in leaf_data.links.values() if x.leaf_intf == nodes['leaf_intf']['if_name']][0]
            leaf_link_data.id = nodes['leaf_intf']['id']
            if nodes['tor']['role'] == 'access':
                # the access switches present
                access_switches[nodes['tor']['label']].main_id = nodes['tor']['id']
            elif nodes['tor']['role'] == 'generic':
                # the generic systems present
                tor_gs.label=nodes['tor']['label']
                tor_gs.id=nodes['tor']['id']
                # TODO: add links, ae_id, ...
        if tor_gs.tor_id is None:
            await SseEvent(data=SseEventData(id='access-gs-box').hidden()).send()
            await SseEvent(data=SseEventData(id='access-gs-label').hidden()).send()
        if len([x.id for x in leaf_switches.values()]) == 2:
            await SseEvent(data=SseEventData(id='leaf1-box').done()).send()
            await SseEvent(data=SseEventData(id='leaf2-box').done()).send()
        if len([x.main_id for x in access_switches.values()]) == 2:
            await SseEvent(data=SseEventData(id='access1-box').done().visible()).send()
            await SseEvent(data=SseEventData(id='access2-box').done().visible()).send()
            await SseEvent(data=SseEventData(id='access1-label').visible()).send()
            await SseEvent(data=SseEventData(id='access2-label').visible()).send()

        cls.logger.warning(f"init_leaf_switches end {leaf_switches=}")
        return


    def sync_main_links(self, global_store):
        """
        Pull the server information of the created access switches in main_bp
          and update the generic_systems data (refresh)
        """
        main_bp = global_store.bp['main_bp']
        server_links_dict = {}
        # update generic_systems from main_bp
        server_links = main_bp.get_switch_interface_nodes(global_store.access_switches.access_switch_pair)
        self.logger.warning(f"sync_main_links {len(server_links)=}")
        for server_link in server_links:
            switch_label = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_id = server_link[CkEnum.MEMBER_SWITCH]['id']
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            tbody_id = f"gs-{server_label}"
            server_links_dict.setdefault(tbody_id, []).append(server_link)
            global_store.access_switches.access_switches[switch_label].id = switch_id

        for tbody_id, links in server_links_dict.items():
            # breakpoint()
            self.generic_systems[tbody_id].refresh(server_links=links)
        return


    async def refresh_tor_generic_systems(self) -> None:
        """
        Called by main.py from SyncState
        The generic systems are synced from tor_bp and main_bp by sysnc_access_groups
        Build rendering data and send it to the web page
        """
        self.logger.warning(f"refresh_tor_generic_systems begin")
        gs_count = len(self.generic_systems)
        is_all_done = True
        # render each generic system
        for tbody_id, server_data in self.generic_systems.items():
            await server_data.sse_tbody()
            if not server_data.is_gs_done():
                is_all_done = False
        # update caption
        caption = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
        await SseEvent(data=SseEventData(
                id=SseEventEnum.CAPTION_GS,
                value=caption)).send()
        if is_all_done:
            await global_store.migration_status.set_gs_done(True)

        self.logger.warning(f"refresh_tor_generic_systems end")
        return

    # async def migrate_generic_system(self, tbody_id) -> dict:
    #     """
    #     """
    #     self.logger.warning(f"migrate_generic_system {tbody_id=}")
    #     if tbody_id not in self.generic_systems:
    #         return {'error': f"tbody_id {tbody_id} not found", 'is_migrated': False}
    #     the_gs = self.generic_systems[tbody_id]
    #     is_migrated = await the_gs.migrate(self.main_bp)
    #     return is_migrated

    async def migrate_generic_systems(self) -> None:
        """
        """
        self.logger.warning(f"migrate_generic_systems begin")
        is_all_done = True
        for tbody_id, server_data in self.generic_systems.items():
            await server_data.migrate()
            if not server_data.is_gs_done():
                is_all_done = False
        if is_all_done:
            await global_store.migration_status.set_gs_done(True)
        
        return



def make_new_label(global_store, old_label) -> str:
    """
    Return new label of the generic system from the old label and tor name
    This is to avoid duplicate names which was created by old tor_bp
    """
    # global global_store

    old_patterns = ['_atl_rack_1_000_', '_atl_rack_1_001_', '_atl_rack_5120_001_']
    tor_gs_prefix = global_store.tor_gs.prefix
    for pattern in old_patterns:
        if old_label.startswith(pattern):
            # replace the string with the prefix
            return f"{tor_gs_prefix}-{old_label[len(pattern):]}"
    # it doesn't starts with the patterns. See if it is too long to prefix
    max_len = 32
    if ( len(old_label) + len(tor_gs_prefix) + 1 ) > max_len:
        # TODO: too long. potential of conflict
        return old_label
    # good to just prefix
    return f"{tor_gs_prefix}-{old_label}"
