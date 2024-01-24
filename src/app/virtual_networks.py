
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from .access_switches import DataStateEnum

class _BoundTo(BaseModel):
    label: str
    value: str = ''  # like '1323'
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
    bound_to: List[_BoundTo] = []

    @property
    def button_vn_id(self):
        return f"vn-{self.vn_id}"

    @property
    def attr_n_value(self):        
        content = _VirtualNetworkResponse(id=self.button_vn_id, value=str(self.vn_id))
        # content.attrs.append(_Attribute(attr='id', value=self.vn_id))
        content.attrs.append(_Attribute(attr='class', value=DataStateEnum.DATA_STATE))
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


    def update_virtual_networks_data(self):
        # cls['vnis'] = [ x['vn']['vn_id'] for x in tor_bp.query("node('virtual_network', name='vn')") ]        
        for vn_node in self.tor_bp.query("node('virtual_network', name='vn')"):
            vn_id = vn_node['vn']['vn_id']
            self.vns[vn_id] = _VirtualNetwork(vn_id=vn_node['vn']['vn_id'])

        # main_vn_nodes_query = f"

        # "


        response = _VirtualNetworksResponse()
        # logging.warning(f"update_virtual_networks_data {cls.vns=}")
        response.values = [v.attr_n_value for k, v in self.vns.items()]
        response.caption = f"Virtual Networks ({len(self.vns)})"
        return response

    def migrate_virtual_networks(self):

        pass