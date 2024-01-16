from pydantic import BaseModel
from typing import Optional, List
import logging

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

    @property
    def tr(self) -> str:
        trs = [
            f'<td data-cell="server_intf" class="data-state" data-state="init">{self.server_intf}</td>',
            f'<td data-cell="switch" class="data-state" data-state="init">{self.switch}</td>',
            f'<td data-cell="switch_intf" class="data-state" data-state="init">{self.switch_intf}</td>',
        ]
        return ''.join(trs)


class _GroupLink(BaseModel):
    ae_name: str  # the ae in the tor blueprint
    speed: str
    cts: Optional[List[int]] = []
    tagged_vlans: Optional[List[int]] = []
    untagged_vlan: Optional[int] = None
    new_cts: Optional[List[int]] = []  # the connectivity templates in main blueprint  
    new_ae_name: Optional[str] = None  # the ae in the main blueprint
    links: Optional[List[_Memberlink]] = []

    @property
    def rowspan(self):
        return len(self.links)

    @property
    def tr(self) -> list:
        row0_head = ''.join([
            f'<td rowspan={self.rowspan} data-cell="ae" class="data-state ae" data-state="init">{self.ae_name}</td>',
            f'<td rowspan={self.rowspan} data-cell="cts" class="data-state cts" data-state="init">{self.cts}</td>',
            f'<td rowspan={self.rowspan} data-cell="speed" class="data-state speed" data-state="init">{self.speed}</td>',
        ])
        trs = []
        for index, link in enumerate(self.links):
            if index == 0:
                trs.append(row0_head + link.tr)
            else:
                trs.append(link.tr)
        return trs


class _GenericSystem(BaseModel):
    label: str  # the label in the tor blueprint
    new_label: str  # the label in the main blueprint (renamed)
    new_id: Optional[str] = None  # the generic system id on main blueprint
    tbody_id: Optional[str] = None  # the id on the tbody element
    group_links: Optional[List[_GroupLink]] = []

    def get_ae(self, ae_name, speed):
        found_ae = [x for x in self.group_links if x.ae_name == ae_name]
        if len(found_ae):
            return found_ae[0]
        ae_link = _GroupLink(ae_name=ae_name, speed=speed)
        self.group_links.append(ae_link)
        return ae_link

    @property
    def rowspan(self):
        return sum([x.rowspan for x in self.group_links])

    def get_tbody(self, index) -> str:
        """
        Return the tbody innerHTML
        """
        row0_head = ''.join([
            f'<td rowspan={self.rowspan}>{index}</td>'
            f'<td rowspan={self.rowspan} data-cell="label" class="system-label">{self.label}</td>',
            f'<td rowspan={self.rowspan} data-cell="new_label" class="data-state system-label" data-state="init">{self.new_label}</td>',
        ])
        tbody_lines = []
        for ae_link in self.group_links:
            for links in ae_link.tr:
                if len(tbody_lines):
                    tbody_lines.append(f'<tr>{links}</tr>')
                else:                    
                    tbody_lines.append(f'<tr>{row0_head}{links}</tr>')
        return ''.join(tbody_lines)

    def migrate(self, main_bp) -> str:
        """
        """
        if self.new_id:
            return self.new_id
        


class GenericSystems:
    tor_servers = {}  # <server_label>: { GenericSystem }
    main_servers = {}
    tor_ae1 = None
    leaf_gs = {'label': None, 'intfs': ['']*4}
    tor_gs = None  # {'label': <>, 'id': None, 'ae_id': None},  # id and ae_id of main_bp

    @classmethod
    def update_generic_systems_table(cls) -> dict:
        """
        Called by main.py
        Build tor_servers from tor_blueprint and return the data 
        """

        class _TBody(BaseModel):
            id: str
            value: str
        class _Response(BaseModel):
            values: Optional[List[_TBody]] = []
            caption: Optional[str] = None

        content = _Response()
        index = 0
        gs_count = len(cls.tor_servers)
        for server_label, server_data in cls.tor_servers.items():
            index += 1
            id = f"gs-{server_label}"
            content.values.append(_TBody(id=id, value=server_data.get_tbody(index)))
        # content['caption'] = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
        content.caption = f"Generic Systems (0/{gs_count}) servers, (0/0) links, (0/0) interfaces"
        return content

    @classmethod
    def migrate_generic_systems(cls) -> dict:
        """
        """


    @classmethod
    def pull_generic_systems(cls, main_bp, tor_bp, tor_gs, access_switches):
        cls.tor_gs = tor_gs
        cls.tor_servers = cls.pull_server_links(tor_bp)


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
    def new_label(cls, old_label) -> str:
        """
        return new label from old label
        """
        # logging.warning(f"new_label() begin, {tor_name=} {old_label=}")
        # the maximum length is 32. Prefix 'r5r14-'
        old_patterns = ['_atl_rack_1_000_', '_atl_rack_1_001_', '_atl_rack_5120_001_']
        # get the prefix from tor_name
        prefix = cls.tor_gs['label'][len('atl1tor-'):]
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
                    label = server_label,
                    new_label = cls.new_label(server_label),
                )
            )
            server_data.get_ae(ae_name, speed).links.append(
                _Memberlink(switch=switch, switch_intf=switch_intf, server_intf=server_intf)
            )

        return data
