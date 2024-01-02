import logging
import dotenv
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pydantic import BaseModel

from .model.ck_global import GlobalStore, ServerItem, BlueprintItem

logger = logging.getLogger(__name__)
app = FastAPI()

app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.mount("/js", StaticFiles(directory="src/static/js"), name="js")
app.mount("/css", StaticFiles(directory="src/static/css"), name="css")
app.mount("/images", StaticFiles(directory="src/static/images"), name="images")
app.mount("/component", StaticFiles(directory="src/component"), name="component")

@app.get("/", response_class=HTMLResponse)
async def get_index_html(request: Request):
    return FileResponse("src/static/index.html")

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
    # dotenv.load_dotenv(file_content)
    # logging.warning(f"/upload_env_ini: {os.getenv('apstra_server_host')=}")
    content = GlobalStore.env_ini.update(file_content)
    # logging.warning(f"upload_env_ini: {os.getenv('apstra_server_host')=}")
    logging.warning(f"/upload_env_ini: {GlobalStore.env_ini.__dict__}")
    return content


@app.post("/login-server")
async def login_server(server: ServerItem):
    logging.warning(f"/login_server: {server=}")
    version = GlobalStore.login_server(server)
    return version


@app.post("/login-blueprint")
async def login_blueprint(blueprint: BlueprintItem):
    logging.warning(f"/login_blueprint: {blueprint=}")
    id = GlobalStore.login_blueprint(blueprint)
    return id


from .graphql_main import graphql_app
app.add_route("/graphql", graphql_app)

def main():
    dotenv.load_dotenv()
    app_host = os.getenv("app_host") or "127.0.0.1"
    app_port = int(os.getenv("app_port")) or 8000
    uvicorn.run(app, host=app_host, port=app_port, log_level="debug")

if __name__ == "__main__":
    main()
