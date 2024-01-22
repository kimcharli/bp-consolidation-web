from pydantic import BaseModel
from typing import Optional, List, Dict, Any, ClassVar
import logging
from enum import Enum, StrEnum, auto

from ck_apstra_api.apstra_blueprint import CkEnum
# TODO: consolidate
class DataStateEnum(StrEnum):
    LOADED = 'done'
    INIT = 'init'
    DONE = 'done'
    ERROR = 'error'
    DATA_STATE = 'data-state'

def get_data_or_default(data, label, new_value):
    """
    Return the member data. Or set it to new value
    """
    if hasattr(data, label):
        # class instance
        if not getattr(data, label):
            setattr(data, label, new_value)
        return getattr(data, label)
    # no class. dict
    if label not in data:
        data[label] = new_value    
    return data[label]


class _Memberlink(BaseModel):
    tags: List[str] = []
    new_tags: List[str] = []
    switch: str
    switch_intf: str
    server_intf: Optional[str] = None
    new_server_intf: Optional[str] = None
    main_id: str = ''   # main_id

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
        if self.server_intf == self.new_server_intf:
            trs.append(f'<td data-cell="server_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.server_intf}</td>')
        else:
            trs.append(f'<td data-cell="server_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.server_intf}</td>')
        if self.main_id:
            trs.append(f'<td data-cell="switch" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.switch}</td>')
            trs.append(f'<td data-cell="switch_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.switch_intf}</td>')
        else:
            trs.append(f'<td data-cell="switch" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.switch}</td>')
            trs.append(f'<td data-cell="switch_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.switch_intf}</td>')
        return ''.join(trs)

    def add_tag(self, tag):
        if tag  not in self.tags:
            self.tags.append(tag)

class _GroupLink(BaseModel):
    ae_name: str  # the ae in the tor blueprint
    speed: str
    cts: Optional[List[int]] = []
    tagged_vlans: Optional[List[int]] = []
    untagged_vlan: Optional[int] = None
    new_cts: Optional[List[int]] = []  # the connectivity templates in main blueprint  
    new_ae_name: Optional[str] = None  # the ae in the main blueprint
    new_speed: str = None
    links: Dict[str, _Memberlink] = {}  # <link id from tor>: _Memberlink

    @property
    def rowspan(self):
        return len(self.links)

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
        # row0_head = ''.join([
        #     f'<td rowspan={self.rowspan} data-cell="ae" class="data-state ae" data-state="init">{self.ae_name}</td>',
        #     f'<td rowspan={self.rowspan} data-cell="cts" class="data-state cts" data-state="init">{self.cts}</td>',
        #     f'<td rowspan={self.rowspan} data-cell="speed" class="data-state speed" data-state="{DataStateEnum.INIT}">{self.speed}</td>',
        # ])
        row0_head = ''.join(row0_head_list)
        trs = []
        for index, link_id in enumerate(self.links):
            link = self.links[link_id]
            if index == 0:
                # breakpoint()
                trs.append(row0_head + link.tr)
            else:
                trs.append(link.tr)
        return trs


