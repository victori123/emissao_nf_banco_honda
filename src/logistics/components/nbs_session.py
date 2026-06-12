from src.shared.windows_application.desktop_driver import DesktopDriver

class NBSSession:
    def __init__(self, app_path):
        self.driver = DesktopDriver(app_path)

    def start(self):
        return self.driver.start()

    def get_main_window(self):
        return self.driver.main_window