from dashcorn.dashboard.lifecycle_service import LifecycleService

def is_hub_running() -> bool:
    return LifecycleService.is_pid_alive()

def read_pid():
    return LifecycleService.read_pid_file()

def write_pid():
    return LifecycleService.write_pid_file()

def clear_pid():
    return LifecycleService.remove_pid_file()
