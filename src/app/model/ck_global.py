import logging
from typing import Optional
from pydantic import BaseModel, field_validator

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint, CkEnum

class ServerItem(BaseModel):
    id: Optional[int] = None
    host: str
    port: int
    username: str
    password: str
    main_bp_label: Optional[str] = None
    tor_bp_label: Optional[str] = None

    @field_validator('id', 'port', mode='before')
    def convert_str_to_int(cls, value) -> int:
        return int(value)

class BlueprintItem(BaseModel):    
    label: str
    role: str

class EnvIni:
    def __init__(self, data = None):
        self.logger = logging.getLogger(f"EnvIni __init__() {data}")
        if data:
            self.host = data.host
            self.port = data.port
            self.username = data.username
            self.password = data.password
            self.main_bp_label = data.main_bp_label
            self.tor_bp_label = data.tor_bp_label
        else:
            self.clear()
            self.update()
    
    def clear(self):
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.main_bp_label = None
        self.tor_bp_label = None

    def get_url(self) -> str:
        if not self.host or not self.port:
            self.logger.warning(f"get_url() {self.host=} {self.port=}")
            return
        return f"https://{self.host}:{self.port}"

    def update(self, file_content=None) -> dict:
        """
        Update the environment variables from the file_content, and return the updated dict.
        """
        # self.logger.warning(f"update(): before update: {self.__dict__}, {file_content=}")
        self.clear()
        # self.logger.warning(f"update(): cleared: {self.__dict__}, {file_content=}")
        lines = file_content.decode('utf-8').splitlines() if file_content else []
        for line in lines:
            name_value = line.split("=")
            if len(name_value) != 2:
                self.logger.warning(f"update(): invalid line: {line}")
                continue
            if name_value[0] == "apstra_server_host":
                self.host = name_value[1]
            elif name_value[0] == "apstra_server_port":
                self.port = int(name_value[1])
            elif name_value[0] == "apstra_server_username":
                self.username = name_value[1]
            elif name_value[0] == "apstra_server_password":
                self.password = name_value[1]
            elif name_value[0] == "main_bp":
                self.main_bp_label = name_value[1]
            elif name_value[0] == "tor_bp":
                self.tor_bp_label = name_value[1]
            else:
                self.logger.warning(f"update(): invalid name: {name_value}")        
        # self.logger.warning(f"update(): after update: {self.__dict__}")
        return_content = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "main_bp_label": self.main_bp_label,
            "tor_bp_label": self.tor_bp_label,
        }
        return return_content

