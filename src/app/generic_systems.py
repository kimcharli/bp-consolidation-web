from pydantic import BaseModel
from typing import Optional, List, Dict, Any, ClassVar
import logging
from enum import Enum, StrEnum, auto
import time
import html

from ck_apstra_api.apstra_blueprint import CkEnum
# TODO: consolidate
class DataStateEnum(StrEnum):
    LOADED = 'done'
    INIT = 'init'
    DONE = 'done'
    ERROR = 'error'
    DATA_STATE = 'data-state'


class _Memberlink(BaseModel):
    tags: List[str] = []
    switch: str
    switch_intf: str
    server_intf: str = ''  # DO NOT USE None
    # from main_bp
    new_tags: List[str] = []
    new_server_intf: str = ''  # DO NOT USE NONE
    new_id: Optional[str] = None   # main_id
    switch_intf_id: str = ''
    server_intf_id: str = ''

    def reset_to_tor_data(self):
        self.new_tags = []
        self.new_server_intf = ''
        self.new_id = None

    def interface_name_spec(self, access_switches) -> dict:
        """
        Fix interface name. 
        """
        if self.new_server_intf != self.server_intf:
            return {
                'id': self.new_id,
                'endpoints': [
                    {
                        'interface': {
                            'id': self.server_intf_id,
                            'if_name': self.server_intf
                        }
                    },
                    {
                        'interface': {
                            'id': self.switch_intf_id
                        }
                    }
                ]
            }
        return None

    @property
    def tr(self) -> str:
        trs = []
        tags_buttons_list = []
        for i in self.tags:
            if i in self.new_tags:
                tags_buttons_list.append(f'<button type="button" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{i}</button>')
            else:
                tags_buttons_list.append(f'<button type="button" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{i}</button>')
        for i in self.new_tags:
            if i not in self.tags:
                tags_buttons_list.append(f'<button type="button" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.ERROR}">{i}</button>')
        tags_buttons = ''.join(tags_buttons_list)
        trs.append(f'<td data-cell="tags">{tags_buttons}</td>')
        if self.new_id and self.server_intf == self.new_server_intf:
            trs.append(f'<td data-cell="server_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.server_intf}</td>')
        else:
            trs.append(f'<td data-cell="server_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.server_intf}</td>')
        if self.new_id:
            trs.append(f'<td data-cell="switch" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.switch}</td>')
            trs.append(f'<td data-cell="switch_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.switch_intf}</td>')
        else:
            trs.append(f'<td data-cell="switch" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.switch}</td>')
            trs.append(f'<td data-cell="switch_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.switch_intf}</td>')
        return ''.join(trs)

    def add_tag(self, tag):
        if tag  not in self.tags:
            self.tags.append(tag)

    def add_new_tag(self, tag):
        if tag not in self.new_tags:
            self.new_tags.append(tag)

    def add_tags(self, main_bp) -> bool:
        """
        Do tagging. Retrun True if changed
        """
        if sorted(self.tags) != sorted(self.new_tags):
            main_bp.post_tagging( 
                [self.new_id], 
                tags_to_add = [x for x in self.tags if x not in self.new_tags],
                tags_to_remove = [x for x in self.new_tags if x not in self.tags]
                )
            return True
        return False


class _GroupLink(BaseModel):
    ae_name: str = '' # the ae in the tor blueprint
    speed: str
    cts: Optional[List[int]] = []
    tagged_vlans: Optional[List[int]] = []
    untagged_vlan: Optional[int] = None
    links: Dict[str, _Memberlink] = {}  # <link id from tor>: _Memberlink
    # from main_bp
    new_ae_name: str = ''  # the ae in the main blueprint
    new_id: str = None
    new_cts: Optional[List[int]] = []  # the connectivity templates in main blueprint  
    new_speed: str = None

    @property
    def rowspan(self):
        return len(self.links)

    def reset_to_tor_data(self):
        self.new_ae_name = None
        self.new_id = None
        self.new_speed = None
        self.new_cts = []
        for _, link in self.links.items():
            link.reset_to_tor_data()

    def build_lag_spec(self):
        """
        Build LAG spec for each link if new_id is absent
        """
        lag_spec = {}
        if self.ae_name != '' and not self.new_id:
            lag_spec = {x.new_id: {
                'group_label': self.ae_name,
                'lag_mode': 'lacp_active'
            } for k, x in self.links.items()}
            self.new_ae_name = self.ae_name
        return lag_spec        

    def add_tags(self, main_bp):
        """
        Do tagging. Retrun True if changed
        """
        changed = False
        for _, link in self.links.items():
            if link.add_tags(main_bp):
                changed = True
        return changed


    @property
    def tr(self) -> list:
        row0_head_list = []
        if self.ae_name == self.new_ae_name:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="ae" class="{DataStateEnum.DATA_STATE} ae" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.ae_name}</td>')
        else:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="ae" class="{DataStateEnum.DATA_STATE} ae" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.ae_name}</td>')
        row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="cts" class="{DataStateEnum.DATA_STATE} cts" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.cts}</td>')
        if self.speed == self.new_speed:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="speed" class="{DataStateEnum.DATA_STATE} speed" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.speed}</td>')
        else:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="speed" class="{DataStateEnum.DATA_STATE} speed" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.speed}</td>')
        row0_head = ''.join(row0_head_list)
        trs = []
        for index, link_id in enumerate(self.links):
            link = self.links[link_id]
            if index == 0:
                trs.append(row0_head + link.tr)
            else:
                trs.append(link.tr)
        return trs


