import logging
from pydantic import BaseModel
from typing import Optional, List
import time
import json

from .ck_global import GlobalStore, DataStateEnum

from .generic_systems import GenericSystems
from ck_apstra_api.apstra_blueprint import CkEnum
from .virtual_networks import VirtualNetworks


class _AccessSwitchResponseItem(BaseModel):
    id: str
    value: Optional[str] = None
    state: Optional[str] = None
    fill: Optional[str] = None
    visibility: Optional[str] = None

    def loaded(self):
        self.state = DataStateEnum.LOADED
        return self

    def hidden(self):
        self.visibility = 'hidden'
        return self

    def visible(self):
        self.visibility = 'visible'
        return self


class _AccessSwitchResponse(BaseModel):
    done: Optional[bool] = False
    values: Optional[List[_AccessSwitchResponseItem]] = []
    caption: Optional[str] = None
    button_state: str = DataStateEnum.INIT


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


class AccessSwitches:
    peer_link = {}  # link-id = { system: {} }
    access_switches = []  # [('atl1tor-r5r15a', {'label': 'atl1tor-r5r15a'}), ('atl1tor-r5r15b', {'label': 'atl1tor-r5r15b'})]
    access_switch_pair = [] # the label of the access switches (tor switches)
    tor_gs = {'label': None, 'id': None, 'ae_id': None}  # {'label': None, 'id': None, 'ae_id': None},  # id and ae_id of main_bp
    leaf_gs = {'intfs': [None] * 4}  #{'label': None, 'intfs': [None] * 4},  # label:, intfs[a-48, a-49, b-48, b-49] - the generic system info for the leaf
    generic_systems = None
    main_bp = None
    tor_bp = None
    leaf_switches = None

    @classmethod
    def load_id_element(cls, id, value):
        return _AccessSwitchResponseItem(id=id, value=value, state=DataStateEnum.LOADED, fill='red')

    @classmethod
    def update_virtual_networks_data(cls):
        data = VirtualNetworks.update_virtual_networks_data(cls.main_bp, cls.tor_bp)
        return data

    @classmethod
    def migrate_generic_system(cls, label):
        data = GenericSystems.migrate_generic_system(label, cls.main_bp, cls.access_switches)
        return data

    # by main.py from SyncState
    @classmethod
    def update_access_switches_table(cls) -> dict:
        cls.tor_bp = GlobalStore.bp['tor_bp']
        cls.main_bp = GlobalStore.bp['main_bp']

        peer_link_query = """
            node('link',role='leaf_leaf',  name='link')
                .in_('link').node('interface', name='intf')
                .in_('hosted_interfaces').node('system', name='switch')
        """
        peer_link_nodes = cls.tor_bp.query(peer_link_query, multiline=True)
        # cls.logger.warning(f"{peer_link_nodes=}")
        temp_access_switches = {}
        for link in peer_link_nodes:
            # register the switch label for further processing later
            switch_label = link['switch']['label']
            temp_access_switches[switch_label] = {'label': switch_label}
            link_id = link['link']['id']
            # peer_link 
            if link_id not in cls.peer_link:
                cls.peer_link[link_id] = { 'system': {} }
            link_data = cls.peer_link[link_id]
            link_data['speed'] = link['link']['speed']
            if switch_label not in link_data['system']:
                link_data['system'][switch_label] = []
            switch_data = link_data['system'][switch_label]
            switch_intf = link['intf']['if_name']
            switch_data.append(switch_intf)
        
        logging.warning(f"update_access_switches_table {temp_access_switches=}")
        cls.access_switches = sorted(temp_access_switches.items())
        cls.access_switch_pair = sorted(temp_access_switches)

        #  setup tor_gs label from the name of tor_bp switches
        logging.warning(f"update_access_switches_table {cls.access_switches=} {cls.tor_gs=}")
        if cls.access_switches[0][0].endswith(('a', 'b')):
            cls.tor_gs['label'] = cls.access_switches[0][0][:-1]
        elif cls.access_switches[0][0].endswith(('c', 'd')):
            cls.tor_gs['label'] = cls.access_switches[0][0][:-1] + 'cd'
        else:
            logging.critical(f"switch names {cls.switches} does not ends with 'a', 'b', 'c', or 'd'!")
        logging.warning(f"update_access_switches_table {cls.access_switches=} {cls.tor_gs=}")

        cls.generic_systems = GenericSystems.pull_generic_systems(cls.main_bp, cls.tor_bp, cls.tor_gs['label'])
        cls.get_leaf_gs()

        for server_label, server_data in GenericSystems.generic_systems.items():
            for group_link in server_data.group_links:
                if group_link.ae_name:
                    for member_link in group_link.links:
                        if member_link.switch_intf in ['et-0/0/48', 'et-0/0/49']:
                            cls.leaf_gs['label'] = server_label
                            if member_link.switch.endswith(('a', 'c')):  # left tor
                                if member_link.switch_intf == 'et-0/0/48':
                                    cls.leaf_gs['intfs'][0] = 'et-' + member_link.server_intf.split('-')[1]
                                else:
                                    cls.leaf_gs['intfs'][1] = 'et-' + member_link.server_intf.split('-')[1]
                            else:
                                if member_link.switch_intf == 'et-0/0/48':
                                    cls.leaf_gs['intfs'][2] = 'et-' + member_link.server_intf.split('-')[1]
                                else:
                                    cls.leaf_gs['intfs'][3] = 'et-' + member_link.server_intf.split('-')[1]


        logging.warning(f"update_access_switches_table {cls.access_switches=} {cls.tor_gs=} {cls.leaf_gs=}")

        response = _AccessSwitchResponse()
        response.values.append(cls.load_id_element('tor1-label', cls.access_switches[0][0])) 
        response.values.append(_AccessSwitchResponseItem(id='tor1-box').loaded()) 
        response.values.append(cls.load_id_element('tor2-label', cls.access_switches[1][0])) 
        response.values.append(_AccessSwitchResponseItem(id='tor2-box').loaded()) 
        response.values.append(cls.load_id_element('leaf-gs-label', cls.leaf_gs['label'])) 
        response.values.append(_AccessSwitchResponseItem(id='leaf-gs-box').loaded()) 
        response.values.append(cls.load_id_element('leafgs1-intf1', cls.leaf_gs['intfs'][0])) 
        response.values.append(cls.load_id_element('leafgs1-intf2', cls.leaf_gs['intfs'][2])) 
        response.values.append(cls.load_id_element('leafgs2-intf1', cls.leaf_gs['intfs'][1])) 
        response.values.append(cls.load_id_element('leafgs2-intf2', cls.leaf_gs['intfs'][3])) 

        response.values.append(cls.load_id_element('leaf1-intf1', cls.leaf_gs['intfs'][0])) 
        response.values.append(cls.load_id_element('leaf1-intf2', cls.leaf_gs['intfs'][2])) 
        response.values.append(cls.load_id_element('leaf2-intf2', cls.leaf_gs['intfs'][1])) 
        response.values.append(cls.load_id_element('leaf2-intf2', cls.leaf_gs['intfs'][3])) 

        if cls.tor_gs['id']:
            response.values.append(cls.load_id_element('access-gs-label', cls.tor_gs['label'])) 
            response.values.append(_AccessSwitchResponseItem(id='access-gs-box').loaded()) 
            response.values.append(cls.load_id_element('leaf1-label', cls.leaf_switches[0][0])) 
            response.values.append(_AccessSwitchResponseItem(id='leaf1-box').loaded()) 
            response.values.append(cls.load_id_element('leaf2-label', cls.leaf_switches[1][0])) 
            response.values.append(_AccessSwitchResponseItem(id='leaf2-box').loaded()) 
        elif cls.leaf_switches[0][1]['id'] and cls.leaf_switches[1][1]['id']:
            response.values.append(cls.load_id_element('leaf1-label', cls.leaf_switches[0][0])) 
            response.values.append(_AccessSwitchResponseItem(id='leaf1-box').loaded()) 
            response.values.append(cls.load_id_element('leaf2-label', cls.leaf_switches[1][0])) 
            response.values.append(_AccessSwitchResponseItem(id='leaf2-box').loaded()) 

            response.values.append(_AccessSwitchResponseItem(id='access-gs-box').hidden()) 
            response.values.append(_AccessSwitchResponseItem(id='access-gs-label').hidden()) 
            response.values.append(_AccessSwitchResponseItem(id='access1-box').visible().loaded()) 
            response.values.append(_AccessSwitchResponseItem(id='access1-label').visible()) 
            response.values.append(_AccessSwitchResponseItem(id='access2-box').visible().loaded()) 
            response.values.append(_AccessSwitchResponseItem(id='access2-label').visible()) 

            response.values.append(cls.load_id_element('access1-label', cls.access_switches[0][0])) 
            response.values.append(cls.load_id_element('access2-label', cls.access_switches[1][0])) 

        if cls.access_switches[0][1]['id'] and cls.access_switches[1][1]['id']:
            response.button_state = DataStateEnum.DONE

        logging.warning(f"update_access_switches_table end... {cls.access_switches=} {cls.leaf_gs=}")
        return response


    @classmethod
    def get_leaf_gs(cls):
        tor_interface_nodes_in_main = cls.main_bp.get_server_interface_nodes(cls.tor_gs['label'])
        if len(tor_interface_nodes_in_main):
            # tor_gs in main_bp
            tor_gs_node = cls.main_bp.query(f"node('system', label='{cls.tor_gs['label']}', name='tor').out().node('interface', if_type='port_channel', name='evpn')")
            if len(tor_gs_node):
                cls.tor_gs['id'] = tor_gs_node[0]['tor']['id']
                cls.tor_gs['ae_id'] = tor_gs_node[0]['evpn']['id']
            logging.warning(f"pull_tor_bp_data {cls.tor_gs=} {tor_gs_node=}")
            leaf_temp = {
                # 'label': { 'label': None, 'id': None, 'links': []},
                # 'label': { 'label': None, 'id': None, 'links': []},
            }
            for member_intf_set in tor_interface_nodes_in_main:
                leaf_label = member_intf_set[CkEnum.MEMBER_SWITCH]['label']
                if leaf_label not in leaf_temp:
                    leaf_temp[leaf_label] = {
                        'label': leaf_label, 
                        'id': member_intf_set[CkEnum.MEMBER_SWITCH]['id'], 
                        'links': []}
                leaf_data = leaf_temp[leaf_label]
                leaf_data['links'].append({
                    'switch_intf': member_intf_set[CkEnum.MEMBER_INTERFACE]['if_name'],
                    'server_intf': member_intf_set[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'],
                    })
                cls.tor_gs['ae_id'] = member_intf_set[CkEnum.EVPN_INTERFACE]['id']
            logging.warning(f"pull_tor_bp_data {leaf_temp=}")
            cls.leaf_switches = sorted(leaf_temp.items(), key=lambda item: item[0])

            cls.switch_pair_spec = build_switch_pair_spec(tor_interface_nodes_in_main, cls.tor_gs['label'])
            cls.tor_interface_nodes_in_main = tor_interface_nodes_in_main

        # TODO: get data when the access_switches are loaded in main_bp
        else:
            access_switch_query = f"""
                match(
                    node('system', system_type='switch', label=is_in({cls.access_switch_pair}), name='ACCESS_SWITCH')
                        .out('hosted_interfaces').node('interface', name='ACCESS_INTF')
                        .out('link').node('link')
                        .in_('link').node('interface', name='LEAF_INTF')
                        .in_('hosted_interfaces').node('system', role='leaf', name='LEAF'),
                    optional(
                        node(name='ACCESS_INTF').in_().node('interface', name='ACCESS_AE')
                    )
                )
            """
            # access_switch_nodes = main_bp.query(f"node('system', label=is_in({access_switch_pair}), name='switch')")
            access_switch_nodes = cls.main_bp.query(access_switch_query, multiline=True)
            access_switches = {x['ACCESS_SWITCH']['label']: {
                'label': x['ACCESS_SWITCH']['label'],
                'id': x['ACCESS_SWITCH']['id'],
                } for x in access_switch_nodes}
            cls.access_switches = sorted(access_switches.items())
            leaf_switches = {x['LEAF']['label']: {
                'label': x['LEAF']['label'],
                'id': x['LEAF']['id'],
                } for x in access_switch_nodes}
            cls.leaf_switches = sorted(leaf_switches.items())
            access_interface_nodes_in_main = cls.main_bp.get_switch_interface_nodes([x[0] for x in cls.access_switches])
            cls.access_interface_nodes_in_main = access_interface_nodes_in_main


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