class GlobalStore:
    apstra_server = None  #  ApstaServer
    bp = {}  # main_bp, tor_bp
    # main_bp = None  # ApstaBlueprint
    # tor_bp = None  # ApstaBlueprint
    tor_data = {}  # 

    env_ini = EnvIni()
    
    logger = logging.getLogger("GlobalStore")
    data = {
    }

    @classmethod
    def get_blueprints(cls):
        cls.logger.warning(f"get_blueprints(): {cls.main_bp=} {cls.tor_bp=}")
        return [cls.main_bp, cls.tor_bp]

    @classmethod
    def set_data(cls, key, value):
        cls.logger.warning(f"set_data(): {key=} {value=}")
        cls.data[key] = value

    @classmethod
    def get_data(cls, key):
        cls.logger.warning(f"get_data(): {key=} {cls.data.get(key)=}")
        return cls.data.get(key)

    @classmethod
    def update_env_ini(cls, data):        
        cls.logger.warning(f"update_env_ini(): {data=}")
        cls.env_ini = EnvIni(data)
        return

    @classmethod
    def login_server(cls, server: ServerItem) -> dict:
        cls.logger.warning(f"login_server() {server=}")
        cls.apstra_server = CkApstraSession(server.host, int(server.port), server.username, server.password)
        cls.logger.warning(f"login_server(): {cls.apstra_server.__dict__}")
        return { "version": cls.apstra_server.version }

    @classmethod
    def logout_server(cls):
        cls.logout_blueprint()
        if cls.apstra_server:
            cls.apstra_server.logout() 
        cls.logger.warning(f"logout_server()")
        cls.apstra_server = None
        return

    @classmethod
    def login_blueprint(cls, blueprint: BlueprintItem):
        cls.logger.warning(f"login_blueprint {blueprint=} {cls.apstra_server=}")
        role = blueprint.role
        label = blueprint.label
        bp = CkApstraBlueprint(cls.apstra_server, label)
        cls.bp[role] = bp
        cls.logger.warning(f"login_blueprint {bp=}")
        id = bp.id
        url = f"{cls.env_ini.get_url()}/#/blueprints/{id}/staged"
        data = { "id": id, "url": url, "label": label }
        cls.logger.warning(f"login_blueprint() return: {data}")
        return data

    @classmethod
    def logout_blueprint(cls):
        cls.bp = {}
        return


    @classmethod
    def pull_tor_bp_data(cls):
        data = {
            'switches': [],  # the tor switches
            'leaf_switches': {},  # the leaf switches <leaf1,2>: { label:, id:, , links: [{ switch_intf:, server_intf}]}
            'tor_name': None,  # coming from switch name
            'leaf_gs': {'label': None, 'intfs': [None] * 4},  # label:, intfs[a-48, a-49, b-48, b-49] - the generic system info for the leaf
            'peer_link': {},  # <id>: { speed: 100G, system: { <label> : [ <intf> ] } }
            'servers': {},  # <server>: { links: {} }
            'vnis': [],            
        }
        cls.logger.warning(f"{cls.bp=}")
        tor_bp = cls.bp['tor_bp']
        main_bp = cls.bp['main_bp']
        peer_link_query = "node('link',role='leaf_leaf',  name='link').in_('link').node('interface', name='intf').in_('hosted_interfaces').node('system', name='switch')"
        peer_link_nodes = tor_bp.query(peer_link_query)
        # cls.logger.warning(f"{peer_link_nodes=}")
        for link in peer_link_nodes:
            link_id = link['link']['id']
            # cls.logger.warning(f"{data=} {link_id=}")
            if link_id not in data['peer_link']:
                data['peer_link'][link_id] = { 'system': {} }
            link_data = data['peer_link'][link_id]
            # cls.logger.warning(f"{data=} {link_data=}")
            link_data['speed'] = link['link']['speed']
            switch_label = link['switch']['label']
            if switch_label not in data['switches']:
                data['switches'].append(switch_label)
            # cls.logger.warning(f"{data=} {switch_label=}")
            if switch_label not in link_data['system']:
                link_data['system'][switch_label] = []
            switch_data = link_data['system'][switch_label]
            switch_intf = link['intf']['if_name']
            switch_data.append(switch_intf)
        cls.logger.warning(f"{data=}")

        #  setup tor_name
        if data['switches'][0].endswith(('a', 'b')):
            data['tor_name'] = data['switches'][0][:-1]
        elif data['switches'][0].endswith(('c', 'd')):
            data['tor_name'] = data['switches'][0][:-1] + 'cd'
        else:
            logging.critical(f"switch names {data['switches']} does not ends with 'a', 'b', 'c', or 'd'!")

        data['servers'] = cls.pull_server_links(tor_bp)

        # set new_label per generic systems
        for old_label, server_data in data['servers'].items():
            server_data['new_label'] = cls.new_label(data['tor_name'], old_label)                            
        
        # update leaf_gs (the generic system in TOR bp for the leaf)
        for server_label, server_data in data['servers'].items():
            for group_link in server_data['group_links']:
                if group_link['ae_name']:
                    for member_link in group_link['links']:
                        if member_link['switch_intf'] in ['et-0/0/48', 'et-0/0/49']:
                            data['leaf_gs']['label'] = server_label
                            if member_link['switch'].endswith(('a', 'c')):  # left tor
                                if member_link['switch_intf'] == 'et-0/0/48':
                                    data['leaf_gs']['intfs'][0] = 'et-' + member_link['server_intf'].split('-')[1]
                                else:
                                    data['leaf_gs']['intfs'][1] = 'et-' + member_link['server_intf'].split('-')[1]
                            else:
                                if member_link['switch_intf'] == 'et-0/0/48':
                                    data['leaf_gs']['intfs'][2] = 'et-' + member_link['server_intf'].split('-')[1]
                                else:
                                    data['leaf_gs']['intfs'][3] = 'et-' + member_link['server_intf'].split('-')[1]


        data['vnis'] = [ x['vn']['vn_id'] for x in tor_bp.query("node('virtual_network', name='vn')") ]

        # get ct assigment and update the servers
        data['ct_table'] = pull_interface_vlan_table(tor_bp, data['switches'])
        for server_label in data['servers']:
            server_data = data['servers'][server_label]
            # breakpoint()
            for ae_data in server_data['group_links']:
                if ae_data['ae_name']:
                    # breakpoint()
                    ae_name = ae_data['ae_name']
                    if ae_name in data['ct_table'][CkEnum.REDUNDANCY_GROUP]:
                        ae_data[CkEnum.TAGGED_VLANS] = data['ct_table'][CkEnum.REDUNDANCY_GROUP][ae_name][CkEnum.TAGGED_VLANS]
                        ae_data[CkEnum.UNTAGGED_VLAN] = data['ct_table'][CkEnum.REDUNDANCY_GROUP][ae_name][CkEnum.UNTAGGED_VLAN]
                else:
                    # none AE, so it will be a single link
                    the_link = ae_data['links'][0]
                    the_switch = the_link['switch']
                    if the_switch in data['ct_table']:
                        the_if_name = the_link['switch_intf']
                        if the_if_name == data['ct_table'][the_switch]:
                            the_if_data = data['ct_table'][the_switch][the_if_name]
                            ae_data[CkEnum.TAGGED_VLANS] = the_if_data[CkEnum.TAGGED_VLANS]
                            ae_data[CkEnum.UNTAGGED_VLAN] = the_if_data[CkEnum.UNTAGGED_VLAN]

        # get leaf information from main BP
        tor_interface_nodes_in_main = main_bp.get_server_interface_nodes(data['tor_name'])
        leaf_switches = [
            # { 'label': None, 'id': None, 'links': []},
            # { 'label': None, 'id': None, 'links': []},
        ]
        leaf_temp = {
            # 'label': { 'label': None, 'id': None, 'links': []},
            # 'label': { 'label': None, 'id': None, 'links': []},
        }
        for member_intf_set in tor_interface_nodes_in_main:
            leaf_label = member_intf_set[CkEnum.MEMBER_SWITCH]['label']
            if leaf_label not in leaf_temp:
                leaf_temp[leaf_label] = {
                    'label': leaf_label, 
                    'id': member_intf_set[CkEnum.MEMBER_SWITCH]['id'], 
                    'links': []}
            leaf_data = leaf_temp[leaf_label]
            leaf_data['links'].append({
                'switch_intf': member_intf_set[CkEnum.MEMBER_INTERFACE]['if_name'],
                'server_intf': member_intf_set[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name'],
                })
        data['leaf_switches'] = sorted(leaf_temp.items(), key=lambda item: item[0])

        data['tor_interface_nodes_in_main'] = tor_interface_nodes_in_main


        cls.tor_data = data
        return data

    
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
            logging.warning(f"Generic system name {old_label=} is too long to prefix. Keeping original label.")
            return old_label
        # just prefix
        return f"{prefix}-{old_label}"


    @classmethod
    def pull_server_links(cls, tor_bp) -> dict:
        """
        return the server and link data
        data = {
            <server>:
                new_label,
                group_links: [
                    {
                        ae_name: aeN or ''
                        speed:,
                        CkEnum.TAGGED_VLANS: [],
                        CkEnum.UNTAGGED_VLAN:,
                        links: [ server_intf:, switch:, switch_intf:]
                    }
                ]
        }
        """
        data = {}  # <server>: { links: {} }
        server_links_query = """
            match(
            node('system', system_type='server',  name='server').out().node('interface', if_type='ethernet', name='server-intf').out('link').node('link', name='link').in_('link').node('interface', name='switch-intf').in_('hosted_interfaces').node('system', system_type='switch', name='switch'),
            optional(
                node(name='switch-intf').in_().node('interface', name='ae')
                ),
            optional(
                node(name='ae').in_().node('interface', name='evpn')
                )
            )
            """
        servers_link_nodes = tor_bp.query(server_links_query, multiline=True)
        for server_link in servers_link_nodes:
            server_label = server_link['server']['label']
            if server_label not in data:
                data[server_label] = {'new_label': None, 'group_links': []}  # <link_id>: {}
            server_data = data[server_label]            
            ae_name = server_link['ae']['if_name'] if server_link['ae'] else ''
            # logging.warning(f"pull_server_links() test1: {dict(server_data)=}")
            if ae_name:
                # breakpoint()
                ae_data = [x for x in server_data['group_links'] if x['ae_name'] == ae_name]
                if len(ae_data) == 0:
                    server_data['group_links'].append({'ae_name': ae_name, 'speed': server_link['link']['speed'], CkEnum.TAGGED_VLANS: [], CkEnum.UNTAGGED_VLAN: None, 'links': []})  # speed, CTs, member_links
                    ae_data = [x for x in server_data['group_links'] if x['ae_name'] == ae_name]
                link_data = {}
                link_data['switch'] = server_link['switch']['label']
                link_data['switch_intf'] = server_link['switch-intf']['if_name']
                link_data['server_intf'] = server_link['server-intf']['if_name']            
                ae_data[0]['links'].append(link_data)
            else:
                # breakpoint()
                ae_data = { 'ae_name': '', 'speed': server_link['link']['speed'], CkEnum.TAGGED_VLANS: [], CkEnum.UNTAGGED_VLAN: None, 'links': []}
                link_data = {}
                link_data['switch'] = server_link['switch']['label']
                link_data['switch_intf'] = server_link['switch-intf']['if_name']
                link_data['server_intf'] = server_link['server-intf']['if_name']            
                ae_data['links'].append(link_data)
                server_data['group_links'].append(ae_data)
                

        return data


def pull_interface_vlan_table(the_bp, switch_label_pair: list) -> dict:
    """
    Pull the single vlan cts for the switch pair

    The return data
    <system_label>:
        <if_name>:
            CkEnum.TAGGED_VLANS: []
            CkEnum.UNTAGGED_VLAN: None
    redundancy_group:
        <ae_id>:
            CkEnum.TAGGED_VLANS: []
            CkEnum.UNTAGGED_VLAN: None
    """
    interface_vlan_table = {
        CkEnum.REDUNDANCY_GROUP: {
        }

    }

    INTERFACE_NODE = 'interface'
    CT_NODE = 'batch'
    SINGLE_VLAN_NODE = 'AttachSingleVLAN'
    VN_NODE = 'virtual_network'

    interface_vlan_query = f"""
        match(
            node('ep_endpoint_policy', policy_type_name='batch', name='{CT_NODE}')
                .in_().node('ep_application_instance', name='ep_application_instance')
                .out('ep_affected_by').node('ep_group')
                .in_('ep_member_of').node(name='{INTERFACE_NODE}'),
            node(name='ep_application_instance')
                .out('ep_nested').node('ep_endpoint_policy', policy_type_name='AttachSingleVLAN', name='{SINGLE_VLAN_NODE}')
                .out('vn_to_attach').node('{VN_NODE}', name='virtual_network'),
            optional(
                node(name='{INTERFACE_NODE}')
                .out('composed_of').node('interface', name='ae')
                ),
            optional(
                node(name='{INTERFACE_NODE}')
                .in_('hosted_interfaces').node('system', system_type='switch', label=is_in({switch_label_pair}), name='switch')
                )            
        )
    """

    interface_vlan_nodes = the_bp.query(interface_vlan_query, multiline=True)
    logging.debug(f"BP:{the_bp.label} {len(interface_vlan_nodes)=}")

    for nodes in interface_vlan_nodes:
        if nodes['ae']:
            # INTERFACE_NODE is AE
            ae_name = nodes['ae']['if_name']
            if ae_name not in interface_vlan_table[CkEnum.REDUNDANCY_GROUP]:
                interface_vlan_table[CkEnum.REDUNDANCY_GROUP][ae_name] = {
                    CkEnum.TAGGED_VLANS: [],
                    CkEnum.UNTAGGED_VLAN: None,
                }
            this_evpn_interface_data = interface_vlan_table[CkEnum.REDUNDANCY_GROUP][ae_name]

        else:
            system_label = nodes['switch']['label']
            if system_label not in interface_vlan_table:
                interface_vlan_table[system_label] = {}
            if_name = nodes[INTERFACE_NODE]['if_name']
            if if_name not in interface_vlan_table[system_label]:
                interface_vlan_table[system_label][if_name] = {
                    CkEnum.TAGGED_VLANS: [],
                    CkEnum.UNTAGGED_VLAN: None,
                }
            this_interface_data = interface_vlan_table[system_label][if_name]

        vnid = int(nodes[VN_NODE]['vn_id'] )
        is_tagged = 'vlan_tagged' in nodes[SINGLE_VLAN_NODE]['attributes']
        if is_tagged:
            if vnid not in this_evpn_interface_data[CkEnum.TAGGED_VLANS]:
                this_evpn_interface_data[CkEnum.TAGGED_VLANS].append(vnid)
        else:
            this_evpn_interface_data[CkEnum.UNTAGGED_VLAN] = vnid

    summary = [f"{x}:{len(interface_vlan_table[x])}" for x in interface_vlan_table.keys()]
    logging.warning(f"BP:{the_bp.label} {summary=}")

    return interface_vlan_table
