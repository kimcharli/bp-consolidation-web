
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import time

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

    def update(self, nodes):
        thisvn = nodes['vn']
        self.vn_node_id = thisvn['id']
        self.vn_name = thisvn['label']
        self.rz_name = nodes['rz']['label']
        self.vn_type = thisvn['vn_type']
        # self.vn_id = thisvn['vn_id']  # this is the initializer
        self.reserved_vlan_id = thisvn['reserved_vlan_id'] or ''
        self.dhcp_service = nodes['vn_instance']['dhcp_enabled'] and 'yes' or ''
        self.ipv4_enabled = thisvn['ipv4_enabled'] and 'yes' or ''
        self.ipv6_enabled = thisvn['ipv6_enabled'] and 'yes' or ''
        self.virtual_gateway_ipv4_enabled = thisvn['virtual_gateway_ipv4_enabled'] and 'yes' or ''
        self.virtual_gateway_ipv6_enabled = thisvn['virtual_gateway_ipv6_enabled'] and 'yes' or ''
        self.ipv4_subnet = thisvn['ipv4_subnet'] and thisvn['ipv4_subnet'] or ''
        self.ipv6_subnet = thisvn['ipv6_subnet'] and thisvn['ipv6_subnet'] or ''
        self.virtual_gateway_ipv4 = thisvn['virtual_gateway_ipv4'] and thisvn['virtual_gateway_ipv4'] or ''
        self.virtual_gateway_ipv6 = thisvn['virtual_gateway_ipv6'] and thisvn['virtual_gateway_ipv6'] or ''
        self.bound_to.setdefault(nodes['redundancy_group']['label'], _BoundTo(vlan_id=nodes['vn_instance']['vlan_id']))

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
    done: bool = False


class VirtualNetworks(BaseModel):
    vns: Dict[int, _VirtualNetwork] = {}  # vni: _VirtualNetwork
    main_bp: Any
    tor_bp: Any
    bound_to: Dict[str, _BoundTo] = {}

    this_bound_to: str = 'atl1tor-r5r15-pair'  # to be updated

    logger: Any = logging.getLogger('VirtualNetworks')

    def render_all(self):
        response = _VirtualNetworksResponse()
        response.values = [v.html_element(self.this_bound_to) for k, v in self.vns.items()]
        response.caption = f"Virtual Networks ({len(self.vns)})"

        not_done_list = [vn_id for vn_id, vn in self.vns.items() if self.this_bound_to not in vn.bound_to]
        if len(not_done_list) == 0:
            response.done = True
        return response

    def update_virtual_networks_data(self):
        # cls['vnis'] = [ x['vn']['vn_id'] for x in tor_bp.query("node('virtual_network', name='vn')") ]        
        for vn_node in self.tor_bp.query("node('virtual_network', name='vn')"):
            vn_id = vn_node['vn']['vn_id']
            self.vns[vn_id] = _VirtualNetwork(vn_id=vn_node['vn']['vn_id'])

        # # TODO: take care of non RG case
        # do query for all to save time to process
        main_vn_nodes_query = f"""match(
            node('virtual_network', name='vn').in_('member_vns').node('security_zone', name='rz'),
            node(name='vn').out('instantiated_by').node('vn_instance', name='vn_instance')
                .in_('hosted_vn_instances').node('system', name='switch')
                .in_('composed_of_systems').node('redundancy_group', name='redundancy_group'),
        )"""
        result = self.main_bp.query(main_vn_nodes_query)
        for nodes in result:
            thisvn = nodes['vn']
            vn_id = thisvn['vn_id']
            if vn_id not in self.vns:
                # irelevant
                continue
            vn = self.vns[vn_id]
            vn.update(nodes)
            for k, v in vn.bound_to.items():
                if k not in self.bound_to:
                    self.bound_to[k] = v

        return self.render_all()

    def csv_headers(self) -> str:
        cols = ["vn_node_id", "vn_name", "rz_name", "vn_type", "vn_id", "reserved_vlan_id", "dhcp_service",
                "ipv4_enabled", "ipv6_enabled", "virtual_gateway_ipv4_enabled", "virtual_gateway_ipv6_enabled",
                "ipv4_subnet", "ipv6_subnet", "virtual_gateway_ipv4", "virtual_gateway_ipv6"]
        for b in self.bound_to:
            cols.append(f"bound_to_{b}")
        cols.append(self.this_bound_to)
        return ','.join(cols)

    def migrate_virtual_networks(self):
        """
        """
        exported_csv = self.main_bp.get_item("virtual-networks-csv-bulk")
        exported_data = [ [y for y in x.split(',')] for x in exported_csv['csv_bulk'].split('\n')]

        header_line = exported_data[0]
        build_data = [','.join(header_line)]  # put the header
        my_bound_to_column = None
        # find the column for this access pair
        for index, value in enumerate(header_line):
            if f"bound_to_{self.this_bound_to}" == value:
                my_bound_to_column = index
                break
        # breakpoint()
        if my_bound_to_column is None:
            # TODO: 
            self.logger.error(f"{self.this_bound_to} not in exported csv")
            return self.render_all()
        for vn_csv in exported_data[1:]:
            vn_id = vn_csv[4] 
            # this vn_csv is not for this access switch pair
            if vn_id not in self.vns:
                continue
            vn_data = self.vns[vn_id]
            # this vn already in this access switch pair
            if self.this_bound_to in vn_data.bound_to:
                continue
            vn_csv[my_bound_to_column] = 'X'  # mart to add
            build_data.append(','.join(vn_csv))

        if len(build_data) > 1:
            patched = self.main_bp.patch_virtual_networks_csv_bulk('\n'.join(build_data))
            self.logger.warning(f"migrate_virtual_networks {patched=} {patched.content=}")
            task_id = patched.json()['task_id']
            max_wait = 30
            for i in range(max_wait):
                task_state = self.main_bp.get_item(f"tasks/{task_id}")                
                self.logger.warning(f"{task_state['status']=}")
                if task_state['status'] != 'in_progress':
                    break
                self.logger.warning(f"Waiting for the task to finish {i}/{max_wait}")
                time.sleep(3)
            self.logger.warning(f"task succeeded")
        else:
            self.logger.warning("no change")
        
        main_vn_nodes_query = f"""match(
            node('virtual_network', name='vn').in_('member_vns').node('security_zone', name='rz'),
            node(name='vn').out('instantiated_by').node('vn_instance', name='vn_instance')
                .in_('hosted_vn_instances').node('system', name='switch')
                .in_('composed_of_systems').node('redundancy_group', name='redundancy_group'),
        )"""
        result = self.main_bp.query(main_vn_nodes_query)
        for nodes in result:
            thisvn = nodes['vn']
            vn_id = thisvn['vn_id']
            if vn_id not in self.vns:
                # irelevant
                continue
            vn = self.vns[vn_id]
            vn.update(nodes)
            for k, v in vn.bound_to.items():
                if k not in self.bound_to:
                    self.bound_to[k] = v

        return self.render_all()