import logging
from enum import StrEnum

from ck_apstra_api.apstra_blueprint import CkEnum

from .generic_systems import CtData


class CtEnum(StrEnum):
    INTERFACE_NODE = 'interface'
    CT_NODE = 'batch'
    SINGLE_VLAN_NODE = 'AttachSingleVLAN'
    VN_NODE = 'virtual_network'
    EPAE_NODE = 'ep_application_instance'

def pull_interface_vlan_table(the_bp, generic_systems, switch_label_pair: list) -> dict:
    """
    Pull the single vlan cts for the switch pair

    The return data
    <system_label>:
        <if_name>:
            id: None
            tagged_vlans: []
            untagged_vlan: None
    redundacy_group:
        <ae_id>:
            tagged_vlans: []
            untagged_vlan: None
            member_interfaces:
                <system_label>: [ <member if_name> ]   
    """
    interface_vlan_table = {
        # atl1tor-r5r14a:
        #     xe-0/0/0:
        #         id: <interface id>
        #         tagged_vlans: []
        #         untagged_vlan: None
        CkEnum.REDUNDANCY_GROUP: {
            # <ae_id>:
            #     tagged_vlans: []
            #     untagged_vlan: None
            #     member_interfaces:
            #         <system_label>: [ <member if_name> ]             
        }

    }



    interface_vlan_query = f"""match(
        node('ep_endpoint_policy', policy_type_name='batch', name='{CtEnum.CT_NODE}')
            .in_().node('ep_application_instance', name='{CtEnum.EPAE_NODE}')
            .out('ep_affected_by').node('ep_group')
            .in_('ep_member_of').node(name='{CtEnum.INTERFACE_NODE}'),
        node(name='{CtEnum.EPAE_NODE}')
            .out('ep_nested').node('ep_endpoint_policy', policy_type_name='AttachSingleVLAN', name='{CtEnum.SINGLE_VLAN_NODE}')
            .out('vn_to_attach').node('virtual_network', name='virtual_network'),
    )"""
    stripped_query = interface_vlan_query.replace('\n', '')
    logging.warning(f"pull_interface_vlan_table {the_bp.label=} {switch_label_pair=} {stripped_query=}")
    interface_vlan_nodes = the_bp.query(stripped_query)
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
            the_ae.tagged_vlans[vn_id] = CtData(vn_id=vn_id)
        else:
            the_ae.untagged_vlan[vn_id] = CtData(vn_id=vn_id)

    return interface_vlan_table
