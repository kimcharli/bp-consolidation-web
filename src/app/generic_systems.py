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



class _Memberlink(BaseModel):
    server_intf: Optional[str]
    switch: str
    switch_intf: str

class _GroupLink(BaseModel):
    ae_name: str  # the ae in the tor blueprint
    speed: str
    cts: Optional[List[int]] = []
    tagged_vlans: Optional[List[int]] = []
    untagged_vlan: Optional[int] = None
    new_cts: Optional[List[int]] = []  # the connectivity templates in main blueprint  
    new_ae_name: Optional[str] = None  # the ae in the main blueprint
    links: Optional[List[_Memberlink]] = []

class _GenericSystem(BaseModel):
    # original_label: str
    new_label: str  # the label in the main blueprint (renamed)
    new_id: Optional[str] = None  # the generic system id on main blueprint
    tbody_id: Optional[str] = None  # the id on the tbody element
    group_links: Optional[List[_GroupLink]] = []

    def get_ae(cls, ae_name, speed):
        found_ae = [x for x in cls.group_links if x.ae_name == ae_name]
        if len(found_ae):
            return found_ae[0]
        ae_link = _GroupLink(ae_name=ae_name, speed=speed)
        cls.group_links.append(ae_link)
        return ae_link

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

        class _TR(BaseModel):
            id: str
            value: str
        class _Response(BaseModel):
            values: Optional[List[_TR]] = []
            caption: Optional[str] = None

        # content = {
        #     'values': [],  # target: html-string
        #     'summary': None,  # 
        #     'continue': False,  # more items to update
        #     'caption': None
        # }
        content = _Response()
        index = 0
        gs_count = len(cls.tor_servers)
        for server_label, server_data in cls.tor_servers.items():
            index += 1
            id = f"gs-{server_label}"
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
            content.values.append(_TR(id=id, value=''.join(td_list)))
            # content['values'].append({'id': generic_system_id_on_tbody, 'value': ''.join(td_list)})
        # content['caption'] = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
        content.caption = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
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
        # logging.warning(f"new_label() begin, {tor_name=} {old_label=}")
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
        # logging.warning(f"new_label() returns: {prefix}-{old_label}")
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
            node('system', system_type='server',  name='server')
                .out().node('interface', if_type='ethernet', name='server_intf')
                .out('link').node('link', name='link')
                .in_('link').node('interface', name='switch_intf')
                .in_('hosted_interfaces').node('system', system_type='switch', name='switch'),
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
            # logging.warning(f"pull_server_links() {server_link=}")
            server_label = server_link['server']['label']
            ae_name = server_link['ae']['if_name'] if server_link['ae'] else ''
            speed = server_link['link']['speed']
            switch = server_link['switch']['label']
            switch_intf = server_link['switch_intf']['if_name']
            server_intf = server_link['server_intf']['if_name']

            server_data = get_data_or_default(  # GenericSystem
                data, 
                server_label,
                _GenericSystem(
                    new_label=server_label,
                )
            )
            server_data.get_ae(ae_name, speed).links.append(
                _Memberlink(switch=switch, switch_intf=switch_intf, server_intf=server_intf)
            )

        return data
