import logging
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import json

from .ck_global import global_store, DataStateEnum, sse_queue, CtEnum, SseEventEnum, SseEvent, SseEventData

from .generic_systems import GenericSystems, LeafGS
from ck_apstra_api.apstra_blueprint import CkEnum
from .virtual_networks import VirtualNetworks
from .vlan_cts import pull_tor_ct_data, pull_main_ct_data, referesh_ct_table, migrate_connectivity_templates


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


class PeerSystem(BaseModel):
    switch_intf: List[str] = []


class LeafLink(BaseModel):
    server_intf: str = ''
    switch_intf: str
class LeafSwitch(BaseModel):
    label: str
    id: str
    links: List[LeafLink] = []

class AccessSwitch(BaseModel):
    label: str
    id: str = ''

class TorGS(BaseModel):
    label: str
    id: str = None
    ae_id: str = None

# class LeafGS(BaseModel):
#     label: str 
#     intfs: List[str] = []

class AccessSwitches(BaseModel):
    access_switches: Dict[str, AccessSwitch] = {}  # [('atl1tor-r5r15a', {'label': 'atl1tor-r5r15a'}), ('atl1tor-r5r15b', {'label': 'atl1tor-r5r15b'})]
    tor_gs: TorGS = TorGS(label='')  # {'label': None, 'id': None, 'ae_id': None},  # id and ae_id of main_bp
    leaf_gs: LeafGS = None  # = {'intfs': [None] * 4}  #{'label': None, 'intfs': [None] * 4},  # label:, intfs[a-48, a-49, b-48, b-49] - the generic system info for the leaf
    generic_systems_data: Any = None
    leaf_switches: Dict[str, LeafSwitch] = None
    logger: Any = logging.getLogger("AccessSwitches") 
    virtual_networks: Any = None
    # TODO:
    this_bound_to: str = 'atl1tor-r5r15-pair'  # to be updated

    @property
    def access_switch_pair(self):
        return sorted(self.access_switches)

    @property
    def leaf_switch_pair(self):
        return sorted(self.leaf_switches)

    @property
    def main_bp(self):
        return global_store.bp['main_bp']

    @property
    def tor_bp(self):
        return global_store.bp['tor_bp']

    @property
    def generic_systems(self):
        if self.generic_systems_data is None:
            self.generic_systems_data = GenericSystems(main_bp=self.main_bp, tor_bp=self.tor_bp, access_switches=self.access_switches, tor_gs_label=self.tor_gs.label)
            self.logger.warning(f"generic_systems {self.generic_systems_data=}")
        return self.generic_systems_data

    @classmethod
    def load_id_element(cls, id, value):
        return _AccessSwitchResponseItem(id=id, value=value, state=DataStateEnum.LOADED, fill='red')

    # 
    # generic systems
    # 
    async def update_generic_systems_table(self):
        self.logger.warning(f"update_generic_systems_table begin...")
        data = await self.generic_systems.pull_tor_generic_systems_table()
        self.logger.warning(f"update_generic_systems_table end...")
        return data

    def migrate_generic_system(self, tbody_id):
        self.generic_systems.access_switches = self.access_switches
        data = self.generic_systems.migrate_generic_system(tbody_id)
        return data

    # 
    # virtual networks
    # 
    async def update_virtual_networks_data(self):
        if self.virtual_networks is None:
            self.virtual_networks = VirtualNetworks(main_bp=self.main_bp, tor_bp=self.tor_bp, this_bound_to=self.this_bound_to)
        data = await self.virtual_networks.update_virtual_networks_data()
        return data


    async def migrate_virtual_networks(self):
        data = await self.virtual_networks.migrate_virtual_networks()
        return data


    # 
    # connectivity template
    #
    async def update_connectivity_template_data(self):
        await SseEvent(event=SseEventEnum.DATA_STATE, data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT, state=DataStateEnum.LOADING)).send()

        data = pull_tor_ct_data(global_store.bp['tor_bp'], self.generic_systems.generic_systems, self.access_switch_pair)
        pull_main_ct_data(global_store.bp['main_bp'], self.generic_systems.generic_systems, self.access_switch_pair)

        await referesh_ct_table(self.generic_systems.generic_systems)

        if self.generic_systems.is_ct_done:
            button_state = DataStateEnum.DONE
        else:
            button_state = DataStateEnum.INIT
        # breakpoint()
        self.logger.warning(f"update_connectivity_template_data {button_state=}")
        await SseEvent(
            event=SseEventEnum.DATA_STATE, 
            data=SseEventData(
                id=SseEventEnum.BUTTON_MIGRATE_CT, 
                state=button_state)).send()
        # if virtual network is not done, disable the migrate CT button
        # if button_state != DataStateEnum.DONE:
        #     await SseEvent(
        #         event=SseEventEnum.DATA_STATE, 
        #         data=SseEventData(
        #             id=SseEventEnum.BUTTON_MIGRATE_CT, 
        #             state=DataStateEnum.DONE)).send()

        return {}

    async def migrate_connectivity_templates(self):
        await migrate_connectivity_templates(global_store.bp['main_bp'], self.generic_systems.generic_systems)


    # the 1st action: called by main.py from SyncState
    def update_access_switches_table(self) -> dict:
        #
        # build self.access_switches from peer link data of tor_bp
        # TODO: remove peer_link
        #
        if self.virtual_networks is None:
            self.virtual_networks = VirtualNetworks(main_bp=self.main_bp, tor_bp=self.tor_bp, this_bound_to=self.this_bound_to)

        class PeerLink(BaseModel):
            speed: str
            system: Dict[str, PeerSystem] = {}

        peer_link: Dict[str, PeerLink] = {}

        peer_link_query = """
            node('link',role='leaf_leaf',  name='link')
                .in_('link').node('interface', name='intf')
                .in_('hosted_interfaces').node('system', name='switch')
        """
        peer_link_nodes = self.tor_bp.query(peer_link_query, multiline=True)
        for link_nodes in peer_link_nodes:
            switch_label = link_nodes['switch']['label']
            switch_id = link_nodes['switch']['id']
            link_id = link_nodes['link']['id']
            link_data = peer_link.setdefault(link_id, PeerLink(speed=link_nodes['link']['speed']))
            link_system = link_data.system.setdefault(switch_label, PeerSystem())
            link_system.switch_intf.append(link_nodes['intf']['if_name'])
            # breakpoint()
            # create empty access switch
            self.access_switches.setdefault(switch_label, AccessSwitch(label=switch_label))
        

        self.logger.warning(f"update_access_switches_table {self.access_switches=}")

        #
        #  setup tor_gs label from the name of access switches (came from tor_bp)
        #
        a_name = next(iter(self.access_switches))
        # self.logger.warning(f"{a_name=}")
        if a_name.endswith(('a', 'b')):
            self.tor_gs = TorGS(label=a_name[:-1])
        elif a_name.endswith(('c', 'd')):
            self.tor_gs = TorGS(label=f"{a_name[:-1]}cd")
        else:
            self.logger.critical(f"switch name {a_name} does not ends with 'a' - 'd'")

        #
        # build generic systems
        # 
        self.generic_systems.pull_tor_generic_systems()

        self.leaf_gs = self.generic_systems.leaf_gs

        # breakpoint()
        # TODO: clarify
        self.get_leaf_gs()

        # for server_label, server_data in GenericSystems.generic_systems.items():
        #     for group_link in server_data.group_links:
        #         if group_link.ae_name:
        #             for member_link in group_link.links:
        #                 if member_link.switch_intf in ['et-0/0/48', 'et-0/0/49']:
        #                     cls.leaf_gs['label'] = server_label
        #                     if member_link.switch.endswith(('a', 'c')):  # left tor
        #                         if member_link.switch_intf == 'et-0/0/48':
        #                             cls.leaf_gs['intfs'][0] = 'et-' + member_link.server_intf.split('-')[1]
        #                         else:
        #                             cls.leaf_gs['intfs'][1] = 'et-' + member_link.server_intf.split('-')[1]
        #                     else:
        #                         if member_link.switch_intf == 'et-0/0/48':
        #                             cls.leaf_gs['intfs'][2] = 'et-' + member_link.server_intf.split('-')[1]
        #                         else:
        #                             cls.leaf_gs['intfs'][3] = 'et-' + member_link.server_intf.split('-')[1]


        logging.warning(f"update_access_switches_table {self.access_switches=} {self.tor_gs=} {self.leaf_gs=}")

        response = _AccessSwitchResponse()
        # breakpoint()
        response.values.append(self.load_id_element('tor1-label', self.access_switches[self.access_switch_pair[0]].label)) 
        response.values.append(_AccessSwitchResponseItem(id='tor1-box').loaded()) 
        response.values.append(self.load_id_element('tor2-label', self.access_switches[self.access_switch_pair[1]].label)) 
        response.values.append(_AccessSwitchResponseItem(id='tor2-box').loaded()) 
        response.values.append(self.load_id_element('leaf-gs-label', self.leaf_gs.label)) 
        response.values.append(_AccessSwitchResponseItem(id='leaf-gs-box').loaded()) 
        response.values.append(self.load_id_element('leafgs1-intf1', self.leaf_gs.a_48)) 
        response.values.append(self.load_id_element('leafgs1-intf2', self.leaf_gs.a_49)) 
        response.values.append(self.load_id_element('leafgs2-intf1', self.leaf_gs.b_48)) 
        response.values.append(self.load_id_element('leafgs2-intf2', self.leaf_gs.b_49)) 

        response.values.append(self.load_id_element('leaf1-intf1', self.leaf_gs.a_48)) 
        response.values.append(self.load_id_element('leaf1-intf2', self.leaf_gs.a_49)) 
        response.values.append(self.load_id_element('leaf2-intf2', self.leaf_gs.b_48)) 
        response.values.append(self.load_id_element('leaf2-intf2', self.leaf_gs.b_49)) 

        if self.tor_gs.id:
            response.values.append(self.load_id_element('access-gs-label', self.tor_gs.label)) 
            response.values.append(_AccessSwitchResponseItem(id='access-gs-box').loaded()) 
            response.values.append(self.load_id_element('leaf1-label', self.leaf_switches[self.leaf_switch_pair[0]].label)) 
            response.values.append(_AccessSwitchResponseItem(id='leaf1-box').loaded()) 
            response.values.append(self.load_id_element('leaf2-label', self.leaf_switches[self.leaf_switch_pair[1]].label)) 
            response.values.append(_AccessSwitchResponseItem(id='leaf2-box').loaded()) 
        elif self.leaf_switches[self.leaf_switch_pair[0]].id and self.leaf_switches[self.leaf_switch_pair[0]].id:
            response.values.append(self.load_id_element('leaf1-label', self.leaf_switches[self.leaf_switch_pair[0]].label)) 
            response.values.append(_AccessSwitchResponseItem(id='leaf1-box').loaded()) 
            response.values.append(self.load_id_element('leaf2-label', self.leaf_switches[self.leaf_switch_pair[1]].label)) 
            response.values.append(_AccessSwitchResponseItem(id='leaf2-box').loaded()) 

            response.values.append(_AccessSwitchResponseItem(id='access-gs-box').hidden()) 
            response.values.append(_AccessSwitchResponseItem(id='access-gs-label').hidden()) 
            response.values.append(_AccessSwitchResponseItem(id='access1-box').visible().loaded()) 
            response.values.append(_AccessSwitchResponseItem(id='access1-label').visible()) 
            response.values.append(_AccessSwitchResponseItem(id='access2-box').visible().loaded()) 
            response.values.append(_AccessSwitchResponseItem(id='access2-label').visible()) 

            response.values.append(self.load_id_element('access1-label', self.access_switches[self.access_switch_pair[0]].label)) 
            response.values.append(self.load_id_element('access2-label', self.access_switches[self.access_switch_pair[1]].label)) 

        if self.access_switches[self.access_switch_pair[0]].id and self.access_switches[self.access_switch_pair[1]].id:
            response.button_state = DataStateEnum.DONE

        logging.warning(f"update_access_switches_table end... {self.access_switches=} {self.leaf_gs=}")
        return response


    def get_leaf_gs(self):
        #
        # update self.tor_gs
        #
        tor_interface_nodes_in_main = self.main_bp.get_server_interface_nodes(self.tor_gs.label)
        if len(tor_interface_nodes_in_main):
            # tor_gs present in main_bp - prep to remove it
            tor_gs_node = self.main_bp.query(f"node('system', label='{self.tor_gs.label}', name='tor').out().node('interface', if_type='port_channel', name='evpn')")
            if len(tor_gs_node):
                self.tor_gs.id = tor_gs_node[0]['tor']['id']
                self.tor_gs.ae_id = tor_gs_node[0]['evpn']['id']
            self.logger.warning(f"pull_tor_bp_data {self.tor_gs=}")
            # leaf_temp = {
            #     # 'label': { 'label': None, 'id': None, 'links': []},
            #     # 'label': { 'label': None, 'id': None, 'links': []},
            # }
            for member_intf_set in tor_interface_nodes_in_main:
                leaf_label = member_intf_set[CkEnum.MEMBER_SWITCH]['label']
                leaf_id = member_intf_set[CkEnum.MEMBER_SWITCH]['id']
                switch_intf = member_intf_set[CkEnum.MEMBER_INTERFACE]['if_name']
                server_intf = member_intf_set[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name']
                leaf_data = self.leaf_switches.setdefault(leaf_label, LeafSwitch(label=leaf_label, id=leaf_id))
                # if leaf_label not in leaf_temp:
                #     leaf_temp[leaf_label] = {
                #         'label': leaf_label, 
                #         'id': member_intf_set[CkEnum.MEMBER_SWITCH]['id'], 
                #         'links': []}
                # leaf_data = leaf_temp[leaf_label]
                leaf_data.links.append(LeafLink(switch_intf=switch_intf,server_intf=server_intf))
            # logging.warning(f"pull_tor_bp_data {leaf_temp=}")
            # cls.leaf_switches = sorted(leaf_temp.items(), key=lambda item: item[0])

            cls.switch_pair_spec = build_switch_pair_spec(tor_interface_nodes_in_main, cls.tor_gs['label'])
            cls.tor_interface_nodes_in_main = tor_interface_nodes_in_main

        # TODO: get data when the access_switches are loaded in main_bp
        else:
            # tor_gs absent. see if access switches are present
            access_switch_query = f"""
                match(
                    node('system', system_type='switch', label=is_in({self.access_switch_pair}), name='ACCESS_SWITCH')
                        .out('hosted_interfaces').node('interface', name='ACCESS_INTF')
                        .out('link').node('link')
                        .in_('link').node('interface', name='LEAF_INTF')
                        .in_('hosted_interfaces').node('system', role='leaf', name='LEAF'),
                    optional(
                        node(name='ACCESS_INTF').in_().node('interface', name='ACCESS_AE')
                    )
                )
            """
            self.logger.warning(f"before access/leaf switches: {self.access_switches=} {self.leaf_switches=}")
            access_switch_nodes = self.main_bp.query(access_switch_query, multiline=True)
            # access_switches = {x['ACCESS_SWITCH']['label']: {
            #     'label': x['ACCESS_SWITCH']['label'],
            #     'id': x['ACCESS_SWITCH']['id'],
            #     } for x in access_switch_nodes}
            self.access_switches = {x['ACCESS_SWITCH']['label']: 
                                    AccessSwitch(label=x['ACCESS_SWITCH']['label'], id=x['ACCESS_SWITCH']['id']) 
                                    for x in access_switch_nodes}
            # self.access_switches = sorted(access_switches.items())
            # leaf_switches = {x['LEAF']['label']: {
            #     'label': x['LEAF']['label'],
            #     'id': x['LEAF']['id'],
            #     } for x in access_switch_nodes}
            # self.leaf_switches = sorted(leaf_switches.items())
            self.leaf_switches = {
                x['LEAF']['label']: LeafSwitch(label=x['LEAF']['label'], id=x['LEAF']['id'])
                for x in access_switch_nodes
            }
            # access_interface_nodes_in_main = self.main_bp.get_switch_interface_nodes([x[0] for x in cls.access_switches])
            # self.access_interface_nodes_in_main = access_interface_nodes_in_main
            self.logger.warning(f"after access/leaf switches: {self.access_switches=} {self.leaf_switches=}")


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


access_switches = AccessSwitches()
