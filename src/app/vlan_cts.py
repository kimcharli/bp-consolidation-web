import logging
from enum import StrEnum
from pydantic import BaseModel

from ck_apstra_api.apstra_blueprint import CkEnum

# from .generic_systems import CtData
from .ck_global import CtEnum, DataStateEnum, SseEvent, SseEventEnum, SseEventData, global_store


class CtData(BaseModel):
    # multiple per link
    vn_id: int
    is_tagged: bool = True
    new_ct_id: str = None  # to capture the ct_id from main_bp

    def reset(self):
        self.new_ct_id = None

interface_vlan_query = f"""match(
    node('ep_endpoint_policy', policy_type_name='batch', name='{CtEnum.CT_NODE}')
        .in_().node('ep_application_instance', name='{CtEnum.EPAE_NODE}')
        .out('ep_affected_by').node('ep_group')
        .in_('ep_member_of').node(name='{CtEnum.INTERFACE_NODE}'),
    node(name='{CtEnum.EPAE_NODE}')
        .out('ep_nested').node('ep_endpoint_policy', policy_type_name='AttachSingleVLAN', name='{CtEnum.SINGLE_VLAN_NODE}')
        .out('vn_to_attach').node('virtual_network', name='{CtEnum.VN_NODE}'),
)"""

def sync_tor_ct(the_bp, generic_systems, switch_label_pair: list) -> dict:
    """
    Pull the single vlan cts for the switch pair
    """

    logging.warning(f"sync_tor_ct begin {the_bp.label=} {switch_label_pair=}")
    interface_vlan_nodes = the_bp.query(interface_vlan_query)
    logging.warning(f"sync_tor_ct BP:{the_bp.label} {len(interface_vlan_nodes)=}")
    # why so many (3172) entries?

    for nodes in interface_vlan_nodes:
        # logging.warning(f"{nodes=}")
        the_interface_id = nodes[CtEnum.INTERFACE_NODE]['id']
        vn_id = int(nodes[CtEnum.VN_NODE]['vn_id'])
        tagged = 'vlan_tagged' in nodes[CtEnum.SINGLE_VLAN_NODE]['attributes']
        the_ae = [x.group_links[the_interface_id] for k, x in generic_systems.items() if the_interface_id in x.group_links ][0]
        # logging.warning(f"{the_ae=}")
        # breakpoint()
        if tagged:
            the_ae.old_tagged_vlans[vn_id] = CtData(vn_id=vn_id, is_tagged=True)
        else:
            the_ae.old_untagged_vlan[vn_id] = CtData(vn_id=vn_id, is_tagged=False)

    return {}

def sync_main_ct(the_bp, generic_systems, switch_label_pair: list):
    """
    Refresh the single vlan cts for the switch pair
    """
    # get the data from main blueprint
    interface_vlan_nodes = the_bp.query(interface_vlan_query)
    if len(interface_vlan_nodes) == 0:
        logging.warning(f"sync_main_ct: no data for {the_bp.label=} {switch_label_pair=}")
        return {}

    for nodes in interface_vlan_nodes:
        # logging.warning(f"{nodes=}")
        ct_node_id = nodes[CtEnum.CT_NODE]['id']
        the_interface_id = nodes[CtEnum.INTERFACE_NODE]['id']
        vn_id = int(nodes[CtEnum.VN_NODE]['vn_id'])
        tagged = 'vlan_tagged' in nodes[CtEnum.SINGLE_VLAN_NODE]['attributes']
        # breakpoint()
        for tbody_id, gs in generic_systems.items():
            for old_ae_id, ae_data in gs.group_links.items():
                if ae_data.new_ae_id and (ae_data.new_ae_id == the_interface_id):
                    # breakpoint()
                    if tagged:
                        ae_data.old_tagged_vlans[vn_id].new_ct_id = ct_node_id
                    else:
                        ae_data.old_untagged_vlan[vn_id].is_tagged = False
                        ae_data.old_untagged_vlan[vn_id].new_ct_id = ct_node_id                   
                else:
                    # assume ae_data.new_ae_id is None. 
                    for link_data in ae_data.links.values():
                        if link_data.new_switch_intf_id == the_interface_id:
                            if tagged:
                                ae_data.old_tagged_vlans[vn_id].new_ct_id = ct_node_id
                            else:
                                ae_data.old_untagged_vlan[vn_id].is_tagged = False
                                ae_data.old_untagged_vlan[vn_id].new_ct_id = ct_node_id
                    # breakpoint()
    return {}

async def referesh_ct_table(generic_systems):
        for _, gs in generic_systems.items():
            for _, ae_data in gs.group_links.items():
                if gs.is_leaf_gs or (ae_data.speed and ae_data.is_old_cts_absent):
                    cell_state = DataStateEnum.NONE
                else:
                    if ae_data.is_ct_done:
                        cell_state = DataStateEnum.DONE
                    else:
                        cell_state = DataStateEnum.INIT
                # breakpoint()
                await SseEvent(
                    event=SseEventEnum.DATA_STATE, 
                    data=SseEventData(
                        id=ae_data.cts_cell_id, 
                        state=cell_state, 
                        value=f'{ae_data.count_of_new_cts}/{ae_data.count_of_old_cts}')).send()


