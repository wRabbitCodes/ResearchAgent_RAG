from src.utils.initializer import initialize
from src.config.config import Config


if __name__ == "__main__":
    import uvicorn

    config = Config()
    initialize()
    uvicorn.run("src.api.app:app", host=config.host, port=config.port, reload=True)
