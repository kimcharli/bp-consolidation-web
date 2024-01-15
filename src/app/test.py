
import logging

from app.model.ck_global import GlobalStore, ServerItem, BlueprintItem
from app.generic_systems import GenericSystems


class EnvData:
    __slot__ = ('host', 'port', 'username', 'password', 'main_bp_label', 'tor_bp_label')
    def __init__(self) -> None:
        self.host = 'nf-apstra.pslab.link'
        self.port = 443
        self.username = 'admin'
        self.password = 'admin'
        self.main_bp_label = 'ATLANTA-Master'
        self.tor_bp_label = 'AZ-1_1-R5R15'

env_data = EnvData()

server = ServerItem(
    host=env_data.host, 
    port=env_data.port, 
    username=env_data.username,
    password=env_data.password, 
    main_bp_label=env_data.main_bp_label,
    tor_bp_label=env_data.tor_bp_label)

main_bp = BlueprintItem(label=env_data.main_bp_label, role='main_bp')
tor_bp = BlueprintItem(label=env_data.tor_bp_label, role='tor_bp')

GlobalStore.update_env_ini(EnvData())
version = GlobalStore.login_server(server)
id = GlobalStore.login_blueprint(main_bp)
id = GlobalStore.login_blueprint(tor_bp)
data = GlobalStore.pull_tor_bp_data()
gs = GenericSystems.get_generic_systems()
logging.warning(f"{gs=}")
