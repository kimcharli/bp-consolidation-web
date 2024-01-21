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
    server_intf: str = ''
    switch: str
    switch_intf: str
    main_id: str = ''   # main_id

    @property
    def tr(self) -> str:
        trs = [
            f'<td data-cell="tags" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.tags}</td>',
            f'<td data-cell="server_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.server_intf}</td>',
            f'<td data-cell="switch" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.switch}</td>',
            f'<td data-cell="switch_intf" class="{DataStateEnum.DATA_STATE}" {DataStateEnum.DATA_STATE}="{DataStateEnum.INIT}">{self.switch_intf}</td>',
        ]
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
    links: Dict[str, _Memberlink] = {}  # <link id from tor>: _Memberlink

    @property
    def rowspan(self):
        return len(self.links)

    @property
    def tr(self) -> list:
        row0_head = ''.join([
            f'<td rowspan={self.rowspan} data-cell="ae" class="data-state ae" data-state="init">{self.ae_name}</td>',
            f'<td rowspan={self.rowspan} data-cell="cts" class="data-state cts" data-state="init">{self.cts}</td>',
            f'<td rowspan={self.rowspan} data-cell="speed" class="data-state speed" data-state="init">{self.speed}</td>',
        ])
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
    label: str  # the label in the tor blueprint
    new_label: str = None  # the label in the main blueprint (renamed)
    new_id: Optional[str] = None  # the generic system id on main blueprint
    tbody_id: Optional[str] = None  # the id on the tbody element
    group_links: Dict[str, _GroupLink] = {}  # <group link id or link id of tor>: _GroupLink

    logger: Any = logging.getLogger('_GenericSystem')
    # tor_gs_label: str  # for renaming TODO: remove this


    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #     """
    #     set new label from old label
    #     """
    #     old_patterns = ['_atl_rack_1_000_', '_atl_rack_1_001_', '_atl_rack_5120_001_']
    #     # get the prefix from tor_name
    #     prefix = self.tor_gs_label[len('atl1tor-'):]
    #     for pattern in old_patterns:
    #         if self.label.startswith(pattern):
    #             # replace the string with the prefix
    #             self.new_label = f"{prefix}-{self.label[len(pattern):]}"
    #             return
    #     # it doesn't starts with the patterns. See if it is too long to prefix
    #     max_len = 32
    #     if ( len(self.label) + len(prefix) + 1 ) > max_len:
    #         # TODO: too long. potential of conflict
    #         self.new_label = self.label
    #         return
    #     # good to just prefix
    #     self.new_label = f"{prefix}-{self.label}"
    #     return


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

    def get_tbody(self, index) -> str:
        """
        Return the tbody innerHTML
        """
        # logging.warning(f"_GenericSystem:get_tbody() begin {self=}")
        row0_head = ''.join([
            f'<td rowspan={self.rowspan}>{index}</td>'
            f'<td rowspan={self.rowspan} data-cell="label" class="system-label">{self.label}</td>',
            f'<td rowspan={self.rowspan} data-cell="new_label" class="data-state new_label" data-state="init">{self.new_label}</td>',
        ])
        tbody_lines = []
        for k, ae_link in self.group_links.items():
            for links in ae_link.tr:
                if len(tbody_lines):
                    tbody_lines.append(f'<tr>{links}</tr>')
                else:                    
                    tbody_lines.append(f'<tr>{row0_head}{links}</tr>')
        return ''.join(tbody_lines)

    def migrate(self, main_bp, access_switches) -> dict:
        """
        Return:
            id: tbody-id
            value: get_tbody()
        """
        logging.warning(f"_GenericSystem::migrate({main_bp=},{access_switches=}) {self=}")
        if self.new_id:
            return {}
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
        if self.new_id:
            # it is already present
            return {}
        server_nodes = main_bp.get_system_node_from_label(self.new_label)
        # breakpoint()
        if server_nodes is not None:
            # it is present in main blueprint
            # TODO: update the tbody
            return self.update_generic_systems_table()

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
        index = 0
        gs_count = len(self.generic_systems)
        for tbody_id, server_data in self.generic_systems.items():
            index += 1
            # id = f"gs-{server_label}"
            content.values.append(_GenericSystemResponseItem(
                id=tbody_id,
                newId='',
                value=server_data.get_tbody(index)
                ))
        # content['caption'] = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
        content.caption = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
        return content

    def migrate_generic_system(self, tbody_id) -> dict:
        """
        """
        self.logger.warning(f"migrate_generic_system {tbody_id=}")
        data = self.generic_systems[tbody_id].migrate(self.main_bp, self.access_switches)
        return {
            'done': True,
            'values': [],
            'data': data
        }

    def pull_generic_systems(self):
        """
        the 1st call
        Pull the generic systems data and rebuild generic_systems
        """
        generic_systems = {}

        # build generic_systems data from tor_bp
        for server_link in self.tor_bp.get_switch_interface_nodes(self.access_switch_pair):
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            tbody_id = f"gs-{server_label}"
            link_id = server_link[CkEnum.LINK]['id']
            ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            ae_id = server_link[CkEnum.AE_INTERFACE]['id'] if server_link[CkEnum.AE_INTERFACE] else link_id
            speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or ''
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None

            server_data = generic_systems.setdefault(tbody_id, _GenericSystem(label=server_label, new_label=self.rename_label(server_label)))
            ae_data = server_data.group_links.setdefault(ae_id, _GroupLink(ae_name=ae_name, speed=speed))
            link_data = ae_data.links.setdefault(link_id, _Memberlink(switch=switch, switch_intf=switch_intf, server_intf=server_intf))
            if tag:
                link_data.add_tag(tag)
            # breakpoint()
        self.generic_systems = generic_systems

        for server_link in self.main_bp.get_switch_interface_nodes(self.access_switch_pair):
            server_label = server_link[CkEnum.GENERIC_SYSTEM]['label']
            tbody_id = f"gs-{server_label}"
            link_id = server_link[CkEnum.LINK]['id']
            ae_name = server_link[CkEnum.AE_INTERFACE]['if_name'] if server_link[CkEnum.AE_INTERFACE] else ''
            ae_id = server_link[CkEnum.AE_INTERFACE]['id'] if server_link[CkEnum.AE_INTERFACE] else link_id
            speed = server_link[CkEnum.LINK]['speed']
            switch = server_link[CkEnum.MEMBER_SWITCH]['label']
            switch_intf = server_link[CkEnum.MEMBER_INTERFACE]['if_name']
            server_intf = server_link[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'] or ''
            # breakpoint()
            # self.logger.warning(f"{server_link[CkEnum.TAG]=}, {type(server_link[CkEnum.TAG])=}")
            tag = server_link[CkEnum.TAG]['label'] if server_link[CkEnum.TAG] != None else None
            # tag = server_link[CkEnum.TAG]['tag']

            # server_data = get_data_or_default(  # GenericSystem
            #     self.generic_systems, 
            #     tbody_id,
            #     _GenericSystem(
            #         label = server_label,
            #         tor_gs_label=self.tor_gs_label,
            #         # new_label = cls.new_label(server_label),
            #     )
            # )
            # ae_data = get_data_or_default(
            #     server_data.group_links,
            #     ae_id,
            #     _GroupLink(ae_name=ae_name, speed=speed)
            # )
            # link_data = get_data_or_default(
            #     ae_data.links,
            #     link_id,
            #     _Memberlink(switch=switch, switch_intf=switch_intf, server_intf=server_intf)
            # )
            # if tag:
            #     link_data.add_tag(tag)
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
