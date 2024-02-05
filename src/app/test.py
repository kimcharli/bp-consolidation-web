
import logging

from app.ck_global import global_store, ServerItem, BlueprintItem, EnvIni
from app.generic_systems import GenericSystems
from app.access_switches import AccessSwitches

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

    # 
    # sync
    # 
    global_store.access_switches = AccessSwitches()
    global_store.generic_systems = None
    access_switches = global_store.access_switches

    await global_store.migration_status.refresh()
    await access_switches.sync_access_switches()
    logging.warning(f"/sync_access_switches end")

    logging.warning(f"/sync_generic_systems begin")
    # await access_switches.sync_generic_systems()
    await global_store.generic_systems.refresh_tor_generic_systems()
    logging.warning(f"/sync_generic_systems end")

    logging.warning(f"/update_virtual_networks_data begin")
    await access_switches.update_virtual_networks_data()
    logging.warning(f"/update_virtual_networks_data end")

    logging.warning(f"/update-connectivity-template-data begin")
    await access_switches.sync_connectivity_template()
    logging.warning(f"/update-connectivity-template-data end")

    await global_store.migration_status.set_sync_done()


    # await access_switches.remove_tor_gs_from_main()
    # await access_switches.create_new_access_switch_pair()


    await global_store.generic_systems.migrate_generic_systems()



    # as_data = await access_switches.sync_access_switches()
    # gs_data = await access_switches.sync_generic_systems()
    # vn_data = await access_switches.update_virtual_networks_data()
    # ct_data = await access_switches.sync_connectivity_template()
    # logging.warning(f"VirtualNetworks {vn_data=}")
    # breakpoint()
    # gs_new = await access_switches.migrate_generic_system('gs-az1kvm1004-az1kvm1028-atl1-LACP')

    ## vn_mig = access_switches.migrate_virtual_networks()

    # ct_m_data = await access_switches.migrate_connectivity_templates()

if __name__ == '__main__':
    import asyncio
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())