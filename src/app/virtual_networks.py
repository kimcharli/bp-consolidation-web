
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from .access_switches import DataStateEnum

class _BoundTo(BaseModel):
    # label: str  # label for the RG or system. TODO: omit?
    vlan_id: int  # like '1323'
class _VirtualNetwork(BaseModel):
    vn_id: int
    vn_node_id: str = ''
    vn_name: str = ''
    rz_name: str = ''
    vn_type: str = ''
    reserved_vlan_id: str = ''
    dhcp_service: str = ''
    ipv4_enabled: str = ''
    ipv6_enabled: str = ''
    virtual_gateway_ipv4_enabled: str = ''
    virtual_gateway_ipv6_enabled: str = ''
    ipv4_subnet: str = ''
    ipv6_subnet: str = ''
    virtual_gateway_ipv4: str = ''
    virtual_gateway_ipv6: str = ''
    bound_to: Dict[str, _BoundTo] = {}

    @property
    def button_vn_id(self):
        return f"vn-{self.vn_id}"

    def html_element(self, this_bound_to):
        content = _VirtualNetworkResponse(id=self.button_vn_id, value=str(self.vn_id))
        # content.attrs.append(_Attribute(attr='id', value=self.vn_id))
        content.attrs.append(_Attribute(attr='class', value=DataStateEnum.DATA_STATE))
        if this_bound_to in self.bound_to:
            content.attrs.append(_Attribute(attr=DataStateEnum.DATA_STATE, value=DataStateEnum.DONE))
        else:
            content.attrs.append(_Attribute(attr=DataStateEnum.DATA_STATE, value=DataStateEnum.INIT))
        return content


class _Attribute(BaseModel):
    attr: str
    value: str

class _VirtualNetworkResponse(BaseModel):
    id: str
    attrs: List[_Attribute] = [] 
    value: str

class _VirtualNetworksResponse(BaseModel):
    values: List[_VirtualNetworkResponse] = []
    caption: str = ''


class VirtualNetworks(BaseModel):
    vns: Dict[int, _VirtualNetwork] = {}  # vni: _VirtualNetwork
    main_bp: Any
    tor_bp: Any

    this_bound_to: str = 'atl1tor-r5r15-pair'  # to be updated

    logger: Any = logging.getLogger('VirtualNetworks')


    def update_virtual_networks_data(self):
        # cls['vnis'] = [ x['vn']['vn_id'] for x in tor_bp.query("node('virtual_network', name='vn')") ]        
        for vn_node in self.tor_bp.query("node('virtual_network', name='vn')"):
            vn_id = vn_node['vn']['vn_id']
            self.vns[vn_id] = _VirtualNetwork(vn_id=vn_node['vn']['vn_id'])

        # TODO: take care of non RG case
        for button_id, vn in self.vns.items():
            main_vn_nodes_query = f"""match(
                node('virtual_network', vn_id='{vn.vn_id}', name='vn').in_('member_vns').node('security_zone', name='rz'),
                node(name='vn').out('instantiated_by').node('vn_instance', name='vn_instance')
                    .in_('hosted_vn_instances').node('system', name='switch')
                    .in_('composed_of_systems').node('redundancy_group', name='redundancy_group'),
            )"""
            result = self.main_bp.query(main_vn_nodes_query)
            # self.logger.warning(f"{len(result)=} {result=}")
            if len(result) == 0:
                continue
            # iterate each list
            for nodes in result:
                # self.logger.warning(f"processing {vn.vn_id=}")
                thisvn = nodes['vn']
                vn.vn_node_id = thisvn['id']
                vn.vn_name = thisvn['label']
                vn.rz_name = nodes['rz']['label']
                vn.vn_type = thisvn['vn_type']
                # vn.vn_id = thisvn['vn_id']  # this is the initializer
                vn.reserved_vlan_id = thisvn['reserved_vlan_id']
                vn.dhcp_service = nodes['vn_instance']['dhcp_enabled']
                vn.ipv4_enabled = thisvn['ipv4_enabled']
                vn.ipv6_enabled = thisvn['ipv6_enabled']
                vn.virtual_gateway_ipv4_enabled = thisvn['virtual_gateway_ipv4_enabled']
                vn.virtual_gateway_ipv6_enabled = thisvn['virtual_gateway_ipv6_enabled']
                vn.ipv4_subnet = thisvn['ipv4_subnet']
                vn.ipv6_subnet = thisvn['ipv6_subnet']
                vn.virtual_gateway_ipv4 = thisvn['virtual_gateway_ipv4']
                vn.virtual_gateway_ipv6 = thisvn['virtual_gateway_ipv6']
                vn.bound_to.setdefault(nodes['redundancy_group']['label'], _BoundTo(vlan_id=nodes['vn_instance']['vlan_id']))

        response = _VirtualNetworksResponse()
        response.values = [v.html_element(self.this_bound_to) for k, v in self.vns.items()]
        response.caption = f"Virtual Networks ({len(self.vns)})"
        return response

    def migrate_virtual_networks(self):

        response = _VirtualNetworksResponse()
        response.values = [v.html_element(self.this_bound_to) for k, v in self.vns.items()]
        response.caption = f"Virtual Networks ({len(self.vns)})"
        return response
