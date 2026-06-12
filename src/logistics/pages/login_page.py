class LoginPage:
    def __init__(self, window):
        self.window = window

    def fill_user(self, user):
        self.window.child_window(auto_id="txtUser").set_text(user)

    def fill_password(self, password):
        self.window.child_window(auto_id="txtPassword").set_text(password)

    def click_login(self):
        self.window.child_window(title="Login").click()