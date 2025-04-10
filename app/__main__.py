import os

import uvicorn
from tomllib import load

from app.server import server
from app.utils import setup_logger

logger = setup_logger(__name__)


def get_version():
    with open("pyproject.toml", "rb") as file:
        data = load(file)
    return data["tool"]["poetry"]["version"]


def run_server():
    """Запуск веб-сервера."""
    logger.info("Запуск FastAPI сервера")
    uvicorn.run(server, host="0.0.0.0", port=int(os.getenv("SERVER_PORT")))


if __name__ == "__main__":
    try:
        logger.info(f"Запуск приложения версии {get_version()}")
        run_server()
    except KeyboardInterrupt:
        logger.info("Работа приложения прервана")
    except Exception as ex:
        logger.critical(ex)
    finally:
        logger.info("Остановка приложения")
