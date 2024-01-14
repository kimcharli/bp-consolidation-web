from pydantic import BaseModel
from typing import Optional, List
import logging
# from .model.ck_global import GlobalStore, ServerItem, BlueprintItem



                # group_links: [
                #     {
                #         ae_name: aeN or ''
                #         speed:,
                #         CkEnum.TAGGED_VLANS: [],
                #         CkEnum.UNTAGGED_VLAN:,
                #         links: [ server_intf:, switch:, switch_intf:]
                #     }
                # ]

def get_data_or_default(data, label, new_value):
    """
    Return the member data. Or set it to new value
    """
    if hasattr(data, label):
        # class instance
        if not getattr(data, label):
            setattr(data, label, new_value)
        return getattr(data, label)
    # no class. dict
    if label not in data:
        data[label] = new_value    
    return data[label]



class Memberlink(BaseModel):
    server_intf: Optional[str]
    switch: str
    switch_intf: str

class GroupLink(BaseModel):
    ae_name: str
    speed: str
    cts: Optional[str] = '0/0'
    tagged_vlans: Optional[List[int]] = []
    untagged_vlan: Optional[int] = None
    links: List[Memberlink]

class GenericSystem(BaseModel):
    # original_label: str
    new_label: str
    # gs_id: str
    group_links: List[GroupLink]


