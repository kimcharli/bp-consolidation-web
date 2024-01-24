import logging
import dotenv
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pydantic import BaseModel

from .ck_global import ServerItem, BlueprintItem, global_store
from .generic_systems import GenericSystems
from .access_switches import access_switches
from .virtual_networks import VirtualNetworks

logger = logging.getLogger(__name__)
app = FastAPI()

app.mount("/static", StaticFiles(directory="src/app/static"), name="static")
app.mount("/js", StaticFiles(directory="src/app/static/js"), name="js")
app.mount("/css", StaticFiles(directory="src/app/static/css"), name="css")
app.mount("/images", StaticFiles(directory="src/app/static/images"), name="images")
app.mount("/component", StaticFiles(directory="src/app/component"), name="component")

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


@app.get("/pull-data")
async def pull_data():
    logging.warning(f"/pull_data begin")
    data = GlobalStore.pull_tor_bp_data()
    logging.warning(f"/pull_data end")
    return data

# from SyncStateButton
@app.get("/update-access-switches-table")
async def update_access_switches_table():
    logging.warning(f"/update_access_switches_table begin")
    data = access_switches.update_access_switches_table()
    logging.warning(f"/update_access_switches_table end")
    return data


# from SyncStateButton
@app.get("/update-generic-systems-table")
async def update_generic_systems_table():
    logging.warning(f"/update_generic_systems_table begin")
    data = access_switches.update_generic_systems_table()
    logging.warning(f"/update_generic_systems_table end")
    return data

@app.get("/update-virtual-networks-data")
async def update_virtual_networks_data():
    logging.warning(f"/update_virtual_networks_data begin")
    data = access_switches.update_virtual_networks_data()
    logging.warning(f"/update_virtual_networks_data end")
    return data

class SystemLabel(BaseModel):
    tbody_id: str

@app.post("/migrate-access-switches")
async def migrate_access_switches():
    """
    Remove TOR generic system in main blueprint
    """
    logging.warning(f"/migrate_access_switches begin")
    data = global_store.remove_old_generic_system_from_main()
    data = global_store.create_new_access_switch_pair()
    logging.warning(f"/migrate_access_switches end")
    return data


@app.post("/migrate-generic-system")
async def migrate_generic_system(system_label: SystemLabel):
    logging.warning(f"/migrate_generic_system begin {system_label=}")
    data = access_switches.migrate_generic_system(system_label.tbody_id)
    logging.warning(f"/migrate_generic_system end {data=}")
    return data


@app.post("/migrate-virtual-networks")
async def migrate_virtual_networks():
    logging.warning(f"/migrate_virtual_networks begin")
    data = access_switches.migrate_virtual_networks()
    logging.warning(f"/migrate_virtual_networks end {data=}")
    return data



def main():
    dotenv.load_dotenv()
    app_host = os.getenv("app_host") or "127.0.0.1"
    app_port = int(os.getenv("app_port")) or 8000
    uvicorn.run(app, host=app_host, port=app_port, log_level="debug")

if __name__ == "__main__":
    main()
