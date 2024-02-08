import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import time
import json

from .ck_global import SseEvent, SseEventData

from ck_apstra_api.apstra_blueprint import CkEnum


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
        logging.info(f"a_link_nodes[{CkEnum.GENERIC_SYSTEM_INTERFACE}]['if_name']: {tor_intf_name}, none of {[x for x in translation_table.keys()]}")
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


@dataclass
class AccessSwitcheWorker:
    global_store: Any

    switch_pair_spec: Any = None  # to create access switches. set by sync_tor_gs_in_main
    tor_interface_nodes_in_main: Any = None  # set by sync_tor_gs_in_main
    logger: Any = logging.getLogger("AccessSwitches") 
    virtual_networks_data: Any = None
    # is_access_switches_done: bool = False  # set if access switches are created
    # TODO:

    # @property
    # def bound_to(self):
    #     """
    #     For bulk_csv operation of virtual networks
    #     """
    #     return f"{self.tor_gs.label}-pair"

    # @property
    # def access_switch_pair(self):
    #     return sorted(self.access_switches)
    
    # def is_access_switch_present_in_main(self):
    #     return len([x for x in self.access_switches.values() if x.id != '']) == 2

    # @property
    # def leaf_switch_pair(self):
    #     return sorted(self.leaf_switches)

    @property
    def main_bp(self):
        return self.global_store.bp['main_bp']

    @property
    def tor_bp(self):
        return self.global_store.bp['tor_bp']

    # @property
    # def generic_systems(self):
    #     # if global_store.generic_systems is None:
    #     #     global_store.generic_systems = GenericSystems(main_bp=self.main_bp, tor_bp=self.tor_bp, tor_gs_label=self.tor_gs.label)
    #     #     self.logger.info(f"generic_systems {global_store.generic_systems=}")
    #     return self.global_store.generic_systems

    # @property
    # def virtual_networks(self):
    #     if self.virtual_networks_data is None:
    #         self.virtual_networks_data = VirtualNetworks(main_bp=self.main_bp, tor_bp=self.tor_bp, this_bound_to=self.bound_to)
    #     return self.virtual_networks_data


    # # 
    # # virtual networks
    # # 
    # async def update_virtual_networks_data(self):
    #     await self.virtual_networks.update_virtual_networks_data()
    #     return


    # async def migrate_virtual_networks(self):
    #     data = await self.virtual_networks.migrate_virtual_networks()
    #     return data


    # async def sync_access_switches(self) -> None:
    #     """
    #     sync access switches from tor_bp
    #     The first action for sync operation
    #     Does set_as_done
    #     """

    #     #
    #     #  setup tor_gs label from the name of access switches (came from tor_bp)
    #     #
    #     a_name = next(iter(self.access_switches))
    #     if a_name.endswith(('a', 'b')):
    #         self.tor_gs = TorGS(label=a_name[:-1])
    #     elif a_name.endswith(('c', 'd')):
    #         self.tor_gs = TorGS(label=f"{a_name[:-1]}cd")
    #     else:
    #         self.logger.critical(f"switch name {a_name} does not ends with 'a' - 'd'")

    #     self.logger.info(f"sync_access_switches tor_gs fetched {self.tor_gs=}")

    #     await SseEvent(data=SseEventData(id='access-gs-label', value=self.tor_gs.label).not_done()).send()


    #     #
    #     # build generic systems for tor blueprint and set leaf_gs
    #     # 
    #     await self.generic_systems.sync_tor_generic_systems()  # generic_systems and leaf_gs
    #     self.generic_systems.sync_main_links()  # update generic systems with the data from the main blueprint

    #     await SseEvent(data=SseEventData(id='leaf1-intf1', value=self.leaf_gs.a_48)).send()
    #     await SseEvent(data=SseEventData(id='leaf1-intf2', value=self.leaf_gs.a_49)).send()
    #     await SseEvent(data=SseEventData(id='leaf2-intf1', value=self.leaf_gs.b_48)).send()
    #     await SseEvent(data=SseEventData(id='leaf2-intf2', value=self.leaf_gs.b_49)).send()


    #     # pull the information from main_bp
    #     self.sync_tor_gs_in_main()  # sync tor_gs in main, or access_switches in main, leaf_switches built

    #     if len(self.leaf_switches) == 2:
    #         # leaf switches in main blueprint are loaded
    #         await SseEvent(data=SseEventData(id='leaf1-box').done()).send()
    #         await SseEvent(data=SseEventData(id='leaf2-box').done()).send()
    #         await SseEvent(data=SseEventData(id='leaf1-label', value=self.leaf_switch_pair[0])).send()
    #         await SseEvent(data=SseEventData(id='leaf2-label', value=self.leaf_switch_pair[1])).send()


    #     self.logger.info(f"sync_access_switches {self.access_switches=}")
    #     if len([x.id for x in self.access_switches.values() if x.id != '']) == 2:            
    #         # access switches are created            
    #         await self.global_store.migration_status.set_as_done(True)
    #         # hide access-gs-box, and show access1-box, access2-box
    #         await SseEvent(data=SseEventData(id='access-gs-box').hidden()).send()
    #         await SseEvent(data=SseEventData(id='access-gs-label').hidden()).send()

    #         await SseEvent(data=SseEventData(id='access1-box').visible().done()).send()
    #         await SseEvent(data=SseEventData(id='access1-label', value=self.access_switch_pair[0]).visible()).send()
    #         await SseEvent(data=SseEventData(id='access2-box').visible().done()).send()
    #         await SseEvent(data=SseEventData(id='access2-label', value=self.access_switch_pair[1]).visible()).send()
    #         await SseEvent(data=SseEventData(id='peer-link').visible()).send()
    #         await SseEvent(data=SseEventData(id='peer-link-name').visible()).send()


    #         # update switch configuration section
    #         await SseEvent(data=SseEventData(id='switch-0', value=self.access_switch_pair[0])).send()
    #         await SseEvent(data=SseEventData(id='switch-1', value=self.access_switch_pair[1])).send()

    #     else:
    #         # access switches are not created yet
    #         await SseEvent(data=SseEventData(id='access-gs-box').not_done()).send()

    #     return

    def build_switch_pair_spec(self, tor_interface_nodes_in_main, tor_label) -> dict:
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


    def sync_tor_gs_in_main(self) -> bool:
        """
        sync tor_gs or access_switches in main_bp 
        set self.tor_gs and self.leaf_gs
        Return True if sync is done
        """
        tor_interface_nodes_in_main = self.main_bp.get_server_interface_nodes(self.tor_gs.label)
        # self.logger.info(f"tor_interface_nodes_in_main: begin {len(tor_interface_nodes_in_main)=}")
        if len(tor_interface_nodes_in_main) >= 4:
            for tor_intf_node in tor_interface_nodes_in_main:
                if tor_intf_node[CkEnum.GENERIC_SYSTEM]:
                    self.tor_gs.id = tor_intf_node[CkEnum.GENERIC_SYSTEM]['id']
                if tor_intf_node[CkEnum.EVPN_INTERFACE]:
                    self.tor_gs.ae_id = tor_intf_node[CkEnum.EVPN_INTERFACE]['id']
                if tor_intf_node[CkEnum.LINK]:
                    self.tor_gs.link_ids.append(tor_intf_node[CkEnum.LINK]['id'])

                leaf_label = tor_intf_node[CkEnum.MEMBER_SWITCH]['label']
                leaf_id = tor_intf_node[CkEnum.MEMBER_SWITCH]['id']
                switch_intf = tor_intf_node[CkEnum.MEMBER_INTERFACE]['if_name']
                server_intf = tor_intf_node[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name']

                leaf_data = self.leaf_switches.setdefault(leaf_label, LeafSwitch(label=leaf_label, id=leaf_id))
                leaf_data.links.append(LeafLink(switch_intf=switch_intf, server_intf=server_intf))

            self.switch_pair_spec = self.build_switch_pair_spec(tor_interface_nodes_in_main, self.tor_gs.label)
            self.tor_interface_nodes_in_main = tor_interface_nodes_in_main

        elif self.access_switches:
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
            access_switch_nodes = self.main_bp.query(access_switch_query)
            for nodes in access_switch_nodes:
                switch_label = nodes['ACCESS_SWITCH']['label']
                switch_id = nodes['ACCESS_SWITCH']['id']
                leaf_label = nodes['LEAF']['label']
                leaf_id = nodes['LEAF']['id']
                self.access_switches[switch_label].id = switch_id
                a = self.leaf_switches.setdefault(leaf_label, LeafSwitch(label=leaf_label, id = leaf_id))


    async def create_new_access_switch_pair(self) -> bool:
        """
        Retrun True if the access switches are created
        """
        ########
        # create new access system pair
        # olg logical device is not useful anymore

        # LD _ATL-AS-Q5100-48T, _ATL-AS-5120-48T created
        # IM _ATL-AS-Q5100-48T, _ATL-AS-5120-48T created
        # rack type _ATL-AS-5100-48T, _ATL-AS-5120-48T created and added
        # ATL-AS-LOOPBACK with 10.29.8.0/22
        
        if self.is_access_switch_present_in_main():
            logging.info(f"create_new_access_switch_pair: access switches are already created")
            return
        # main_bp = self.main_bp
        switch_pair_spec = self.switch_pair_spec

        REDUNDANCY_GROUP = 'redundancy_group'
        
        access_switch_pair_created = self.main_bp.add_generic_system(switch_pair_spec)
        logging.info(f"{access_switch_pair_created=}")

        # wait for the new system to be created
        while True:
            new_systems = self.main_bp.query(f"""
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
        self.main_bp.patch_node_single(
            new_systems[0][REDUNDANCY_GROUP]['id'], 
            {"label": self.bound_to }  # redundancy group id to be used for virtual network association
            )

        # rename each access switch for the label and hostname
        for leaf in new_systems:
            given_label = leaf['leaf']['label']
            # when the label is <tor_label>1, rename it to <tor_label>a
            if given_label[-1] == '1':
                new_label = self.access_switch_pair[0]
            # when the labe is <tor_label>2, rename it to <tor_label>b
            elif given_label[-1] == '2':
                new_label = self.access_switch_pair[1]
            else:
                logging.info(f"skipp chaning name {given_label=}")
                continue
            self.main_bp.patch_node_single(
                leaf['leaf']['id'], 
                {"label": new_label, "hostname": new_label }
                )
        
        # hide access-gs-box
        await SseEvent(data=SseEventData(id='access-gs-box').hidden()).send()
        await SseEvent(data=SseEventData(id='access-gs-label').hidden()).send()

        await SseEvent(data=SseEventData(id='access1-box').visible().done()).send()
        await SseEvent(data=SseEventData(id='access2-box').visible().done()).send()
        await SseEvent(data=SseEventData(id='peer-link').visible()).send()
        await SseEvent(data=SseEventData(id='peer-link-name').visible()).send()

        await SseEvent(data=SseEventData(id='access1-label').visible()).send()
        await SseEvent(data=SseEventData(id='access2-label').visible()).send()

        await self.global_store.migration_status.set_as_done(True)
        return


    async def remove_tor_gs_from_main(self) -> bool:
        """
        Remove the old generic system from the main blueprint
        remove the connectivity templates assigned to the generic system
        remove the generic system (links)
        Return True if the generic system is removed
        """
        self.logger.info('remove_tor_gs_from_main - begin {self.tor_gs=}')
        if not self.tor_gs.id:
            self.logger.info(f"tor_gs_id is absent. No need to remove")
            return True
        if not self.tor_gs.ae_id:
            self.logger.info(f"tor_gs.ae_id is absent, but tor_gs.id is present. Something wrong")
            return False
        # main_bp = self.global_store.bp['main_bp']

        tor_interface_nodes_in_main = self.tor_interface_nodes_in_main
        
        # remove the connectivity templates assigned to the generic system
        cts_to_remove = self.main_bp.get_interface_cts(self.tor_gs.ae_id)
        logging.info(f"remove_tor_gs_from_main - {len(cts_to_remove)=}")

        # damping CTs in chunks
        while len(cts_to_remove) > 0:
            throttle_number = 50
            cts_chunk = cts_to_remove[:throttle_number]
            self.logger.info(f"Removing Connecitivity Templates on this links: {len(cts_chunk)=}")
            batch_ct_spec = {
                "operations": [
                    {
                        "path": "/obj-policy-batch-apply",
                        "method": "PATCH",
                        "payload": {
                            "application_points": [
                                {
                                    "id": self.tor_gs.ae_id,
                                    "policies": [ {"policy": x, "used": False} for x in cts_chunk]
                                }
                            ]
                        }
                    }
                ]
            }
            batch_result = self.main_bp.batch(batch_ct_spec, params={"comment": "batch-api"})
            del cts_to_remove[:throttle_number]

        # remove the generic system (links)
        link_remove_spec = {
            "operations": [
                {
                    "path": "/delete-switch-system-links",
                    "method": "POST",
                    "payload": {
                        "link_ids": [ x['link']['id'] for x in tor_interface_nodes_in_main ]
                    }
                }
            ]
        }
        batch_result = self.main_bp.batch(link_remove_spec, params={"comment": "batch-api"})
        self.logger.info(f"{batch_result=} {batch_result.content=} {link_remove_spec=}")
        while True:
            if_generic_system_present = self.main_bp.query(f"node('system', label='{self.tor_gs.label}')")
            if len(if_generic_system_present) == 0:
                break
            logging.info(f"{if_generic_system_present=}")
            time.sleep(3)
        # the generic system is gone.            



        return
