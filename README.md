# Emissão NF Banco Honda

Projeto de automação RPA em Python para integrar etapas do CRM web com o sistema de logística/NBS no Windows.

## Visão geral

A aplicação possui três modos principais de execução:

- `crm`: acessa o CRM web, navega até o funil de vendas e extrai registros para um CSV em `data/input`.
- `logistics`: lê arquivos CSV de `data/input`, processa chassis no sistema NBS, tenta emitir NF, Renave e impressão em PDF, e grava o resultado em `data/output`.
- `crm-attach`: localiza CSVs com caminhos de anexos (`nbs_attachment_path` ou `attachment_path`) e envia os PDFs gerados de volta ao CRM.

Também existe o modo `all`, que executa `crm`, `logistics` e `crm-attach` em sequência.

## Fluxo operacional

```text
CRM (extração) -> data/input/*.csv
Logística/NBS  -> data/output/*.csv + PDFs
CRM (anexação) -> anexa PDFs gerados ao CRM
```

Resumo do encadeamento:

1. O bot `crm` extrai oportunidades/NFs e gera um CSV de entrada.
2. O bot `logistics` consome esse CSV, processa os chassis e gera CSV enriquecido e PDFs.
3. O bot `crm-attach` usa os caminhos dos PDFs para anexar os arquivos no CRM.

## Arquitetura

```text
config/                  Configurações e credenciais via .env
data/input/              CSVs prontos para processamento
data/output/             CSVs processados e PDFs gerados
data/logs/               Logs diários e execution_report.csv
docs/                    Documentação complementar
scripts/                 Scripts auxiliares
src/crm/                 Automação web do CRM
src/logistics/           Automação desktop do NBS/logística
src/shared/              Infraestrutura compartilhada
tests/                   Testes automatizados
main.py                  Ponto de entrada dos bots
```

Organização interna:

- `pages/`: page objects e abstrações de tela.
- `components/`: blocos reutilizáveis de interface.
- `flows/`: fluxos de negócio e orquestração.
- `shared/browser/`: criação e gerenciamento do Selenium WebDriver.
- `shared/windows_application/`: suporte à automação desktop.
- `shared/utils/`: logger, arquivos, retry e relatório de execução.

## Requisitos

- Windows.
- Python 3.11+ recomendado.
- Google Chrome ou Mozilla Firefox para o CRM.
- Acesso ao CRM web.
- Acesso ao executável/ambiente do NBS no servidor configurado.

Dependências relevantes instaladas pelo projeto:

- `selenium`
- `webdriver-manager`
- `pywinauto`
- `python-dotenv`

## Configuração

Crie ou atualize o arquivo `.env` na raiz do projeto com as variáveis usadas pelo código:

```env
CRM_USERNAME=
CRM_PASSWORD=

LOGISTICS_USERNAME=
LOGISTICS_PASSWORD=
LOGISTICS_SERVER=
LOGISTICS_NFS_SERVER=C:\NBS\Nfvendas

CRM_BASE_URL=http://crm.grupoaccampo.com.br
LOGISTICS_BASE_SERVER=C:\NBS\ger_veic

HEADLESS=false
BROWSER=chrome
IMPLICIT_WAIT=30
PAGE_LOAD_TIMEOUT=120

MAX_RETRIES=3
RETRY_DELAY=2.0
```

Observações:

- O projeto já tenta carregar `.env` automaticamente.
- Os diretórios `data/input`, `data/output` e `data/logs` são criados automaticamente.
- O modo `headless` só se aplica ao CRM web; a automação da logística depende de interface gráfica do Windows.

## Instalação

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Execução

Executar apenas a extração do CRM:

```powershell
python main.py --bot crm
```

Executar apenas o processamento da logística:

```powershell
python main.py --bot logistics
```

Executar apenas a anexação no CRM:

```powershell
python main.py --bot crm-attach
```

Executar o fluxo completo:

```powershell
python main.py --bot all
```

Também é possível informar mais de um bot explicitamente:

```powershell
python main.py --bot crm logistics
python main.py --bot logistics crm-attach
```

