class NFEmissionPage:
    def __init__(self, window):
        self.window = window

    def emitir_nf(self):
        self.window.child_window(title="Emitir NF").click()

    def confirmar(self):
        self.window.child_window(title="Confirmar").click()
