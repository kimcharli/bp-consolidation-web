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



    # for nodes in interface_vlan_nodes:
    #     if nodes[CkEnum.MEMBER_INTERFACE]:
    #         # INTERFACE_NODE is EVPN
    #         evpn_id = nodes[INTERFACE_NODE]['id']
    #         system_label = nodes[CkEnum.MEMBER_SWITCH]['label']
    #         if_name = nodes[CkEnum.MEMBER_INTERFACE]['if_name']
    #         if if_name in ['et-0/0/48', 'et-0/0/49']:
    #             # skip et-0/0/48 and et-0/0/49 which will be taken care of by Apstra
    #             continue
    #         vlan_id = int(nodes[VN_NODE]['vn_id'] )- 100000
    #         is_tagged = 'vlan_tagged' in nodes[SINGLE_VLAN_NODE]['attributes']
    #         if evpn_id not in interface_vlan_table[CkEnum.REDUNDANCY_GROUP]:
    #             interface_vlan_table[CkEnum.REDUNDANCY_GROUP][evpn_id] = {
    #                 CkEnum.TAGGED_VLANS: [],
    #                 CkEnum.UNTAGGED_VLAN: None,
    #                 CkEnum.MEMBER_INTERFACE: {}
    #             }
    #         this_evpn_interface_data = interface_vlan_table[CkEnum.REDUNDANCY_GROUP][evpn_id]
    #         if system_label not in this_evpn_interface_data[CkEnum.MEMBER_INTERFACE]:
    #             this_evpn_interface_data[CkEnum.MEMBER_INTERFACE][system_label] = []
    #         if if_name not in this_evpn_interface_data[CkEnum.MEMBER_INTERFACE][system_label]:
    #             this_evpn_interface_data[CkEnum.MEMBER_INTERFACE][system_label].append(if_name)
    #         if is_tagged:
    #             # add vlan_id if not already in the list
    #             if vlan_id not in this_evpn_interface_data[CkEnum.TAGGED_VLANS]:
    #                 this_evpn_interface_data[CkEnum.TAGGED_VLANS].append(vlan_id)
    #         else:
    #             this_evpn_interface_data[CkEnum.UNTAGGED_VLAN] = vlan_id
    #     else:
    #         system_label = nodes['switch']['label']
    #         if_name = nodes['interface']['if_name']
    #         vlan_id = int(nodes['virtual_network']['vn_id'] )- 100000
    #         is_tagged = 'vlan_tagged' in nodes[SINGLE_VLAN_NODE]['attributes']
    #         if system_label not in interface_vlan_table:
    #             interface_vlan_table[system_label] = {}
    #         if if_name not in interface_vlan_table[system_label]:
    #             interface_vlan_table[system_label][if_name] = {
    #                 'id': nodes['interface']['id'],
    #                 CkEnum.TAGGED_VLANS: [],
    #                 CkEnum.UNTAGGED_VLAN: None,
    #             }
    #         this_interface_data = interface_vlan_table[system_label][if_name]
    #         if is_tagged:
    #             this_interface_data[CkEnum.TAGGED_VLANS].append(vlan_id)
    #         else:
    #             this_interface_data[CkEnum.UNTAGGED_VLAN] = vlan_id

    # summary = [f"{x}:{len(interface_vlan_table[x])}" for x in interface_vlan_table.keys()]
    # logging.debug(f"BP:{the_bp.label} {summary=}")

    return interface_vlan_table
