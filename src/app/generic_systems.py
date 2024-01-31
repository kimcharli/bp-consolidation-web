from pydantic import BaseModel
from typing import Optional, List, Dict, Any, ClassVar
import logging
from enum import Enum, StrEnum, auto
import time

from ck_apstra_api.apstra_blueprint import CkEnum
from .ck_global import DataStateEnum, sse_queue, SseEvent, SseEventEnum, SseEventData
from .vlan_cts import CtData
# TODO: consolidate
# TODO: catch AE creation delay
# TODO: generic systems done update


class _Memberlink(BaseModel):
    old_tags: List[str] = []
    switch: str
    switch_intf: str
    old_server_intf: str = ''  # DO NOT USE None
    # from main_bp
    new_tags: List[str] = []
    new_server_intf: str = ''  # DO NOT USE NONE
    new_link_id: Optional[str] = None   # main_id
    new_switch_intf_id: str = ''
    new_server_intf_id: str = ''

    def is_not_done(self) -> bool:
        if not self.new_switch_intf_id or self.old_tags != self.new_tags or self.old_server_intf != self.new_server_intf:
            # logging.warning(f"_Memberlink is_not_done ##################### {self=}")
            return True
        return False
     
    def reset_to_tor_data(self):
        self.new_tags = []
        self.new_server_intf = ''
        self.new_link_id = None

    def interface_name_spec(self, access_switches) -> dict:
        """
        Fix interface name. 
        """
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

    def add_tags(self, main_bp) -> bool:
        """
        Do tagging. Retrun True if changed
        """        
        if sorted(self.old_tags) != sorted(self.new_tags):
            main_bp.post_tagging( 
                [self.new_link_id], 
                tags_to_add = [x for x in self.old_tags if x not in self.new_tags],
                tags_to_remove = [x for x in self.new_tags if x not in self.old_tags]
                )
            return True
        return False




class _GroupLink(BaseModel):
    old_ae_id: str  # to use for ct_id
    old_ae_name: str = '' # the ae in the tor blueprint
    speed: str
    # cts: List[CtData] = []
    old_tagged_vlans: Dict[int, CtData] = {}
    old_untagged_vlan: Dict[int, CtData] = {}  # one entry at most
    links: Dict[str, _Memberlink] = {}  # <member interface id from tor>: _Memberlink
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

    def is_not_done(self) -> bool:
        if self.speed != self.new_speed:
            # logging.warning(f"_GroupLink is_not_done ##################### {self.new_ae_id=} {self.speed=} {self.new_speed=}")
            return True
        if self.new_ae_name != self.old_ae_name:
            return True
        for _, link in self.links.items():
            if link.is_not_done():
                # logging.warning(f"_GroupLink is_not_done ##################### {link=}")
                return True
        return False

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

    def add_tags(self, main_bp):
        """
        Do tagging. Retrun True if changed
        """
        changed = False
        for _, link in self.links.items():
            if link.add_tags(main_bp):
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


