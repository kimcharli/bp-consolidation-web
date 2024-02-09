
from typing import List, Dict, Any
from dataclasses import dataclass, field
import logging
import time
import asyncio

from .ck_global import SseEvent, SseEventEnum, SseEventData, global_store, sse_logging

@dataclass
class _BoundTo:
    vlan_id: int  # like '1323'

@dataclass
class _VirtualNetwork:
    vn_id: int
    bound_to: Dict[str, _BoundTo] = None  # the systems (rgs) this vn is bound to 

    @property
    def button_vn_id(self):
        return f"vn-{self.vn_id}"
        

    async def sse_vn(self, this_bound_to):
        """
        send the sse event for this vn. See if this vn is bound to the access switch pair
        """
        sse_data = SseEventData(id=self.button_vn_id, value=str(self.vn_id))
        if this_bound_to in self.bound_to:
            # sse_data = sse_data.done()
            await SseEvent(event=SseEventEnum.UPDATE_VN, data=sse_data.done()).send()            
        else:
            # sse_data = sse_data.init()
            await SseEvent(event=SseEventEnum.UPDATE_VN, data=sse_data.init()).send()            

    async def remove(self):
        await SseEvent(data=SseEventData(id=self.button_vn_id).remove()).send()
        

    def update(self, nodes):
        # logging.warning(f"update {nodes=} {self=}")
        thisvn = nodes['vn']
        self.bound_to.setdefault(nodes['redundancy_group']['label'], _BoundTo(vlan_id=nodes['vn_instance']['vlan_id']))


@dataclass
class VirtualNetworks:
    global_store: Any  # should be given at the time of creation
    vns: Dict[int, _VirtualNetwork] = None  # all the vnis to be in this access pair: _VirtualNetwork
    bound_to: Dict[str, _BoundTo] = None  # bound_to (of all rg in the main bp) 
    this_bound_to: str  = None  # the access switch pair label like 'atl1tor-r5r15-pair'
    # is_all_done: bool = False

    logger: Any = logging.getLogger('VirtualNetworks')

    @property
    def main_bp(self):
        return self.global_store.bp['main_bp']
    
    @property
    def tor_bp(self):
        return self.global_store.bp['tor_bp']

    async def sse_logging(self, text: str):
        await sse_logging(text, self.logger)


    async def render_all(self):
        for vn in self.vns.values():
            await vn.sse_vn(self.this_bound_to)

        await SseEvent(data=SseEventData(id=SseEventEnum.CAPTION_VN, 
                            value=f'Virtual Networks ({len(self.vns)})')).send()
        not_done_list = [vn for vn in self.vns.values() if self.this_bound_to not in vn.bound_to]
        await self.global_store.migration_status.set_vn_done(len(not_done_list) == 0)

        return

    async def remove(self):
        for vn in self.vns.values():
            await vn.remove()
        await SseEvent(data=SseEventData(id=SseEventEnum.CAPTION_VN, 
                            value=f'Virtual Networks (0)')).send()
        await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).init()).send(), 
        await self.global_store.migration_status.set_vn_done(False)
        await asyncio.sleep(1)


    async def sync_tor_vns(self):
        # cls['vnis'] = [ x['vn']['vn_id'] for x in tor_bp.query("node('virtual_network', name='vn')") ]        
        for vn_node in self.tor_bp.query("node('virtual_network', name='vn')"):
            vn_id = vn_node['vn']['vn_id']
            self.vns[vn_id] = _VirtualNetwork(vn_id=vn_node['vn']['vn_id'], bound_to={})

        # # TODO: take care of non RG case
        # do query for all to save time to process
        # vn to switch matching of all the main blueprint
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
            vn = self.vns[vn_id]  # _VirtualNetwork
            vn.update(nodes)
            for rg_pair, vlan_id in vn.bound_to.items():
                if rg_pair not in self.bound_to:
                    # logging.warning(f"bound_to {rg_pair=} {vlan_id=} {self.bound_to=} {vn=}")
                    self.bound_to[rg_pair] = vlan_id

        # for vn_id, vn in self.vns.items():
        #     await vn.sse_vn(self.this_bound_to)

        # await self.queue_render()
        return await self.render_all()
        # return

    def csv_headers(self) -> str:
        cols = ["vn_node_id", "vn_name", "rz_name", "vn_type", "vn_id", "reserved_vlan_id", "dhcp_service",
                "ipv4_enabled", "ipv6_enabled", "virtual_gateway_ipv4_enabled", "virtual_gateway_ipv6_enabled",
                "ipv4_subnet", "ipv6_subnet", "virtual_gateway_ipv4", "virtual_gateway_ipv6"]
        for b in self.bound_to:
            cols.append(f"bound_to_{b}")
        cols.append(self.this_bound_to)
        return ','.join(cols)

    async def migrate_virtual_networks(self):
        """
        """

        # await SseEvent(event=SseEventEnum.BUTTION_DISABLE, data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).disable()).send()

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
            await self.sse_logging(f"{self.this_bound_to} not in exported csv")
            return await self.render_all(self.bound_to)
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
            # TODO: WARNING
            await self.sse_logging(f"migrate_virtual_networks {patched=} {patched.content=}")
            task_id = patched.json()['task_id']
            max_wait = 30
            for i in range(max_wait):
                task_state = self.main_bp.get_item(f"tasks/{task_id}")   
                # TODO: WARNING  
                await self.sse_logging(f"{task_state['status']=}")
                if task_state['status'] != 'in_progress':
                    break
                # TODO: WARNING
                await self.sse_logging(f"Waiting for the task to finish {i}/{max_wait}")
                time.sleep(3)  # should block and wait. should NOT use asyncio.sleep
            # TODO: WARNING
            await self.sse_logging(f"task succeeded")
        else:
            # TODO: WARNING
            await self.sse_logging("no change")
        
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

        # await self.queue_render()
        await self.render_all()

        await global_store.migration_status.set_vn_done(True)
        # await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).done()).send()
        # await SseEvent(event=SseEventEnum.BUTTION_DISABLE, data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_CT).enable()).send()

        return {}
