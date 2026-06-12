from src.logistics.flows.main_flow import NBSMainFlow
from src.shared.utils.logger import get_logger
from config.credentials import LogisticsCredentials

logger = get_logger(__name__)

class NBSBot:
    def __init__(self):
        self.flow = NBSMainFlow()
        self.user = LogisticsCredentials.USERNAME
        self.password = LogisticsCredentials.PASSWORD
        self.server = LogisticsCredentials.SERVER

    def run(self):
        self.flow.run(self.user, self.password, self.server)
