from src.logistics.pages.print_nf_page import PrintNFPage
from src.shared.utils.logger import get_logger
from config.credentials import LogisticsCredentials

logger = get_logger(__name__)


class PrintNFFlow:
    def __init__(self, window):
        self.window = window
        self.page = PrintNFPage(window)
        self.user = LogisticsCredentials.USERNAME
        self.password = LogisticsCredentials.PASSWORD
        self.nfs_server = LogisticsCredentials.NFS_SERVER

    def execute(self, chassis: str):
        logger.info("Iniciando PrintNFFlow para chassis %s", chassis)
        resultado = None
        try:
            # efetua login no servidor de impressão (pode ser outro executável/path)
            self.page.login_to_server(self.user, self.password, self.nfs_server)

            # localiza o chassi e realiza navegações nas duas telas necessárias
            self.page.search_chassis(chassis)
            self.page.navigate_first_screen()
            resultado = self.page.navigate_second_screen_and_print()

            logger.info("PrintNFFlow finalizado com sucesso para chassis %s", chassis)
            return resultado

        except Exception:
            logger.error("Erro no PrintNFFlow", exc_info=True)
            raise
        finally:
            try:
                # garante fechamento/exit do servidor de impressão
                self.page.close()
            except Exception:
                logger.warning("Falha ao fechar servidor de impressão após tentativa de print")
