from pywinauto import Application

class DesktopDriver:
    def __init__(self, app_path=None):
        self.app = None
        self.main_window = None
        self.app_path = app_path

    def start(self):
        self.app = Application(backend="uia").start(self.app_path)
        self.main_window = self.app.window()
        return self.main_window

    def connect(self, title):
        self.app = Application(backend="uia").connect(title=title)
        self.main_window = self.app.window(title=title)
        return self.main_window