class _GenericSystem(BaseModel):
    index: int = 0
    label: str  # the label in the tor blueprint
    new_label: str = None  # the label in the main blueprint (renamed)
    is_leaf_gs: bool = False
    group_links: Dict[str, _GroupLink] = {}  # <group link id or link id of tor>: _GroupLink    
    # set by main_bp
    message: str = None  # creation message
    new_id: str = None  # the generic system id on main blueprint

    logger: Any = logging.getLogger('_GenericSystem')

    @property
    def tbody_id(self):
        return f"gs-{self.new_label}"

    @property
    def rowspan(self):
        return sum([v.rowspan for k, v in self.group_links.items()])

    @property
    def port_channel_id_min(self) -> int:
        ae_names = [x.ae_name[2:] for k, x in self.group_links.items() if x.ae_name.startswith('ae')]
        if len(ae_names):
            return int(min(ae_names))
        return 0

    @property
    def port_channel_id_max(self) -> int:
        ae_names = [x.ae_name[2:] for k, x in self.group_links.items() if x.ae_name.startswith('ae')]
        if len(ae_names):
            return int(max(ae_names))
        return 0

    def reset_to_tor_data(self):
        self.new_id = None
        for _, ae_link in self.group_links.items():
            ae_link.reset_to_tor_data()

    def add_tags(self, main_bp):
        """
        Do tagging. Refresh if changed.
        """
        changed =False
        for _, ae in self.group_links.items():
            if ae.add_tags(main_bp):
                changed = True
        if changed:
            self.refresh(main_bp)
        return

    def get_tbody(self) -> str:
        """
        Return the tbody innerHTML
        """
        message_attr = f' data-message="{self.message}" ' if self.message else ''
        row0_head_list = []
        row0_head_list.append(f'<td rowspan={self.rowspan}>{self.index}</td>')
        row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="label" class="system-label">{self.label}</td>')
        if self.new_id:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}" {message_attr}>{self.new_label}</td>')
        else:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}" {message_attr}>{self.new_label}</td>')
        row0_head = ''.join(row0_head_list)       

        tbody_lines = []
        for k, ae_link in self.group_links.items():
            for links in ae_link.tr:
                if len(tbody_lines):
                    tbody_lines.append(f'<tr>{links}</tr>')
                else:                    
                    tbody_lines.append(f'<tr>{row0_head}{links}</tr>')
        return ''.join(tbody_lines)

    def form_lag(self, main_bp):
        """
        Build LAG on each LAG links
        """
        lag_spec = {
            'links': {}
        }
        for _, ae_link in self.group_links.items():
            for link, link_spec in ae_link.build_lag_spec().items():
                lag_spec['links'][link] = link_spec
        if len(lag_spec['links']):
            lag_updated = main_bp.patch_leaf_server_link_labels(lag_spec)
            self.logger.warning(f"{lag_updated=} for {self.new_label=}")
            self.refresh(main_bp)

    def refresh(self, main_bp, server_links = None):
        """
        Refresh new data from main blueprint
        """
        # get server_links from main_bp
        if server_links is None:
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
            new_ae_id = server_link[CkEnum.EVPN_INTERFACE]['id'] if server_link[CkEnum.EVPN_INTERFACE] else None
            new_speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            switch_intf_id = server_link[CkEnum.MEMBER_INTERFACE]['id']
            new_server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or ''
            server_intf_id = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['id']
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            self.new_id = new_server_id
            for _, ae_data in self.group_links.items():
                for _, link_data in ae_data.links.items():
                    if link_data.switch == switch and link_data.switch_intf == switch_intf:
                        # found the matching link
                        if tag:
                            link_data.add_new_tag(tag)
                        link_data.new_id = new_link_id
                        ae_data.new_ae_name = new_ae_name
                        ae_data.new_speed = new_speed
                        ae_data.new_id = new_ae_id
                        link_data.new_server_intf = new_server_intf
                        link_data.switch_intf_id = switch_intf_id
                        link_data.server_intf_id = server_intf_id


    def create_generic_system(self, main_bp, access_switches):
        """
        Create its generic system and refresh data. Called by migration.
        """
        server_links = main_bp.get_server_interface_nodes(self.new_label)

        # generic system present
        if len(server_links):
            self.refresh(main_bp)
            return

        # geneirc system absent. creating
        generic_system_spec = {
            'links': [],
            'new_systems': [],
        }
    
        for _, ae_link in self.group_links.items():
            for _, member_link in ae_link.links.items():
                switch_label = member_link.switch
                switch_intf = member_link.switch_intf
                generic_system_spec['links'].append({
                    'lag_mode': None,
                    'system': {
                        'system_id': None,
                        # 'if_name': member_link.server_intf,  ### MUST NOT HAVE THIS. THIS WILL FAIL
                    },
                    'switch': {
                        'system_id': access_switches[switch_label].id,
                        'transformation_id': main_bp.get_transformation_id(switch_label, switch_intf , ae_link.speed),
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
        generic_system_spec['new_systems'].append(new_system)
        # TODO: catch error message
        generic_system_created = main_bp.add_generic_system(generic_system_spec)
        self.message = generic_system_created
        self.logger.warning(f"migrate() {generic_system_created=}")

        self.refresh(main_bp)
        return


    def update_interface_names(self, main_bp, access_switches):
        link_name_spec = {
            'links': []
        }
        for _, ae_link in self.group_links.items():
            for _, link in ae_link.links.items():
                new_item = link.interface_name_spec(access_switches)
                if new_item:
                    link_name_spec['links'].append(new_item)
        if len(link_name_spec['links']):
            cable_map_patched = main_bp.patch_cable_map(link_name_spec)
            self.logger.warning(f"update_interface_names {cable_map_patched=}")
            # TODO: wait for the finish the task
            self.refresh(main_bp)
        return


    def migrate(self, main_bp, access_switches) -> dict:
        """
        Return:
            new_id: new_id
            value: get_tbody()
            caption: caption
        """
        # skip if this is leaf_gs
        if self.is_leaf_gs:
            return {
                'value': self.get_tbody(),
            }
        self.logger.warning(f"_GenericSystem::migrate({main_bp=},{access_switches=}) {self=}")
        self.create_generic_system(main_bp, access_switches)
        self.form_lag(main_bp)
        self.update_interface_names(main_bp, access_switches)
        self.add_tags(main_bp)

        return {
            'new_id': self.new_id,  # TODO: no need?
            'value': self.get_tbody(),
            # 'caption': None # TODO: later
        }

class _GenericSystemResponseItem(BaseModel):
    id: str
    newId: str
    value: str

class _GenericSystemResponse(BaseModel):
    done: Optional[bool] = False
    values: Optional[List[_GenericSystemResponseItem]] = []
    caption: Optional[str] = None

class _AccessSwitch(BaseModel):
    label: str
    id: str

class LeafGS(BaseModel):
    label: str = None
    a_48: str = None
    a_49: str = None
    b_48: str = None
    b_49: str = None

class GenericSystems(BaseModel):
    generic_systems: Dict[str, _GenericSystem] = {}  # <tbody-id>: { GenericSystem }
    # main_servers = {}
    # tor_ae1 = None
    # leaf_gs: LeafGS = LeafGS()  # {'label': None, 'intfs': ['']*4}
    # tor_gs = None  # {'label': <>, 'id': None, 'ae_id': None},  # id and ae_id of main_bp
    access_switches: Any = {}  # <label>: _AccessSwitch
    logger: Any = logging.getLogger('GenericSystems')
    # given by AccessSwitch
    main_bp: Any
    tor_bp: Any
    tor_gs_label: str

    @property
    def access_switch_pair(self):
        return sorted(self.access_switches)

    @property
    def leaf_gs(self) -> LeafGS:
        #
        # get leaf_gs (the generic system in TOR bp for the leaf)
        #   to be used by AccessSwitch
        #
        the_data = LeafGS()
        for tbody_id, server_data in self.generic_systems.items():
            server_label = server_data.label
            for ae_link_id, group_link in server_data.group_links.items():
                if group_link.ae_name:
                    for member_id, member_link in group_link.links.items():
                        # breakpoint()
                        if member_link.switch_intf in ['et-0/0/48', 'et-0/0/49']:
                            the_data.label = server_label                            
                            if member_link.switch.endswith(('a', 'c')):  # left tor
                                if member_link.switch_intf == 'et-0/0/48':
                                    the_data.a_48 = 'et-' + member_link.server_intf.split('-')[1]
                                else:
                                    the_data.a_49 = 'et-' + member_link.server_intf.split('-')[1]
                            else:
                                if member_link.switch_intf == 'et-0/0/48':
                                    the_data.b_48 = 'et-' + member_link.server_intf.split('-')[1]
                                else:
                                    the_data.b_49 = 'et-' + member_link.server_intf.split('-')[1]
        return the_data

    def update_generic_systems_table(self) -> dict:
        """
        Called by main.py from SyncState
        Build generic_systems from tor_blueprint and return the data 
        """
        content = _GenericSystemResponse()
        gs_count = len(self.generic_systems)
        for tbody_id, server_data in self.generic_systems.items():
            content.values.append(_GenericSystemResponseItem(
                id=tbody_id,
                newId='',
                value=server_data.get_tbody()
                ))
        content.caption = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
        return content

    def migrate_generic_system(self, tbody_id) -> dict:
        """
        """
        self.logger.warning(f"migrate_generic_system {tbody_id=}")
        data = self.generic_systems[tbody_id].migrate(self.main_bp, self.access_switches)
        return data

    def pull_generic_systems(self):
        """
        the 1st call
        Pull the generic systems data and rebuild generic_systems
        """
        generic_systems = {}

        # build generic_systems data from tor_bp
        for server_link in self.tor_bp.get_switch_interface_nodes(self.access_switch_pair):
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            new_label = self.set_new_generic_system_label(server_label)
            tbody_id = f"gs-{new_label}"
            link_id = server_link[CkEnum.LINK]['id']
            ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            ae_id = server_link[CkEnum.EVPN_INTERFACE]['id'] if server_link[CkEnum.EVPN_INTERFACE] else link_id
            speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or ''
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            server_data = generic_systems.setdefault(tbody_id, _GenericSystem(label=server_label, new_label=self.set_new_generic_system_label(server_label)))
            if switch_intf == 'et-0/0/48':
                server_data.is_leaf_gs = True
            ae_data = server_data.group_links.setdefault(ae_id, _GroupLink(ae_name=ae_name, speed=speed))
            link_data = ae_data.links.setdefault(link_id, _Memberlink(switch=switch, switch_intf=switch_intf, server_intf=server_intf))
            if tag:
                link_data.add_tag(tag)
        for index, (k, v) in enumerate(generic_systems.items()):
            v.index = index + 1
        self.generic_systems = generic_systems

        server_links_dict = {}
        # update generic_systems from main_bp
        for server_link in self.main_bp.get_switch_interface_nodes(self.access_switch_pair):
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            tbody_id = f"gs-{server_label}"
            server_links_dict.setdefault(tbody_id, []).append(server_link)            
        for tbody_id, links in server_links_dict.items():
            self.generic_systems[tbody_id].refresh(self.main_bp, links)

        return


    def set_new_generic_system_label(self, old_label):
        """
        Return new label of the generic system from the old label and tor name
        This is to avoid duplicate names which was created by old tor_bp
        """
        old_patterns = ['_atl_rack_1_000_', '_atl_rack_1_001_', '_atl_rack_5120_001_']
        prefix = self.tor_gs_label[len('atl1tor-'):]
        for pattern in old_patterns:
            if old_label.startswith(pattern):
                # replace the string with the prefix
                return f"{prefix}-{old_label[len(pattern):]}"
        # it doesn't starts with the patterns. See if it is too long to prefix
        max_len = 32
        if ( len(old_label) + len(prefix) + 1 ) > max_len:
            # TODO: too long. potential of conflict
            return old_label
        # good to just prefix
        return f"{prefix}-{old_label}"
