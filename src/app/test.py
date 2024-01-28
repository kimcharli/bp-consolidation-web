
import logging

from app.ck_global import global_store, ServerItem, BlueprintItem, EnvIni
from app.generic_systems import GenericSystems
from app.access_switches import access_switches

# class EnvData:
#     __slot__ = ('host', 'port', 'username', 'password', 'main_bp_label', 'tor_bp_label')
#     def __init__(self) -> None:
#         self.host = 'nf-apstra.pslab.link'
#         self.port = 443
#         self.username = 'admin'
#         self.password = 'admin'
#         self.main_bp_label = 'ATLANTA-Master'
#         self.tor_bp_label = 'AZ-1_1-R5R15'

env_data = EnvIni(host='nf-apstra.pslab.link', port=443, username='admin', password='admin', main_bp_label='ATLANTA-Master', tor_bp_label='AZ-1_1-R5R15')

server = ServerItem(
    host=env_data.host, 
    port=env_data.port, 
    username=env_data.username,
    password=env_data.password, 
    main_bp_label=env_data.main_bp_label,
    tor_bp_label=env_data.tor_bp_label)

async def main():
    main_bp = BlueprintItem(label=env_data.main_bp_label, role='main_bp')
    tor_bp = BlueprintItem(label=env_data.tor_bp_label, role='tor_bp')

    # global_store.update_env_ini(EnvData())
    global_store.replace_env_ini(env_data)
    version = global_store.login_server(server)
    id = global_store.login_blueprint(main_bp)
    id = global_store.login_blueprint(tor_bp)
    # data = GlobalStore.pull_tor_bp_data()
    as_data = access_switches.update_access_switches_table()
    # logging.warning(f"AccessSwitches {as_data=}")
    ## gs_data = access_switches.generic_systems.update_generic_systems_table()
    # logging.warning(f"GenericSystems {gs_data=}")
    ## vn_data = access_switches.update_virtual_networks_data()
    # logging.warning(f"VirtualNetworks {vn_data=}")
    # breakpoint()
    # gs_new = access_switches.migrate_generic_system('gs-az1kvm1004-az1kvm1028-atl1-LACP')

    ## vn_mig = access_switches.migrate_virtual_networks()

    ct_data = await access_switches.update_connectivity_template_data()
    ct_m_data = await access_switches.migrate_connectivity_templates()

if __name__ == '__main__':
    import asyncio
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())