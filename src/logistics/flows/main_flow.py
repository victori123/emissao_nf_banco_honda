from src.logistics.components.nbs_session import NBSSession
from src.logistics.flows.login_flow import LoginFlow
from src.logistics.flows.chassis_search_flow import ChassisSearchFlow
from src.logistics.flows.nf_emission_flow import NFEmissionFlow
from config.settings import LOGISTICS_BASE_URL


class NBSMainFlow:
    def __init__(self, app_path=LOGISTICS_BASE_URL):
        self.session = NBSSession(app_path)

    def run(self, user, password):
        window = self.session.start()

        list_chassis = [] 
        LoginFlow(window).execute(user, password)
        ChassisSearchFlow(window).execute(list_chassis)
        NFEmissionFlow(window).execute()