class _GenericSystem(BaseModel):
    index: int = 0
    label: str  # the generic system label in the tor blueprint
    new_label: str  # the generic system label in the main blueprint (renamed)
    is_leaf_gs: bool = False
    group_links: Dict[str, _GroupLink] = {}  # <evpn/member interface id from tor>: _GroupLink    
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

    def is_not_done(self) -> bool:
        if self.is_leaf_gs:
            return False
        if not self.new_gs_id:
            # self.logger.warning(f"is_not_done {self.new_label=} {self.new_gs_id=}")
            return True
        for _, ae in self.group_links.items():
            if ae.is_not_done():
                # self.logger.warning(f"is_not_done {self.new_label=}")
                return True
        return False

    def reset_to_tor_data(self):
        self.new_gs_id = None
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
        elif self.is_not_done():
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}" {message_attr}>{self.new_label}</td>')
        else:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}" {message_attr}>{self.new_label}</td>')
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

    def form_lag(self, main_bp):
        """
        Build LAG on each LAG links
        """
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
            self.refresh(main_bp)


    def refresh(self, main_bp, server_links = None):
        """
        Refresh new data from main blueprint given by server_links
        """
        # get server_links from main_bp
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
                trasnsformation_id = main_bp.get_transformation_id(switch_label, switch_intf , ae_link.speed)
                logging.warning(f"create_generic_system() {trasnsformation_id=} {trasnsformation_id.content=}")
                generic_system_spec['links'].append({
                    'lag_mode': None,
                    'system': {
                        'system_id': None,
                        # 'if_name': member_link.server_intf,  ### MUST NOT HAVE THIS. THIS WILL FAIL
                    },
                    'switch': {
                        'system_id': access_switches[switch_label].id,
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
        generic_system_spec['new_systems'].append(new_system)
        # TODO: catch error message
        # it returns the link id(s)
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


    async def migrate(self, main_bp, access_switches):
        """
        Return:
            new_id: new_gs_id
            value: get_tbody()
            caption: caption
        """
        # skip if this is leaf_gs
        if self.is_leaf_gs:
            return
        
        self.create_generic_system(main_bp, access_switches)

        self.form_lag(main_bp)

        self.update_interface_names(main_bp, access_switches)

        self.add_tags(main_bp)

        await self.sse_tbody()

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
    generic_systems: Dict[str, _GenericSystem] = {}  # init by sys_tor_generic_systems. <tbody-id>: { GenericSystem }
    # main_servers = {}
    # tor_ae1 = None
    leaf_gs: LeafGS = LeafGS()  # set from sync_tor_generic_systems {'label': None, 'intfs': ['']*4}
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

    # @property
    # def leaf_gs(self) -> LeafGS:
    #     #
    #     # get leaf_gs (the generic system in TOR bp for the leaf)
    #     #   to be used by AccessSwitch
    #     #
    #     the_data = LeafGS()
    #     for tbody_id, server_data in self.generic_systems.items():
    #         server_label = server_data.label
    #         for ae_link_id, group_link in server_data.group_links.items():
    #             if group_link.old_ae_name:
    #                 for member_id, member_link in group_link.links.items():
    #                     if member_link.switch_intf in ['et-0/0/48', 'et-0/0/49']:
    #                         the_data.label = server_label                            
    #                         if member_link.switch.endswith(('a', 'c')):  # left tor
    #                             if member_link.switch_intf == 'et-0/0/48':
    #                                 the_data.a_48 = 'et-' + member_link.old_server_intf.split('-')[1]
    #                             else:
    #                                 the_data.a_49 = 'et-' + member_link.old_server_intf.split('-')[1]
    #                         else:
    #                             if member_link.switch_intf == 'et-0/0/48':
    #                                 the_data.b_48 = 'et-' + member_link.old_server_intf.split('-')[1]
    #                             else:
    #                                 the_data.b_49 = 'et-' + member_link.old_server_intf.split('-')[1]
    #     return the_data

    @property
    def is_ct_done(self) -> bool:
        ct_not_done_list = [ tbody_id for tbody_id, gs in self.generic_systems.items() if not gs.is_ct_done]
        return len(ct_not_done_list) == 0


    def sync_tor_generic_systems(self):
        """
        Pull the generic systems data and rebuild generic_systems
        the 1st call
        does not render the web page (TODO: may be render the page)
        """
        if self.generic_systems != {}:
            return

        # build generic_systems data from tor_bp. set the variables 'old-'
        for server_link in self.tor_bp.get_switch_interface_nodes(self.access_switch_pair):
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            new_label = self.set_new_generic_system_label(server_label)
            tbody_id = f"gs-{new_label}"
            # link_id = server_link[CkEnum.LINK]['id']
            old_switch_intf_id = server_link[CkEnum.MEMBER_INTERFACE]['id']
            old_ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            old_ae_id = server_link[CkEnum.EVPN_INTERFACE]['id'] if server_link[CkEnum.EVPN_INTERFACE] else old_switch_intf_id
            speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            old_server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or ''
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            server_data = self.generic_systems.setdefault(tbody_id, _GenericSystem(label=server_label, new_label=self.set_new_generic_system_label(server_label)))
            if switch_intf == 'et-0/0/48':
                server_data.is_leaf_gs = True
                server_data.new_label = server_label  # do not rename leaf_gs
            # breakpoint()
            ae_data = server_data.group_links.setdefault(old_ae_id, _GroupLink(old_ae_name=old_ae_name, old_ae_id=old_ae_id, speed=speed))
            link_data = ae_data.links.setdefault(old_switch_intf_id, _Memberlink(switch=switch, switch_intf=switch_intf, old_server_intf=old_server_intf))
            if tag:
                link_data.add_old_tag(tag)
                # breakpoint()
                self.logger.warning(f"sync_tor_generic_systems {tag=} {server_label=} {tbody_id=}")            
        # set index number for each generic system
        for index, (k, v) in enumerate(self.generic_systems.items()):
            v.index = index + 1

        # setup leaf_gs with deduced interface names for the leaf switches
        the_data = self.leaf_gs
        for tbody_id, server_data in self.generic_systems.items():
            the_data.label = server_data.label
            for ae_link_id, group_link in server_data.group_links.items():
                if group_link.old_ae_name:
                    for member_id, member_link in group_link.links.items():
                        if member_link.switch_intf in ['et-0/0/48', 'et-0/0/49']:
                            # breakpoint()
                            if member_link.switch.endswith(('a', 'c')):  # left tor
                                if member_link.switch_intf == 'et-0/0/48':
                                    the_data.a_48 = 'et-' + member_link.old_server_intf.split('-')[1]
                                else:
                                    the_data.a_49 = 'et-' + member_link.old_server_intf.split('-')[1]
                            else:
                                if member_link.switch_intf == 'et-0/0/48':
                                    the_data.b_48 = 'et-' + member_link.old_server_intf.split('-')[1]
                                else:
                                    the_data.b_49 = 'et-' + member_link.old_server_intf.split('-')[1]

        # breakpoint()
        return


    def sync_main_links(self):
        """
        Not sure of this 
        """
        server_links_dict = {}
        # update generic_systems from main_bp
        for server_link in self.main_bp.get_switch_interface_nodes(self.access_switch_pair):
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            tbody_id = f"gs-{server_label}"
            server_links_dict.setdefault(tbody_id, []).append(server_link)            
        for tbody_id, links in server_links_dict.items():
            # breakpoint()
            self.generic_systems[tbody_id].refresh(self.main_bp, links)

        return


    async def pull_tor_generic_systems_table(self) -> dict:
        """
        Called by main.py from SyncState
        Build generic_systems from tor_blueprint and return the data 
        """
        self.logger.warning(f"pull_tor_generic_systems_table begin")
        # response = _GenericSystemResponse()
        gs_count = len(self.generic_systems)
        # render each generic system
        for tbody_id, server_data in self.generic_systems.items():
            await server_data.sse_tbody()
            # response.values.append(_GenericSystemResponseItem(
            #     id=tbody_id,
            #     newId='',
            #     value=server_data.get_tbody()
            #     ))
        # update caption
        caption = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
        await SseEvent(
            event=SseEventEnum.DATA_STATE,
            data=SseEventData(
                id=SseEventEnum.CAPTION_GS,
                value=caption)).send()

        # update buttion state
        for _, gs in self.generic_systems.items():
            if gs.is_not_done():
                # breakpoint()
                await SseEvent(
                    event=SseEventEnum.DATA_STATE,
                    data=SseEventData(
                        id=SseEventEnum.BUTTON_MIGRATE_GS,
                        state=DataStateEnum.INIT)).send()
                return
        # no init - done
        await SseEvent(
            event=SseEventEnum.DATA_STATE,
            data=SseEventData(
                id=SseEventEnum.BUTTON_MIGRATE_GS,
                state=DataStateEnum.DONE)).send()
        self.logger.warning(f"pull_tor_generic_systems_table end")
        return

    async def migrate_generic_system(self, tbody_id) -> dict:
        """
        """
        self.logger.warning(f"migrate_generic_system {tbody_id=}")
        data = await self.generic_systems[tbody_id].migrate(self.main_bp, self.access_switches)
        return data



    def set_new_generic_system_label(self, old_label) -> str:
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
