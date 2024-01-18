
from pydantic import BaseModel
from typing import List
import logging

class _VirtualNetwork(BaseModel):
    vni: int
    in_main_switch: bool = False  # 

    @property
    def vn_id(self):
        return f"vn-{self.vni}"

    @property
    def attr_n_value(self):
        content = _VirtualNetworkResponseItems(value=f"vn{self.vni}")
        content.attrs.append(_Attribute(attr='id', value=self.vn_id))
        content.attrs.append(_Attribute(attr='class', value='data-state'))
        content.attrs.append(_Attribute(attr='data-state', value='init'))
        return content

class _Attribute(BaseModel):
    attr: str
    value: str

class _VirtualNetworkResponseItems(BaseModel):
    attrs: List[_Attribute] = [] 
    value: str

class _VirtualNetworkResponse(BaseModel):
    values: List[_VirtualNetworkResponseItems] = []
    caption: str = ''


class VirtualNetworks:
    vns = {}  # vni: _VirtualNetwork

    @classmethod
    def update_virtual_networks_data(cls, main_bp, tor_bp):
        # cls['vnis'] = [ x['vn']['vn_id'] for x in tor_bp.query("node('virtual_network', name='vn')") ]
        for vn in tor_bp.query("node('virtual_network', name='vn')"):
            vni = vn['vn']['vn_id']
            cls.vns[vni] = _VirtualNetwork(vni=vni)
        response = _VirtualNetworkResponse()
        logging.warning(f"update_virtual_networks_data {cls.vns=}")
        response.values = [v.attr_n_value for k, v in cls.vns.items()]
        response.caption = f"Virtual Networks ({len(VirtualNetworks.vns)})"
        return response

