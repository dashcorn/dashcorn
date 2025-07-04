from .hooks import start_threads, stop_threads
from ..dashboard.lifecycle_service import LifecycleService

service = LifecycleService(
    on_startup=[start_threads],
    on_shutdown=[stop_threads],
)

service.start()
