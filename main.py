from src.config.config import Config

config = Config()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.app:app", host=config.host, port=config.port, reload=True)
