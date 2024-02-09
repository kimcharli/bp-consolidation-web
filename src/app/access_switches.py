import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import time
import json

from .ck_global import SseEvent, SseEventData

from ck_apstra_api.apstra_blueprint import CkEnum





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

    @property
    def access_switch_pair(self):
        return self.global_store.access_switch_pair
    
    @property
    def main_bp(self):
        return self.global_store.bp['main_bp']

    @property
    def tor_bp(self):
        return self.global_store.bp['tor_bp']

    @property
    def tor_gs(self):
        return self.global_store.tor_gs


    def build_switch_pair_spec(self) -> dict:
        '''
        Build the switch pair spec from the links query
        '''
        switch_pair_spec = {
            "links": [],
            "new_systems": None
        }

        for leaf_label in sorted(self.global_store.leaf_switches):
            leaf_data = self.global_store.leaf_switches[leaf_label]
            # self.logger.info(f"build_switch_pair_spec {leaf_data=}")
            for link_index, leaf_link in leaf_data.links.items():
                system_peer = 'first' if link_index.startswith('a') else 'second'  # a48, a49, b48, b49
                tor_if_name = 'et-0/0/48' if link_index.endswith('48') else 'et-0/0/49'
                switch_pair_spec['links'].append({
                        "lag_mode": "lacp_active",
                        "system_peer": system_peer,
                        "switch": {
                            "system_id": leaf_data.id,
                            "transformation_id": 2,
                            "if_name": leaf_link.leaf_intf
                        },
                        "system": {
                            "system_id": None,
                            "transformation_id": 1,
                            "if_name": tor_if_name
                        }
                    })
                
        # TODO: 
        with open('./tests/fixtures/fixture-switch-system-links-5120.json', 'r') as file:
            sample_data = json.load(file)

        switch_pair_spec['new_systems'] = sample_data['new_systems']
        switch_pair_spec['new_systems'][0]['label'] = self.tor_gs.label

        return switch_pair_spec


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
        
        if len([x for x in self.global_store.access_switches.values() if x.main_id is not None]):
            logging.info(f"create_new_access_switch_pair: access switches are already created")
            return
        # main_bp = self.main_bp
        switch_pair_spec = self.build_switch_pair_spec()

        REDUNDANCY_GROUP = 'redundancy_group'
        
        self.logger.info(f"create_new_access_switch_pair: {switch_pair_spec['links']=}")
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
            {"label": self.global_store.bound_to }  # redundancy group id to be used for virtual network association
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

        for i in range(10):
            for nodes in self.main_bp.query(f"node('system', label=is_in({self.access_switch_pair}), name='access')"):
                access_label = nodes['access']['label']
                main_id = nodes['access']['id']
                self.global_store.access_switches[access_label].main_id = main_id
            if len([x for x in self.global_store.access_switches.values() if x.main_id is not None]) == 2:
                break
            self.logger.info(f"create_new_access_switch_pair: Waiting for access switches to be created: {i}/10")
            time.sleep(3)

        await SseEvent(data=SseEventData(id='access1-box').visible().done()).send()
        await SseEvent(data=SseEventData(id='access2-box').visible().done()).send()
        await SseEvent(data=SseEventData(id='peer-link').visible()).send()
        await SseEvent(data=SseEventData(id='peer-link-name').visible()).send()

        await SseEvent(data=SseEventData(id='access1-label', value=self.access_switch_pair[0]).visible()).send()
        await SseEvent(data=SseEventData(id='access2-label', value=self.access_switch_pair[1]).visible()).send()

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
        if not self.tor_gs.tor_id:
            self.logger.info(f"tor_gs_id is absent. No need to remove")
            return True
        if not self.tor_gs.ae_id:
            self.logger.error(f"tor_gs.ae_id is absent, but tor_gs.id is present. Something wrong")
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
                        "link_ids": [ x for x in self.tor_gs.link_ids ]
                    }
                }
            ]
        }
        batch_result = self.main_bp.batch(link_remove_spec, params={"comment": "batch-api"})
        # self.logger.info(f"{batch_result=} {batch_result.content=} {link_remove_spec=}")
        while True:
            if_generic_system_present = self.main_bp.query(f"node('system', label='{self.tor_gs.label}')")
            if len(if_generic_system_present) == 0:
                break
            logging.info(f"{if_generic_system_present=}")
            time.sleep(3)
        # the generic system is gone.            
        await SseEvent(data=SseEventData(id='access-gs-label').hidden()).send()
        await SseEvent(data=SseEventData(id='access-gs-box').hidden()).send()

        return

