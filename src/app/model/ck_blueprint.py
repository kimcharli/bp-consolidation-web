import strawberry
from typing import List, Annotated, Union
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



@strawberry.type
class BlueprintQuery:    
    @strawberry.field
    def fetch_blueprints(self, info) -> List[ApstaBlueprint]:
        dotenv.load_dotenv()
        main_bp_label = os.getenv("main_bp")
        tor_bp_label = os.getenv("tor_bp")
        main_bp = ApstaBlueprint(label=main_bp_label, role="main_bp")
        tor_bp = ApstaBlueprint(label=tor_bp_label, role="tor_bp")
        return [main_bp, tor_bp]
    
    def fetch_blueprints_real(self, info) -> List[ApstaBlueprint]:
        session = GlobalStore.apstra_server.session
        logging.info(f"{session=}")
        dotenv.load_dotenv()
        main_bp_label = os.getenv("main_bp")
        tor_bp_label = os.getenv("tor_bp")
        ck_main_bp = CkApstraBlueprint(session=session, label=main_bp_label)
        ck_tor_bp = CkApstraBlueprint(session=session, label=tor_bp_label)
        main_bp = ApstaBlueprint(label=main_bp_label, role="main_bp")
        tor_bp = ApstaBlueprint(label=tor_bp_label, role="tor_bp")
        main_bp.blueprint = ck_main_bp
        tor_bp.blueprint = ck_tor_bp
        GlobalStore.main_bp = main_bp
        GlobalStore.tor_bp = tor_bp
        main_bp.bp_id = ck_main_bp.id
        tor_bp.bp_id = ck_tor_bp.id
        return [main_bp, tor_bp]

