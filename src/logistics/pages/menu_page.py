class MenuPage:
    def __init__(self, window):
        self.window = window

    def go_to_chassis_search(self):
        self.window.type_keys("%F")  # ALT + F (exemplo)
        self.window.type_keys("C")   # abrir menu