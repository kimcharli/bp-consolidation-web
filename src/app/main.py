import logging
import dotenv
import asyncio
import uvicorn
from fastapi import FastAPI, Request, UploadFile, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import os
import yaml

from .ck_global import global_store, sse_queue, SseEvent, SseEventEnum, SseEventData, GlobalStore
from .generic_systems import GenericSystemWorker
from .access_switches import AccessSwitcheWorker
from .vlan_cts import CtWorker
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

@app.post("/upload-env-ini")
async def upload_env_ini(request: Request, file: UploadFile):
    """
    take environment yaml file to init global_store
    """
    global global_store

    logger.warning(f"/upload-env-ini begin")
    file_content = await file.read()
    file_dict = yaml.safe_load(file_content)

    global_store = GlobalStore(**file_dict)
    
    await SseEvent(data=SseEventData(id='apstra-host', value=global_store.apstra['host'])).send()
    await SseEvent(data=SseEventData(id='apstra-port', value=global_store.apstra['port'])).send()
    await SseEvent(data=SseEventData(id='apstra-username', value=global_store.apstra['username'])).send()
    await SseEvent(data=SseEventData(id='apstra-password', value=global_store.apstra['password'])).send()

    await SseEvent(data=SseEventData(id='main_bp', value=global_store.target['main_bp'])).send()
    await SseEvent(data=SseEventData(id='tor_bp', value=global_store.target['tor_bp'])).send()

    await SseEvent(data=SseEventData(id='load-env-div').done()).send()

    logging.warning(f"/upload_env_ini: {global_store=}")
    return await connect()



@app.get("/connect")
async def connect():
    """
    login to the server and blueprints
    then sync the data
    """
    global global_store

    logging.warning(f"/connect begin")
    await SseEvent(data=SseEventData(id='connect').loading()).send()

    version = global_store.login_server()

    await global_store.login_blueprint()
    await SseEvent(data=SseEventData(id='connect').done()).send()
    logging.warning(f"/connect end")
    # return version
    return await sync()

@app.get("/disconnect")
async def disconnect():
    """
    logout from the server and blueprints, discard the global_store
    """
    global global_store

    logging.warning(f"/disconnect")
    global_store.logout_server()
    global_store = None


    await SseEvent(data=SseEventData(id='apstra-host', value="")).send()
    await SseEvent(data=SseEventData(id='apstra-port', value="")).send()
    await SseEvent(data=SseEventData(id='apstra-username', value="")).send()
    await SseEvent(data=SseEventData(id='apstra-password', value="")).send()

    await SseEvent(data=SseEventData(id='main_bp', value="").init()).send()
    await SseEvent(data=SseEventData(id='tor_bp', value="").init()).send()

    await SseEvent(data=SseEventData(id='connect').init()).send()
    await SseEvent(data=SseEventData(id='load-env-div').init()).send()
    return "disconnected"


# from SyncStateButton
@app.get("/sync")
async def sync():
    """
    sync the data from the server for the access switches, generic systems, virtual networks, and connectivity templates
    """    
    global global_store

    logging.warning(f"/sync begin")
    await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_SYNC_STATE).loading()).send()

    accessSwitchWorker = global_store.accessSwitchWorker = AccessSwitcheWorker(global_store=global_store)
    genericSystemWorker = global_store.genericSystemWorker = GenericSystemWorker(global_store=global_store)
    await genericSystemWorker.sync_tor_generic_systems()
    await genericSystemWorker.init_leaf_switches()
    await genericSystemWorker.refresh_tor_generic_systems()

    global_store.virtualNetworks = VirtualNetworks(global_store=global_store, vns={}, this_bound_to=global_store.bound_to, bound_to={})
    await global_store.virtualNetworks.sync_tor_vns()

    ctWorker = global_store.ctWorker = CtWorker(global_store=global_store)
    ctWorker.sync_tor_ct()
    ctWorker.sync_main_ct()
    await ctWorker.referesh_ct_table()

    await global_store.migration_status.set_sync_done()

    logging.warning(f"/sync end")
    return {}

@app.get("/migrate-access-switches")
async def migrate_access_switches():
    """
    Remove TOR generic system in main blueprint and create new access switches in main blueprint
    """
    global global_store

    accessSwitchWorker = global_store.accessSwitchWorker
    logging.warning(f"/migrate_access_switches begin")
    await accessSwitchWorker.remove_tor_gs_from_main()
    await accessSwitchWorker.create_new_access_switch_pair()
    # await global_store.migration_status.set_as_done(is_access_switch_created)
    logging.warning(f"/migrate_access_switches end")
        
    return {}


@app.get("/migrate-generic-systems")
async def migrate_generic_system():
    global global_store

    logging.warning(f"/migrate_generic_systems begin")
    await global_store.generic_systems.migrate_generic_systems()
    logging.warning(f"/migrate_generic_systems end")
    return {}


@app.get("/migrate-virtual-networks")
async def migrate_virtual_networks():
    global global_store

    await SseEvent(data=SseEventData(id=SseEventEnum.BUTTON_MIGRATE_VN).loading()).send()
    logging.warning(f"/migrate_virtual_networks begin")
    await global_store.virtualNetworks.migrate_virtual_networks()
    logging.warning(f"/migrate_virtual_networks end")
    return {}

@app.get("/migrate-cts")
async def migrate_cts():
    global global_store

    CtWorker = global_store.ctWorker
    logging.warning(f"/migrate_cts begin")
    await CtWorker.migrate_connectivity_templates()
    logging.warning(f"/migrate_cts end")
    return {}

@app.get("/compare-config")
async def compare_config():
    global global_store

    accessSwitchWorker = global_store.accessSwitchWorker
    logging.warning(f"/compare_config begin")
    data = await accessSwitchWorker.compare_config()
    logging.warning(f"/compare_config end")
    return {}


@app.get('/sse')
async def sse(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            item = await sse_queue.get()
            # logging.warning(f"######## event_generator get {sse_queue.qsize()=} {item=}")          
            yield item
            sse_queue.task_done()
            # set 0.05 to produce progressing
            await asyncio.sleep(0.05)
    return EventSourceResponse(event_generator())


async def main():
    dotenv.load_dotenv()
    app_host = os.getenv("app_host") or "127.0.0.1"
    app_port = int(os.getenv("app_port")) or 8000
    uvicorn.run(app, host=app_host, port=app_port, log_level="debug")

if __name__ == "__main__":
    main()
