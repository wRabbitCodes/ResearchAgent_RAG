from fastapi import FastAPI
from src.api.routes import ask, ingest, metrics, file_io
from fastapi.responses import FileResponse, HTMLResponse

from src.utils.logger_config import setup_logger


def create_app() -> FastAPI:
    setup_logger()
    app = FastAPI(
        title="RA Assistant",
        version="1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.include_router(ask.router)
    app.include_router(ingest.router)
    app.include_router(metrics.router)
    app.include_router(file_io.router)
    return app


app = create_app()


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<html>
  <head>
    <title>RA Assistant Agent</title>
    <link rel="icon" href="/favicon.ico">
    <style>
      body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        padding: 3rem;
        background-color: #f9f9f9;
        color: #333;
      }
      h1 {
        font-size: 2.5rem;
        color: #2c3e50;
      }
      p {
        font-size: 1.1rem;
        margin: 1rem 0;
      }
      a {
        color: #007acc;
        text-decoration: none;
      }
      a:hover {
        text-decoration: underline;
      }
      .footer {
        margin-top: 3rem;
        font-size: 0.95rem;
        color: #555;
      }
    </style>
  </head>
  <body>
    <h1>Greetings from your Research Assistant!</h1>
    <p>Explore the <a href="/docs">Swagger UI</a> for API testing.</p>
    <p>WebSocket Endpoint: <code>ws://localhost:8000/ws/ask/stream</code></p>

    <div class="footer">
      <p><strong>Author:</strong> Aashish Bhandari</p>
      <p><strong>Email:</strong> <a href="mailto:aashish.dux@gmail.com">aashish.dux@gmail.com</a></p>
      <p><strong>Repositories:</strong><br>
        <a href="https://github.com/githubForAashish" target="_blank">githubForAashish</a> |
        <a href="https://github.com/wRabbitCodes" target="_blank">wRabbitCodes</a>
      </p>
    </div>
  </body>
</html>
"""


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("src/api/static/favicon.ico")
