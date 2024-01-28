import logging
from enum import StrEnum

from ck_apstra_api.apstra_blueprint import CkEnum

from .generic_systems import CtData
from .ck_global import CtEnum

interface_vlan_query = f"""match(
    node('ep_endpoint_policy', policy_type_name='batch', name='{CtEnum.CT_NODE}')
        .in_().node('ep_application_instance', name='{CtEnum.EPAE_NODE}')
        .out('ep_affected_by').node('ep_group')
        .in_('ep_member_of').node(name='{CtEnum.INTERFACE_NODE}'),
    node(name='{CtEnum.EPAE_NODE}')
        .out('ep_nested').node('ep_endpoint_policy', policy_type_name='AttachSingleVLAN', name='{CtEnum.SINGLE_VLAN_NODE}')
        .out('vn_to_attach').node('virtual_network', name='{CtEnum.VN_NODE}'),
)"""

def pull_interface_vlan_table(the_bp, generic_systems, switch_label_pair: list) -> dict:
    """
    Pull the single vlan cts for the switch pair
    """

    logging.warning(f"pull_interface_vlan_table {the_bp.label=} {switch_label_pair=}")
    interface_vlan_nodes = the_bp.query(interface_vlan_query)
    logging.debug(f"BP:{the_bp.label} {len(interface_vlan_nodes)=}")
    # why so many (3172) entries?

    for nodes in interface_vlan_nodes:
        # logging.warning(f"{nodes=}")
        the_interface_id = nodes[CtEnum.INTERFACE_NODE]['id']
        vn_id = int(nodes[CtEnum.VN_NODE]['vn_id'])
        tagged = 'vlan_tagged' in nodes[CtEnum.SINGLE_VLAN_NODE]['attributes']
        the_ae = [x.group_links[the_interface_id] for k, x in generic_systems.generic_systems.items() if the_interface_id in x.group_links ][0]
        # logging.warning(f"{the_ae=}")
        # breakpoint()
        if tagged:
            the_ae.old_tagged_vlans[vn_id] = CtData(vn_id=vn_id)
        else:
            the_ae.old_untagged_vlan[vn_id] = CtData(vn_id=vn_id)

    return {}

def refresh_ct_table(the_bp, generic_systems, switch_label_pair: list):
    """
    Refresh the single vlan cts for the switch pair
    """
    # get the data from main blueprint
    interface_vlan_nodes = the_bp.query(interface_vlan_query)

    for nodes in interface_vlan_nodes:
        # logging.warning(f"{nodes=}")
        ct_node_id = nodes[CtEnum.CT_NODE]['id']
        the_interface_id = nodes[CtEnum.INTERFACE_NODE]['id']
        vn_id = int(nodes[CtEnum.VN_NODE]['vn_id'])
        tagged = 'vlan_tagged' in nodes[CtEnum.SINGLE_VLAN_NODE]['attributes']
        for tbody_id, gs in generic_systems.generic_systems.items():
            for old_ae_id, ae_data in gs.group_links.items():
                if ae_data.new_ae_id == the_interface_id:
                    # breakpoint()
                    if tagged:
                        ae_data.old_tagged_vlans[vn_id].new_ct_id = ct_node_id
                    else:
                        ae_data.old_untagged_vlan[vn_id].new_ct_id = ct_node_id
                    break
            break
    return {}
