import strawberry
from typing import Any, List, Annotated, Union
import uuid
import dotenv
import os
import logging

from .ck_global import GlobalStore

from ck_apstra_api.apstra_blueprint import CkApstraBlueprint


@strawberry.type
class ApstraMemberInterface:
    id: str = strawberry.field(default_factory=lambda: str(uuid.uuid4()))
    sw_intf: str
    sg_intf: str
    speed: str

@strawberry.type
class ApstraLagInterface:
    id: str = strawberry.field(default_factory=lambda: str(uuid.uuid4()))
    sw_intf: str
    sg_intf: str

@strawberry.type
class ApstaGenericSystem:
    id: str = strawberry.field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    interfaces: List[ApstraMemberInterface]
    lag_interfaces: List[ApstraLagInterface]


@strawberry.type
class GenericSystemQuery:    
    @strawberry.field
    def get_generic_systems(self, info, bp_role: str, gs_label: str) -> ApstaGenericSystem:
        logging.warning(f"get_generic_systems() {bp_role=} {gs_label=}")
        if bp_role == "main_bp":
            bp = GlobalStore.main_bp
        elif bp_role == "tor_bp":
            bp = GlobalStore.tor_bp
        gs_data = bp.blueprint.get_server_interface_nodes(gs_label)
        logging.warning(f"gs_data {len(gs_data)} {gs_data}")
        return ApstaGenericSystem(label=gs_label, role=bp_role, bp_id=bp.id)
    
# @strawberry.type
# class GenericSystemMutation:    
#     @strawberry.field
#     def add_generic_system(self, info) -> List[ApstaGenericSystem]:
#         bps = [ x for x in GlobalStore.get_blueprints() ]
#         logging.warning(f"Connecting blueprints {bps}")
#         for bp in bps:  # ApstaBlueprint
#             logging.warning(f"Connecting blueprint {bp.label}")
#             bp.connect()
#             logging.warning(f"Connected blueprint {bp.label}")
#         return bps

