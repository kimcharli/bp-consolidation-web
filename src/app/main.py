import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

logger = logging.getLogger(__name__)
app = FastAPI()

app.mount("/static", StaticFiles(directory="src/static"), name="static")
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


from .graphql_main import graphql_app
app.add_route("/graphql", graphql_app)


def main():
    # config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="debug", reload=True)
    # server = uvicorn.Server(config)
    # await server.serve()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")

if __name__ == "__main__":
    main()
