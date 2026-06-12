class ChassisSearchPage:
    def __init__(self, window):
        self.window = window

    def search(self, chassis):
        self.window.child_window(auto_id="txtChassi").set_text(chassis)
        self.window.child_window(title="Buscar").click()

    def select_result(self):
        self.window.child_window(auto_id="grid").click_input()