class _GenericSystem(BaseModel):
    index: int = 0
    label: str  # the label in the tor blueprint
    new_label: str = None  # the label in the main blueprint (renamed)
    new_id: str = None  # the generic system id on main blueprint
    tbody_id: str = None  # the id on the tbody element
    group_links: Dict[str, _GroupLink] = {}  # <group link id or link id of tor>: _GroupLink    

    logger: Any = logging.getLogger('_GenericSystem')

    def get_ae(self, ae_name, speed):
        found_ae = [x for x in self.group_links if x.ae_name == ae_name]
        if len(found_ae):
            return found_ae[0]
        ae_link = _GroupLink(ae_name=ae_name, speed=speed)
        self.group_links.append(ae_link)
        return ae_link

    @property
    def rowspan(self):
        # breakpoint()
        return sum([v.rowspan for k, v in self.group_links.items()])

    def get_tbody(self) -> str:
        """
        Return the tbody innerHTML
        """
        # logging.warning(f"_GenericSystem:get_tbody() begin {self=}")
        row0_head_list = []
        row0_head_list.append(f'<td rowspan={self.rowspan}>{self.index}</td>')
        row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="label" class="system-label">{self.label}</td>')
        if self.new_id:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.DONE}">{self.new_label}</td>')
        else:
            row0_head_list.append(f'<td rowspan={self.rowspan} data-cell="new_label" class="{DataStateEnum.DATA_STATE} new_label" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.new_label}</td>')
        row0_head = ''.join(row0_head_list)       

        # row0_head = ''.join([
        #     f'<td rowspan={self.rowspan}>{index}</td>'
        #     f'<td rowspan={self.rowspan} data-cell="label" class="system-label">{self.label}</td>',
        #     f'<td rowspan={self.rowspan} data-cell="new_label" class="data-state new_label" data-state="init">{self.new_label}</td>',
        # ])
        tbody_lines = []
        for k, ae_link in self.group_links.items():
            for links in ae_link.tr:
                if len(tbody_lines):
                    tbody_lines.append(f'<tr>{links}</tr>')
                else:                    
                    tbody_lines.append(f'<tr>{row0_head}{links}</tr>')
        return ''.join(tbody_lines)

    def create_generic_system(self, main_bp, access_switches):
        lag_group = {}
        generic_system_spec = {
            'links': [],
            'new_systems': [],
        }

        for ae_id, ae_link in self.group_links.items():
            for member_id, member_link in ae_link.links.items():
                switch_label = member_link.switch
                switch_intf = member_link.switch_intf
                # breakpoint()
                generic_system_spec['links'].append({
                    'lag_mode': None,
                    'system': {
                        'system_id': None,
                        'if_name': member_link.server_intf,
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
            'port_channel_id_min': 0,
            'port_channel_id_max': 0,
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
        generic_system_created = main_bp.add_generic_system(generic_system_spec)
        logging.warning(f"generic_system_created: {generic_system_created}")

    def migrate(self, main_bp, access_switches) -> dict:
        """
        Return:
            new_id: new_id
            value: get_tbody()
            caption: caption
        """
        # breakpoint()
        self.logger.warning(f"_GenericSystem::migrate({main_bp=},{access_switches=}) {self=}")
        server_links = main_bp.get_server_interface_nodes(self.new_label)
        # create the generic system if absent
        if len(server_links) == 0:
            self.create_generic_system(main_bp, access_switches)
            server_links = main_bp.get_server_interface_nodes(self.new_label)

        for server_link in server_links:
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            tbody_id = f"gs-{server_label}"  # the server_label would match new_label
            new_id = server_link[CkEnum.GENERIC_SYSTEM]['id']
            link_id = server_link[CkEnum.LINK]['id']
            ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            ae_id = server_link[CkEnum.EVPN_INTERFACE]['id'] if server_link[CkEnum.EVPN_INTERFACE] else link_id
            speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or None
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            # data_from_tor = self.generic_systems[tbody_id]
            # data_from_tor.new_id = new_id
            # search matching member link
            looking = True
            for old_ae_id, ae_data in self.group_links.items():
                for old_link_id, link_data in ae_data.links.items():
                    if link_data.switch == switch and link_data.switch_intf == switch_intf:
                        # found the matching link
                        if tag:
                            link_data.add_tag(tag)
                        looking = False
                        link_data.main_id = link_id
                        ae_data.new_ae_name = ae_name
                        ae_data.new_speed = speed

        return {
            'new_id': self.new_id,  # TODO: no need?
            'value': self.get_tbody(),
            # 'caption': None # TODO: later
        }
        if not self.new_id:
            pass

        """
        Create new generic systems in the main blueprint based on the generic systems in the TOR blueprint. 
            <generic_system_label>:
                <link_id>:
                    gs_if_name: None
                    sw_if_name: xe-0/0/15
                    sw_label: atl1tor-r5r14a
                    speed: 10G
                    aggregate_link: <aggregate_link_id>
                    tags: []

        """
        # if self.new_id:
        #     # it is already present
        #     return {}
        # server_nodes = main_bp.get_system_node_from_label(self.new_label)
        # # breakpoint()
        # if server_nodes is not None:
        #     # it is present in main blueprint
        #     # TODO: update the tbody
        #     return self.update_generic_systems_table()


        # # wait for the access switch to be created
        # for switch_label in order.switch_label_pair:
        #     for i in range(5):
        #         switch_nodes = main_bp.get_system_node_from_label(switch_label)
        #         # it returns None if the system is not created yet
        #         if switch_nodes:
        #             break
        #         logging.info(f"waiting for {switch_label} to be created in {main_bp.label}")
        #         time.sleep(3)
        # logging.info(f"{order.switch_label_pair} present in {main_bp.label}")

        # # itrerate through the generic systems retrived from the TOR blueprint
        # for generic_system_label, gs_data in generic_system_data.items():
        #     # working with a generic system 
        #     logging.debug(f"Creating {generic_system_label=} {gs_data=}")
        #     # if generic_system_label not in [ 'az1kvm1008-az1kvm1028-atl1-LACP' ]:
        #     #     continue
        #     # breakpoint()
        #     # see if this generic system is already present in the main blueprint
        #     if main_bp.get_system_node_from_label(generic_system_label):
        #         logging.info(f"skipping: {generic_system_label} is present in the main blueprint")
        #         # TODO: compare and revise the generic system
        #         continue
        #     ########

        lag_group = {}
        generic_system_spec = {
            'links': [],
            'new_systems': [],
        }

        for ae_id, ae_link in self.group_links.items():
            for member_id, member_link in ae_link.links.items():
                switch_label = member_link.switch
                switch_intf = member_link.switch_intf
                # breakpoint()
                generic_system_spec['links'].append({
                    'lag_mode': None,
                    'system': {
                        'system_id': None,
                        'if_name': member_link.server_intf,
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
            'port_channel_id_min': 0,
            'port_channel_id_max': 0,
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
        generic_system_created = main_bp.add_generic_system(generic_system_spec)
        logging.warning(f"generic_system_created: {generic_system_created}")

        # update the lag mode
        """
        lag_spec example:
            "links": {
                "atl1tor-r5r14a<->_atl_rack_1_001_sys072(link-000000001)[1]": {
                    "group_label": "link1",
                    "lag_mode": "lacp_active"
                },
                "atl1tor-r5r14b<->_atl_rack_1_001_sys072(link-000000002)[1]": {
                    "group_label": "link1",
                    "lag_mode": "lacp_active"
                }
            }            
        """
        lag_spec = {
            'links': {}
        }

        # for i in range(len(link_list)):
        # # for _, link_data in generic_system_data.items():
        #     link_data = link_list[i]
        #     if 'aggregate_link' in link_data and link_data['aggregate_link']:
        #         lag_spec['links'][generic_system_created[i]] = {
        #             'group_label': link_data['aggregate_link'],
        #             'lag_mode': 'lacp_active' }

        #     # tag the link
        #     if len(link_data['tags']):
        #         tagged = main_bp.post_tagging([generic_system_created[i]], tags_to_add=link_data['tags'])
        #         logging.debug(f"{tagged=}")

        # if len(lag_spec['links']):
        #     lag_updated = main_bp.patch_leaf_server_link_labels(lag_spec)
        #     logging.debug(f"lag_updated: {lag_updated}")

        # # update generic system interface name
        # for link_data in [v for _, v in gs_data.items() if v['gs_if_name']]:
        #     sw_label = link_data['sw_label']
        #     sw_if_name = link_data['sw_if_name']
        #     gs_if_name = link_data['gs_if_name']
        #     link_query = f"""
        #         node('system', name='switch', label='{ sw_label }')
        #             .out().node('interface', if_name='{ sw_if_name }', name='sw_intf')
        #             .out().node('link', name='link')
        #             .in_().node('interface', name='gs_intf')
        #             .in_().node('system', system_type='server', name='server')
        #     """
        #     for i in range(3):
        #         link_nodes = main_bp.query(link_query, multiline=True)
        #         if len(link_nodes) > 0:
        #             break
        #         logging.info(f"waiting for {sw_label}:{sw_if_name} to be created in {main_bp.label}")
        #         time.sleep(3)
        #         continue
        #     if link_nodes is None or len(link_nodes) == 0:
        #         logging.warning(f"{link_nodes=} not found. {gs_if_name=}, {link_query=}. Skipping")
        #         continue
        #     if link_nodes[0]['gs_intf']['if_name'] != gs_if_name:
        #         main_bp.patch_node_single(
        #             link_nodes[0]['gs_intf']['id'], 
        #             {"if_name": gs_if_name }
        #         )
    


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
                # breakpoint()
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
            new_label = self.rename_label(server_label)
            tbody_id = f"gs-{new_label}"  # to be useful in main_bp
            link_id = server_link[CkEnum.LINK]['id']
            ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            ae_id = server_link[CkEnum.EVPN_INTERFACE]['id'] if server_link[CkEnum.EVPN_INTERFACE] else link_id
            speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or None
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            # breakpoint()
            server_data = generic_systems.setdefault(tbody_id, _GenericSystem(label=server_label, new_label=self.rename_label(server_label)))
            ae_data = server_data.group_links.setdefault(ae_id, _GroupLink(ae_name=ae_name, speed=speed))
            link_data = ae_data.links.setdefault(link_id, _Memberlink(switch=switch, switch_intf=switch_intf, server_intf=server_intf))
            if tag:
                link_data.add_tag(tag)
        for index, (k, v) in enumerate(generic_systems.items()):
            v.index = index + 1
        self.generic_systems = generic_systems

        # update generic_systems from main_bp
        for server_link in self.main_bp.get_switch_interface_nodes(self.access_switch_pair):
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            tbody_id = f"gs-{server_label}"  # the server_label would match new_label
            new_id = server_link[CkEnum.GENERIC_SYSTEM]['id']
            link_id = server_link[CkEnum.LINK]['id']
            ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            ae_id = server_link[CkEnum.EVPN_INTERFACE]['id'] if server_link[CkEnum.EVPN_INTERFACE] else link_id
            speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or None
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            data_from_tor = self.generic_systems[tbody_id]
            data_from_tor.new_id = new_id
            # search matching member link
            looking = True
            for old_ae_id, ae_data in data_from_tor.group_links.items():
                for old_link_id, link_data in ae_data.links.items():
                    if link_data.switch == switch and link_data.switch_intf == switch_intf:
                        # found the matching link
                        if tag:
                            link_data.add_tag(tag)
                        looking = False
                        link_data.main_id = link_id
                        ae_data.new_ae_name = ae_name
                        ae_data.new_speed = speed

        return

    def rename_label(self, old_label):
        """
        Return new label of the generic system from the old label and tor name
        This is to avoid duplicate names which was created by old tor_bp
        """
        old_patterns = ['_atl_rack_1_000_', '_atl_rack_1_001_', '_atl_rack_5120_001_']
        # self.logger.warning(f"rename_label() {old_label=} {self.tor_gs_label=}")
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
