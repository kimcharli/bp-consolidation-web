import strawberry
from typing import Any, List, Annotated, Union
import uuid
import dotenv
import os
import logging

from .ck_global import GlobalStore

from ck_apstra_api.apstra_blueprint import CkApstraBlueprint


@strawberry.type
class ApstaBlueprint:
    id: str = strawberry.field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    role: str = None
    bp_id: str = None
    blueprint: strawberry.Private[CkApstraBlueprint] = None

    def connect(self):
        logging.warning(f"Connecting blueprint {self.label}, {GlobalStore.apstra_server}")
        session = GlobalStore.apstra_server.session
        self.blueprint = CkApstraBlueprint(session=session, label=self.label)
        self.bp_id = self.blueprint.id

@strawberry.type
class BlueprintQuery:    
    @strawberry.field
    def fetch_blueprints(self, info) -> List[ApstaBlueprint]:
        dotenv.load_dotenv()
        main_bp_label = os.getenv("main_bp")
        tor_bp_label = os.getenv("tor_bp")
        main_bp = ApstaBlueprint(label=main_bp_label, role="main_bp")
        GlobalStore.main_bp = main_bp
        tor_bp = ApstaBlueprint(label=tor_bp_label, role="tor_bp")
        GlobalStore.tor_bp = tor_bp
        return [main_bp, tor_bp]
    
@strawberry.type
class BlueprintMutation:    
    @strawberry.field
    def connect_blueprints(self, info) -> List[ApstaBlueprint]:
        bps = [ x for x in GlobalStore.get_blueprints() ]
        logging.warning(f"Connecting blueprints {bps}")
        for bp in bps:  # ApstaBlueprint
            logging.warning(f"Connecting blueprint {bp.label}")
            bp.connect()
            logging.warning(f"Connected blueprint {bp.label}")
        return bps

