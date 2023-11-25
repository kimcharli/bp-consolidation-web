from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

from .lib.utils import openfile

app = FastAPI()

templates = Jinja2Templates(directory="src/templates")
app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = openfile("home.md")
    # result = templates.TemplateResponse("index.html", {"request": request})
    result = templates.TemplateResponse("page.html", {"request": request, "data": data})
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
