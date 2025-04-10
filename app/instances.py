import asyncio
import os
import threading

from app.utils import setup_logger

logger = setup_logger(__name__)


class ThreadSafeKey:
    _key = None
    _name = None
    _lock = threading.Lock()

    @classmethod
    def add(cls, data: tuple):
        """Добавляет элемент в множество."""
        with cls._lock:
            logger.debug(f"Set key = {data}")
            cls._key = data[0]
            cls._name = data[1]

    @classmethod
    def is_valid(cls, key: int):
        """Проверяет, содержится ли элемент в множестве."""
        with cls._lock:
            logger.debug(f"is_valid (our == your): {cls._key} == {key} ?")
            if key == cls._key:
                return cls._name
            return None

    @classmethod
    def clear(cls):
        """Удаляет элемент из множества, если он есть."""
        with cls._lock:
            logger.debug(f"Clear key = {cls._key}")
            cls._key = None


class TimerSingleton:
    _instance = None
    _task = None
    _event = asyncio.Event()
    _lock = asyncio.Lock()
    timeout = int(os.getenv("TIMER", 30))
    message_id = None
    chat_id = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TimerSingleton, cls).__new__(cls)
        return cls._instance

    async def _start_timer(self):
        """Таймер с задержкой в n секунд"""
        logger.debug(f"Таймер начался, ожидаем {self.timeout} секунд...")
        try:
            await asyncio.wait_for(self._event.wait(), timeout=self.timeout)
        except TimeoutError:
            logger.debug("Таймер завершился.")
        except asyncio.CancelledError:
            logger.debug("Таймер был остановлен вручную.")
        finally:
            ThreadSafeKey.clear()
            self._task = None
            self._event.clear()

    async def start(self, data: tuple):
        """Запускает таймер и сохраняет ID сообщения"""
        async with self._lock:
            if self._task is not None and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    print("Предыдущий таймер был отменен.")
            ThreadSafeKey.add(data)
            self._event.clear()
            self._task = asyncio.create_task(self._start_timer())

    async def stop(self, name=None):
        """Останавливает таймер до истечения времени"""
        logger.debug(f"Stop timer ({name})")
        async with self._lock:
            if self._task is not None:
                self._task.cancel()
                self._event.set()
