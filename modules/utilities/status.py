import modules.ui as ui
import modules.globals

def update_status(message: str, scope: str = 'DLC.CORE') -> None:
    try:
        print(f'[{scope}] {message}')
        if not modules.globals.headless and callable(ui.update_status):  # Ensure ui.update_status is callable
            ui.update_status(message)
    except Exception as e:
        print(f"[{scope}] Failed to update status: {e}")
