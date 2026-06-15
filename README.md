# RPA Project

Automação de CRM (web) e Sistema de Logística com Selenium + Python.

## Estrutura
```
rpa_project/
├── config/           # Configurações e credenciais (via .env)
├── data/             # Inputs, outputs e logs gerados em runtime
├── docs/             # Documentação adicional
├── src/
│   ├── crm/          # Tudo relacionado ao CRM web
│   │   ├── pages/    # Page Objects (uma classe por tela)
│   │   ├── components/ # Componentes reutilizáveis (forms, tables)
│   │   └── flows/    # Orquestração de fluxos de negócio
│   ├── logistics/    # Sistema de logística em construção (próxima fase)
│   └── shared/       # Código comum entre bots
│       ├── browser/  # Driver factory e BasePage
│       ├── utils/    # Logger, retry, file handler
│       └── exceptions/ # Hierarquia de exceções
├── tests/            # Testes unitários por módulo
├── main.py           # Entry point: python main.py --bot crm
├── requirements.txt
└── .env.example      # Copie para .env e preencha
```

## Setup
```bash
cp .env.example .env          # Configure suas credenciais
pip install -r requirements.txt
python main.py --bot crm
```

## Execução
```bash
python main.py --bot crm         # Apenas CRM
python main.py --bot logistics   # Apenas logística
python main.py --bot all         # Ambos em sequência
```

## Testes
```bash
pytest tests/ -v
```
