import logging
import dotenv
import asyncio
import uvicorn
import json
from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import os
from pydantic import BaseModel

from .ck_global import ServerItem, BlueprintItem, global_store, sse_queue, DataStateEnum, SseEvent, SseEventEnum, SseEventData, get_timestamp
from .generic_systems import GenericSystems
from .access_switches import access_switches
from .virtual_networks import VirtualNetworks

logger = logging.getLogger(__name__)
app = FastAPI()

app.mount("/static", StaticFiles(directory="src/app/static"), name="static")
app.mount("/js", StaticFiles(directory="src/app/static/js"), name="js")
app.mount("/css", StaticFiles(directory="src/app/static/css"), name="css")
app.mount("/images", StaticFiles(directory="src/app/static/images"), name="images")

@app.get("/", response_class=HTMLResponse)
async def get_index_html(request: Request):
    return FileResponse("src/app/static/index.html")

@app.post("/test", response_class=HTMLResponse)
async def test(request: Request):
    data = await request.body()
    logger.warning(f"request.body: {data}")
    result = data
    return result

@app.post("/upload-env-ini")
async def upload_env_ini(file: UploadFile):
    file_content = await file.read()
    logging.warning(f"/upload_env_ini: {file.filename=} {file_content=}")
    content = global_store.env_ini.update(file_content)
    logging.warning(f"/upload_env_ini: {global_store.env_ini.__dict__}")
    return content

@app.post("/update-env-ini")
async def update_env_ini(server: ServerItem):
    logging.warning(f"/update-env-ini: {server=}")
    global_store.update_env_ini(server)
    logging.warning(f"/update-env-ini: {global_store.env_ini.__dict__}")
    return server


@app.post("/login-server")
async def login_server(server: ServerItem):
    logging.warning(f"/login_server: {server=}")
    version = global_store.login_server(server)
    return version

@app.post("/logout-server")
async def logout_server():
    logging.warning(f"/logout_server")
    version = GlobalStore.logout_server()
    return


@app.post("/login-blueprint")
async def login_blueprint(blueprint: BlueprintItem):
    logging.warning(f"/login_blueprint: begin {blueprint=}")
    id = global_store.login_blueprint(blueprint)
    logging.warning(f"/login_blueprint: end {blueprint=}")
    return id


# from SyncStateButton
@app.get("/sync")
async def sync():
    # yield {}
    logging.warning(f"/sync_access_switches begin {get_timestamp()=}")
    await global_store.migration_status.refresh()
    await access_switches.sync_access_switches()
    logging.warning(f"/sync_access_switches end")

    logging.warning(f"/sync_generic_systems begin")
    await access_switches.sync_generic_systems()
    logging.warning(f"/sync_generic_systems end")

    logging.warning(f"/update_virtual_networks_data begin")
    await access_switches.update_virtual_networks_data()
    logging.warning(f"/update_virtual_networks_data end")

    logging.warning(f"/update-connectivity-template-data begin")
    await access_switches.sync_connectivity_template()
    logging.warning(f"/update-connectivity-template-data end")

    await global_store.migration_status.set_sync_done()

    return {}

class SystemLabel(BaseModel):
    tbody_id: str

@app.post("/migrate-access-switches")
async def migrate_access_switches():
    """
    Remove TOR generic system in main blueprint
    """
    logging.warning(f"/migrate_access_switches begin")
    data = access_switches.remove_tor_gs_from_main()
    is_access_switch_created = await access_switches.create_new_access_switch_pair()
    await global_store.migration_status.set_as_done(is_access_switch_created)
    logging.warning(f"/migrate_access_switches end")
        
    return {}


@app.post("/migrate-generic-system")
async def migrate_generic_system(system_label: SystemLabel):
    logging.warning(f"/migrate_generic_system begin {system_label=}")
    is_migrated = await access_switches.migrate_generic_system(system_label.tbody_id)
    await global_store.migration_status.set_gs_done(is_migrated)
    logging.warning(f"/migrate_generic_system end {is_migrated=}")
    return {'is_migrated': is_migrated }


@app.post("/migrate-virtual-networks")
async def migrate_virtual_networks():
    logging.warning(f"/migrate_virtual_networks begin")
    is_vn_done = await access_switches.migrate_virtual_networks()
    await global_store.migration_status.set_vn_done(is_vn_done)
    logging.warning(f"/migrate_virtual_networks end")
    return {}

@app.post("/migrate-cts")
async def migrate_cts():
    logging.warning(f"/migrate_cts begin")
    is_ct_done = await access_switches.migrate_connectivity_templates()
    # await global_store.migration_status.set_ct_done(is_ct_done)  # done in generic_systems
    logging.warning(f"/migrate_cts end")
    return {}

@app.post("/compare-config")
async def compare_config():
    logging.warning(f"/compare_config begin")
    data = await access_switches.compare_config()
    logging.warning(f"/compare_config end")
    return {}


@app.get('/sse')
async def sse(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            item = await sse_queue.get()
            logging.warning(f"######## event_generator get {get_timestamp()} {sse_queue.qsize()=} {item=}")          
            yield item
            sse_queue.task_done()
            # set 0.05 to produce progressing
            await asyncio.sleep(0.02)
    return EventSourceResponse(event_generator())


async def main():
    dotenv.load_dotenv()
    app_host = os.getenv("app_host") or "127.0.0.1"
    app_port = int(os.getenv("app_port")) or 8000
    uvicorn.run(app, host=app_host, port=app_port, log_level="debug")

if __name__ == "__main__":
    main()
