from src.logistics.pages.print_nf_page import PrintNFPage
from src.shared.utils.logger import get_logger
from config.credentials import LogisticsCredentials
from config.settings import LOGISTICS_NFS_SERVER
from src.logistics.components.nbs_session import NBSNFSession

logger = get_logger(__name__)


class PrintNFFlow:
    def __init__(self, app_path=LOGISTICS_NFS_SERVER):
        self.session = NBSNFSession(app_path) 
        self.window = self.session.start()
        self.page = PrintNFPage(self.window)
        self.user = LogisticsCredentials.USERNAME
        self.password = LogisticsCredentials.PASSWORD
        self.nfs_server = LogisticsCredentials.NFS_SERVER

    def execute(self, chassis: str, download_path: str):
        logger.info("Iniciando PrintNFFlow para chassis %s", chassis)
        resultado = None
        try:
            # efetua login no servidor de impressão (pode ser outro executável/path)
            self.page.login_to_server(self.user, self.password, self.nfs_server)

            # localiza o chassi e realiza navegações nas duas telas necessárias
            self.page.search_chassis(chassis)
            resultado = self.page.navigate_second_screen_and_print(download_path=download_path)

            logger.info("PrintNFFlow finalizado com sucesso para chassis %s", chassis)
            return resultado

        except Exception:
            logger.error("Erro no PrintNFFlow", exc_info=True)
            raise
        finally:
            try:
                # garante fechamento/exit do servidor de impressão
                self.page.close(force=True)
            except Exception:
                logger.warning("Falha ao fechar servidor de impressão após tentativa de print")