async def migrate_connectivity_templates(main_bp, generic_systems):
    # main_bp = global_store.bp['main_bp']

    # the nodes for the single vlan cts
    ct_vlan_query = f"""node('ep_endpoint_policy', name='{CtEnum.CT_NODE}')
        .out('ep_subpolicy').node('ep_endpoint_policy', policy_type_name='pipeline')
        .out('ep_first_subpolicy').node('ep_endpoint_policy', policy_type_name='AttachSingleVLAN', name='{CtEnum.SINGLE_VLAN_NODE}')
        .out().node('virtual_network', name='{CtEnum.VN_NODE}')"""
    ct_vlan_nodes = main_bp.query(ct_vlan_query)

    # interate generic systems and fix the connectivity templates
    for tbody_id, gs in generic_systems.generic_systems.items():
        if gs.is_leaf_gs:
            # won't fix the connectivity tempaltes towards the leaf switches
            continue
        for old_ae_id, ae_data in gs.group_links.items():
            # ct attachment per group_link
            if ae_data.is_ct_done:
                continue

            ct_data_queue = []
            # add tagged vlan cts
            # TODO: use new_ct_id instead of new_tagged_vlans
            # breakpoint()
            for vn_id, ct_data in ae_data.old_tagged_vlans.items():
                if ct_data.new_ct_id:
                    # it is already migrated
                    continue
                tagged_ct_nodes = [x for x in ct_vlan_nodes if x[CtEnum.VN_NODE]['vn_id'] == str(vn_id) and 'vlan_tagged' in x[CtEnum.SINGLE_VLAN_NODE]['attributes']]
                if len(tagged_ct_nodes) == 0:
                    logging.warning(f"migrate_connectivity_templates: no tagged vlan ct for {vn_id=} ####")
                    continue
                ct_id = tagged_ct_nodes[0][CtEnum.CT_NODE]['id']
                ct_data.new_ct_id = ct_id
                ct_data_queue.append(ct_data)
            for vn_id, ct_data in ae_data.old_untagged_vlan.items():
                if ct_data.new_ct_id:
                    continue
                untagged_ct_nodes = [x for x in ct_vlan_nodes if x[CtEnum.VN_NODE]['vn_id'] == str(vn_id) and 'untagged' in x[CtEnum.SINGLE_VLAN_NODE]['attributes']]
                if len(untagged_ct_nodes) == 0:
                    logging.warning(f"migrate_connectivity_templates: no untagged vlan ct for {vn_id=} ####")
                    break
                ct_id = untagged_ct_nodes[0][CtEnum.CT_NODE]['id']
                ct_data.new_ct_id = ct_id
                ct_data_queue.append(ct_data)
            total_cts = len(ct_data_queue)
            while len(ct_data_queue) > 0:
                throttle_number = 50
                cts_chunk = ct_data_queue[:throttle_number]
                interface_id = ae_data.new_ae_id if ae_data.new_ae_id else [x for x in ae_data.links.values()][0].new_switch_intf_id
                batch_ct_spec = {
                    "operations": [
                        {
                            "path": "/obj-policy-batch-apply",
                            "method": "PATCH",
                            "payload": {
                                "application_points": [
                                    {
                                        "id": interface_id,
                                        "policies": [ {"policy": x.new_ct_id, "used": True} for x in cts_chunk]
                                    }
                                ]
                            }
                        }
                    ]
                }
                batch_result = main_bp.batch(batch_ct_spec, params={"comment": "batch-api"})
                if batch_result.status_code != 201:
                    logging.warning(f"migrate_connectivity_templates: {ae_data=} {len(cts_chunk)=} {batch_ct_spec=} {batch_result=} {batch_result.content=}")
                # if not ae_data.new_ae_id:
                #     logging.warning(f"migrate_connectivity_templates: {ae_data.new_ae_id=} {ae_data=}")
                # for ct_data in cts_chunk:
                #     ae_data.new_tagged_vlans[vn_id] = ae_data.old_tagged_vlans[vn_id]
                del ct_data_queue[:throttle_number]
                cell_state = DataStateEnum.DONE if ae_data.is_ct_done else DataStateEnum.INIT

                await SseEvent(
                    event=SseEventEnum.DATA_STATE, 
                    data=SseEventData(
                        id=ae_data.cts_cell_id, 
                        state=cell_state, 
                        value=f'{ae_data.count_of_new_cts}/{ae_data.count_of_old_cts}')).send()

    await global_store.migration_status.set_ct_done(True)
    # if generic_systems.is_ct_done:
    #     await SseEvent(
    #         event=SseEventEnum.DATA_STATE, 
    #         data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).done()).send()
    # else:
    #     await SseEvent(
    #         event=SseEventEnum.DATA_STATE, 
    #         data=SseEventData(
    #             id=SseEventEnum.BUTTON_MIGRATE_CT).not_done()).send()

    return {}

