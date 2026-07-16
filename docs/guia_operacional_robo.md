# Guia Operacional do Robô

## Objetivo

Este documento foi preparado para a área que acompanhará a execução do robô no dia a dia.

O robô apoia o processo de emissão de nota fiscal, tratamento no sistema de logística e envio do arquivo de volta ao CRM quando aplicável.

## O que o robô faz

De forma resumida, o processo acontece em três etapas:

1. O robô consulta o CRM e gera uma base com os registros que precisam ser tratados.
2. O robô entra no sistema de logística, processa os chassis e tenta gerar os documentos necessários.
3. O robô identifica os PDFs gerados e faz o anexo dessas informações no CRM.

## Quando a equipe deve usar este guia

Este guia deve ser usado para:

- acompanhar a execução do robô
- validar se o processamento terminou corretamente
- localizar arquivos gerados
- identificar rapidamente situações que exigem atuação manual

## Antes de iniciar a execução

Verifique os pontos abaixo:

- a máquina está ligada e com acesso aos sistemas necessários
- o CRM está disponível
- o sistema de logística/NBS está acessível
- a pasta de entrada contém os arquivos esperados, quando houver processamento de logística
- não existe bloqueio de tela, aviso do Windows ou janela pedindo interação manual

## Modos de execução

O robô pode rodar de formas diferentes, conforme a necessidade operacional.

### 1. Extração do CRM

Usado quando a equipe precisa gerar a base inicial com os registros que serão processados.

Resultado esperado:

- criação de um arquivo CSV na pasta `data/input`

### 2. Processamento da logística

Usado quando já existe um arquivo CSV na pasta de entrada e ele precisa ser processado no sistema de logística.

Resultado esperado:

- geração de um novo CSV na pasta `data/output`
- geração dos PDFs das notas, quando disponíveis

### 3. Anexação no CRM

Usado quando os PDFs já foram gerados e precisam ser anexados de volta no CRM.

Resultado esperado:

- atualização do CSV com o status do anexo

### 4. Fluxo completo

Também é possível executar o processo completo em sequência:

1. extração no CRM
2. processamento na logística
3. anexação no CRM

## Pastas que a área deve acompanhar

### Pasta de entrada

`data/input`

O que esperar nesta pasta:

- arquivos CSV que serão processados pelo robô
- arquivo gerado pela etapa de extração do CRM

### Pasta de saída

`data/output`

O que esperar nesta pasta:

- arquivos CSV já processados
- arquivos PDF gerados durante o processo
- pasta `nao_processado`, quando houver arquivos antigos ou pendentes retirados da entrada

### Pasta de logs

`data/logs`

O que esperar nesta pasta:

- arquivo de log diário
- arquivo `execution_report.csv`, com o resumo das execuções

## Como saber se a execução foi bem-sucedida

Sinais positivos mais comuns:

- o processamento termina sem travar
- o arquivo esperado aparece em `data/output`
- os PDFs são gerados quando a operação permite impressão
- o arquivo `execution_report.csv` recebe um novo registro de execução
- o log do dia mostra conclusão da rotina

## Onde validar o resultado

### 1. Arquivo de saída

O primeiro ponto de validação é o CSV salvo em `data/output`.

Esse arquivo normalmente traz informações como:

- situação do processamento
- mensagem de erro, quando houver
- indicação de PDF gerado
- data e hora de processamento

### 2. Relatório de execução

No arquivo `data/logs/execution_report.csv`, a equipe consegue consultar um resumo da execução, incluindo:

- data da execução
- bot executado
- arquivo processado
- status final
- quantidade processada
- quantidade não processada
- mensagem de retorno

### 3. Log diário

Na pasta `data/logs`, existe um arquivo de log com a data do dia.

Esse log ajuda a entender:

- em que etapa o robô estava
- qual item estava sendo tratado
- se houve erro de acesso, tela, impressão ou sistema

## Situações esperadas durante o processamento

Nem toda ocorrência significa falha do robô. Algumas situações fazem parte da regra do processo.

Exemplos:

- chassi sem informação suficiente
- chassi não localizado
- nota já emitida anteriormente
- PDF não encontrado para anexação

Nesses casos, o item pode ser marcado como não processado ou com falha, mas o restante do arquivo pode continuar normalmente.

## Quando a área deve agir

Acione o responsável técnico ou a área dona do processo quando houver:

- erro recorrente em vários itens do mesmo arquivo
- falha de acesso ao CRM
- falha de acesso ao sistema de logística/NBS
- ausência de arquivos de saída após a execução
- geração incompleta de PDFs
- falha de anexação no CRM em volume acima do esperado
- travamento da aplicação ou janelas bloqueando a continuidade

## Ações rápidas de conferência

Checklist simples após cada execução:

1. verificar se o arquivo foi movido ou gerado na pasta correta
2. conferir se há novo registro em `execution_report.csv`
3. validar se existem itens com erro no CSV final
4. confirmar se os PDFs esperados foram criados
5. confirmar se o CRM recebeu os anexos, quando essa etapa fizer parte da rotina

## Boas práticas para acompanhamento

- evitar uso manual da máquina durante a execução do robô
- não fechar janelas abertas pelo processo
- manter acesso estável à rede e aos sistemas
- guardar o CSV e os logs quando houver necessidade de análise posterior
- registrar horário da ocorrência quando for necessário abrir chamado

## Resumo para a operação

Se a execução ocorrer normalmente, a área deve encontrar:

- base gerada ou consumida corretamente
- arquivo final em `data/output`
- PDFs disponíveis, quando houver emissão
- atualização do relatório de execução
- status de anexação preenchido, quando houver retorno ao CRM

Se algum desses pontos não acontecer, a orientação é consultar primeiro o arquivo de saída e o relatório de execução. Se o motivo não ficar claro, o próximo passo é encaminhar o log do dia para análise técnica.