class GenericSystems:
    tor_servers = {}  # <server_label>: { GenericSystem }
    main_servers = {}
    tor_ae1 = None
    leaf_gs = {'label': None, 'intfs': ['']*4}
    tor_gs = None  # {'label': <>, 'id': None, 'ae_id': None},  # id and ae_id of main_bp


    @classmethod
    def get_generic_systems(cls) -> dict:
        """
        """
        content = {
            'targets': [],  # target: html-string
            'summary': None,  # 
            'continue': False,  # more items to update
        }
        index = 0
        gs_count = len(cls.tor_servers)
        for server_label, server_data in cls.tor_servers.items():
            index += 1
            generic_system_id_on_tr = f"gs-tr-{server_label}"
            td_list = [ 
                f"<td data-cell=\"index\">{index}</td>",
                f"<td data-cell=\"label\" class=\"old-label\">{server_label}</td>",
                f"<td data-cell=\"new_label\" class=\"data-state new-label\" data-state=\"init\">{server_data.new_label}</td>",
                f"<td data-cell=\"ae\" class=\"data-state ae\" >{server_data.group_links[0].ae_name}</td>",
                f"<td data-cell=\"cts\" class=\"data-state cts\">{server_data.group_links[0].cts}</td>",
                f"<td data-cell=\"speed\" class=\"data-state speed\">{server_data.group_links[0].speed}</td>",
                f"<td data-cell=\"server_intf\" class=\"data-state\" data-state=\"init\">{server_data.group_links[0].links[0].server_intf}</td>",
                f"<td data-cell=\"switch\" lass=\"data-state\" data-state=\"init\">{server_data.group_links[0].links[0].switch}</td>",
                f"<td data-cell=\"switch_intf\" lass=\"data-state\" data-state=\"init\">{server_data.group_links[0].links[0].switch_intf}</td>",
                ]
            content['targets'].append({'target': 'generic-systems-table', 'value': ''.join(td_list)})
        content['targets'].append({'target': 'gs-captiion', 'value': f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"})
        return content


    @classmethod
    def pull_generic_systems(cls, main_bp, tor_bp, tor_gs, access_switches):
        cls.tor_gs = tor_gs
        cls.tor_servers = cls.pull_server_links(tor_bp)


        # # set new_label per generic systems
        # for old_label, server_data in cls.tor_gs.items():
        #     server_data['new_label'] = cls.new_label(cls.tor_gs['label'], old_label)                            
        
        # update leaf_gs (the generic system in TOR bp for the leaf)        
        for server_label, server_data in cls.tor_servers.items():
            # y = [x for server_label, server_data in cls.tor_servers.items() if server_data.group_links ]
            for group_link in server_data.group_links:
                if group_link.ae_name:
                    for member_link in group_link.links:
                        if member_link.switch_intf in ['et-0/0/48', 'et-0/0/49']:
                            cls.leaf_gs['label'] = server_label
                            if member_link.switch.endswith(('a', 'c')):  # left tor
                                if member_link.switch_intf == 'et-0/0/48':
                                    cls.leaf_gs['intfs'][0] = 'et-' + member_link.server_intf.split('-')[1]
                                else:
                                    cls.leaf_gs['intfs'][1] = 'et-' + member_link.server_intf.split('-')[1]
                            else:
                                logging.warning(f"pull_generic_systems {cls.leaf_gs=}")
                                if member_link.switch_intf == 'et-0/0/48':
                                    cls.leaf_gs['intfs'][2] = 'et-' + member_link.server_intf.split('-')[1]
                                else:
                                    cls.leaf_gs['intfs'][3] = 'et-' + member_link.server_intf.split('-')[1]

    @classmethod
    def new_label(cls, tor_name, old_label) -> str:
        """
        return new label from old label
        """
        # the maximum length is 32. Prefix 'r5r14-'
        old_patterns = ['_atl_rack_1_000_', '_atl_rack_1_001_', '_atl_rack_5120_001_']
        # get the prefix from tor_name
        prefix = tor_name[len('atl1tor-'):]
        for pattern in old_patterns:
            if old_label.startswith(pattern):
                # replace the string with the prefix
                return f"{prefix}-{old_label[len(pattern):]}"
        # it doesn't starts with the patterns. See if it is too long to prefix
        max_len = 32
        if ( len(old_label) + len(prefix) + 1 ) > max_len:
            # TODO: potential of conflict
            # logging.warning(f"Generic system name {old_label=} is too long to prefix. Keeping original label.")
            return old_label
        # just prefix
        return f"{prefix}-{old_label}"


    @classmethod
    def pull_server_links(cls, the_bp) -> dict:
        """
        return the server and link data
        data = { <server>: GenericSystem }
        """
        data = {}  # <server>: { GenericSystem }
        server_links_query = """
            match(
            node('system', system_type='server',  name='server').out().node('interface', if_type='ethernet', name='server_intf').out('link').node('link', name='link').in_('link').node('interface', name='switch_intf').in_('hosted_interfaces').node('system', system_type='switch', name='switch'),
            optional(
                node(name='switch_intf').in_().node('interface', name='ae')
                ),
            optional(
                node(name='ae').in_().node('interface', name='evpn')
                )
            )
            """
        servers_link_nodes = the_bp.query(server_links_query, multiline=True)

        for server_link in servers_link_nodes:
            logging.warning(f"pull_server_links() {server_link=}")
            server_label = server_link['server']['label']
            ae_name = server_link['ae']['if_name'] if server_link['ae'] else ''

            #  every server_link will add a link_data
            link_data = Memberlink(
                switch=server_link['switch']['label'],
                switch_intf=server_link['switch_intf']['if_name'],
                server_intf=server_link['server_intf']['if_name']
            )
            group_link = GroupLink(
                ae_name=ae_name, 
                speed=server_link['link']['speed'], 
                # tagged_vlans=[], 
                # untagged_vlan=None, 
                links=[link_data]
            )
            server_data = get_data_or_default(  # GenericSystem
                data, 
                server_label,
                GenericSystem(
                    new_label=cls.new_label(cls.tor_gs['label'], server_label),
                    group_links=[group_link]
                )
            )

            if ae_name:
                group_links = [x for x in data[server_label].group_links if x.ae_name == ae_name]
                if group_links:
                    group_links[0].links.append(link_data)
                else:                    
                    data[server_label] = server_data
            else:
                data[server_label] = server_data

            # server_data = get_data_or_default(  # GenericSystem
            #     data, 
            #     server_label,
            #     GenericSystem(
            #         new_label=cls.new_label(cls.tor_gs['label'], server_label),
            #         group_links=[]
            #     )
            # )
            # if server_label not in data:
            #     data[server_label] = GenericSystem(new_label=cls.new_label(cls.tor_gs['label'], server_label), group_links=[])  # <link_id>: {}
            # server_data = data[server_label]            
            # logging.warning(f"pull_server_links() test1: {dict(server_data)=}")


            # if ae_name:
            #     # breakpoint()
            #     ae_data = [x for x in server_data.# The `group_links` attribute is a list of
            #     # `GroupLink` objects. Each `GroupLink` object
            #     # represents a group link configuration for a
            #     # specific server. It contains information such as
            #     # the AE (Aggregate Ethernet) name, speed, tagged
            #     # VLANs, untagged VLAN, and a list of member links.
            #     # The member links are represented by `Memberlink`
            #     # objects, which contain the details of the server
            #     # interface, switch, and switch interface for each
            #     # member link.
            #     group_links if x and x.ae_name == ae_name]
            #     if len(ae_data) == 0:
            #         server_data.group_links.append(GroupLink(
            #             ae_name=ae_name, 
            #             speed=server_link['link']['speed'], 
            #             tagged_vlans=[], 
            #             untagged_vlan=None, 
            #             links=[link_data])
            #         )
            #         # ae_data = [x for x in server_data.group_links if x.ae_name == ae_name]
            #     # link_data = Memberlink(
            #     #     switch=server_link['switch']['label'],
            #     #     switch_intf=server_link['switch_intf']['if_name'],
            #     #     server_intf=server_link['server_intf']['if_name']
            #     #     )
            #     # link_data['switch'] = server_link['switch']['label']
            #     # link_data['switch_intf'] = server_link['switch-intf']['if_name']
            #     # link_data['server_intf'] = server_link['server-intf']['if_name']            
            #     server_data.group_links.links.append(link_data)
            # else:
            #     # # breakpoint()
            #     # ae_data = GroupLink(
            #     #     ae_name='', 
            #     #     speed=server_link['link']['speed'], 
            #     #     tagged_vlans=[], 
            #     #     untagged_vlan=None,
            #     #     link_data = Memberlink(
            #     #         switch=server_link['switch']['label'],
            #     #         switch_intf=server_link['switch-intf']['if_name'],
            #     #         server_intf=server_link['server-intf']['if_name']
            #     #     )
            #     # )
            #     # #     ae_data.links.append(link_data)
            #     # # link_data = {}
            #     # # link_data['switch'] = server_link['switch']['label']
            #     # # link_data['switch_intf'] = server_link['switch-intf']['if_name']
            #     # # link_data['server_intf'] = server_link['server-intf']['if_name']            
            #     # # ae_data['links'].append(link_data)
            #     # server_data.group_links[ae_data]
            #     # breakpoint()


            #     server_data.group_links = GroupLink(
            #         ae_name=ae_name, 
            #         speed=server_link['link']['speed'], 
            #         tagged_vlans=[], 
            #         untagged_vlan=None, 
            #         links = [ link_data ]
            #         # links=Memberlink(
            #         #     switch=server_link['switch']['label'],
            #         #     switch_intf=server_link['switch_intf']['if_name'],
            #         #     server_intf=server_link['server_intf']['if_name']
            #         # )
            #     )
        return data
