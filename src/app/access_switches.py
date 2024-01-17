import logging
from pydantic import BaseModel
from typing import Optional, List

from .model.ck_global import GlobalStore


class _AccessSwitchResponseItem(BaseModel):
    id: str
    value: str

class _AccessSwitchResponse(BaseModel):
    done: Optional[bool] = False
    values: Optional[List[_AccessSwitchResponseItem]] = []
    caption: Optional[str] = None


class AccessSwitches:
    peer_link = {}  # link-id = { system: {} }
    access_switches = []  # 
    tor_gs = { 'label': None, }
    
    @classmethod
    def update_access_switches_table(cls) -> dict:
        tor_bp = GlobalStore.bp['tor_bp']
        main_bp = GlobalStore.bp['main_bp']

        peer_link_query = """
            node('link',role='leaf_leaf',  name='link')
                .in_('link').node('interface', name='intf')
                .in_('hosted_interfaces').node('system', name='switch')
        """
        peer_link_nodes = tor_bp.query(peer_link_query, multiline=True)
        # cls.logger.warning(f"{peer_link_nodes=}")
        temp_access_switches = {}
        for link in peer_link_nodes:
            # register the switch label for further processing later
            switch_label = link['switch']['label']
            temp_access_switches[switch_label] = {'label': switch_label}
            link_id = link['link']['id']
            # peer_link 
            if link_id not in cls.peer_link:
                cls.peer_link[link_id] = { 'system': {} }
            link_data = cls.peer_link[link_id]
            link_data['speed'] = link['link']['speed']
            if switch_label not in link_data['system']:
                link_data['system'][switch_label] = []
            switch_data = link_data['system'][switch_label]
            switch_intf = link['intf']['if_name']
            switch_data.append(switch_intf)

        cls.access_switches = sorted(temp_access_switches.items(), key=lambda item: item[0])
        access_switch_pair = sorted(temp_access_switches)

        #  setup tor_gs label from the name of tor_bp switches
        if cls.access_switches[0][0].endswith(('a', 'b')):
            cls.tor_gs['label'] = cls.access_switches[0][0][:-1]
        elif cls.access_switches[0][0].endswith(('c', 'd')):
            cls.tor_gs['label'] = cls.access_switches[0][0][:-1] + 'cd'
        else:
            logging.critical(f"switch names {cls.switches} does not ends with 'a', 'b', 'c', or 'd'!")

        response = _AccessSwitchResponse()
        response.values.append(_AccessSwitchResponseItem(id=''))    
    