## Hardening para Task Scheduler (Windows Server)

A aplicação possui validações de preflight e trava de execução única no `main.py`.

O que é validado antes da execução:

- presença do `.env` na raiz do projeto
- credenciais obrigatórias para os bots selecionados
- permissão de escrita em `data/input`, `data/output` e `data/logs`
- sessão interativa ativa para fluxos desktop (`logistics`)
- modo não-headless do CRM somente com sessão interativa
- existência dos caminhos configurados em `LOGISTICS_BASE_SERVER` e `LOGISTICS_NFS_SERVER`

Também foi adicionada trava anti-concorrência:

- lockfile em `data/logs/locks/rpa_runner.lock`
- limpeza automática de lock antigo com base em `HARDENING_LOCK_TTL_HOURS` (padrão 12)

### Script recomendado para agendamento

Arquivo: `scripts/task_scheduler_bootstrap.ps1`

Exemplo de execução manual:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\task_scheduler_bootstrap.ps1 -Bot all
```

Esse script:

- força o diretório de trabalho para a raiz do projeto
- ativa a virtualenv (`.venv`)
- executa `python main.py --bot <bot>`
- registra `stdout`/`stderr` em `data/logs/scheduler`

### Configuração recomendada da tarefa

- Program/script: `powershell.exe`
- Arguments: `-ExecutionPolicy Bypass -File "C:\caminho\projeto\scripts\task_scheduler_bootstrap.ps1" -Bot all`
- Start in: `C:\caminho\projeto`
- Marcar para não executar instâncias paralelas da mesma tarefa
- Para `logistics`, executar somente com usuário logado e desktop desbloqueado

## Entradas e saídas

### CRM

- Lê credenciais do `.env`.
- Extrai registros do CRM e grava um CSV como `crm_nfs_YYYYMMDD_HHMMSS.csv` em `data/input`.
- Antes de nova extração, move arquivos pendentes existentes em `data/input` para `data/output/nao_processado`.

### Logística

- Processa todos os arquivos `*.csv` de `data/input`.
- Espera pelo menos a coluna `veiculo_chassi` para cada linha.
- Enriquece as linhas com status, mensagens, timestamps e, quando existir, o caminho do PDF gerado.
- Salva o CSV final em `data/output` e remove o arquivo original de `data/input`.

Campos de retorno comuns adicionados no fluxo de logística:

- `nbs_status`
- `nbs_error`
- `nbs_processed_at`
- `nbs_renave_status`
- `nbs_renave_message`
- `nbs_print_nf_status`
- `nbs_print_nf_message`
- `nbs_attachment_path`
- `nbs_attachment_file_name`

### CRM Attach

- Procura CSVs em `data/output` e `data/input` que tenham `nbs_attachment_path` ou `attachment_path`.
- Atualiza cada linha com o resultado da anexação:
	- `crm_attachment_status`
	- `crm_attachment_error`
	- `crm_attachment_updated_at`

## Logs e rastreabilidade

Durante a execução, o projeto gera artefatos em `data/logs`:

- log diário com nome no formato `YYYY-MM-DD.log`
- `execution_report.csv` com status consolidado de cada execução
- `chassis_processing_report.csv` com rastreio por chassi ao longo das etapas

Status esperados no `chassis_processing_report.csv`:

- `Pendente`: chassi extraído no CRM e aguardando início da logística
- `Processando`: logística/NBS iniciada (ou concluída aguardando anexação no CRM)
- `Concluido`: anexação no CRM finalizada com sucesso
- `Erro`: falha em qualquer etapa; a coluna `observacao` recebe a mensagem do erro

## Testes

```powershell
pytest tests -v
```

## Observações técnicas

- O Chrome é o navegador padrão; Firefox pode ser habilitado com `BROWSER=firefox`.
- A criação do driver Chrome usa a instalação local do navegador.
- A automação desktop usa `pywinauto` e depende do ambiente do NBS disponível na máquina/servidor.
- O modo `all` registra um relatório final consolidado no encerramento da execução.
