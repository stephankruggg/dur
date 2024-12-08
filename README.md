# dur

## Funcionamento
O DUR é um programa de controle de concorrência em transações com replicação de atualização adiada (Deferred Update Replication). Consiste em um grupo dinâmico de servidores replicados que atuam como Key-Value Stores (Bancos de dados de chave-valor) em memória não-volátil. O sistema é dividido em:
- Servidores Key-Value Stores (SKVS) replicados que salvam os valores enviados pelos clientes.
- Um servidor sequenciador (SS), responsável por garantir a ordem da execução das operações em todos os servidores.
- Um servidor descobridor (SD), responsável por conectar os clientes aos servidores replicados, que registra quais endereços de servidores estão disponíveis.
- Clientes Key-Value Stores (CKVS) que atuam como uma interface ao usuário para se conectar aos servidores, sendo possível enviar operações de leitura, escrita, aborto ou confirmação.

## Configurações
O programa possui um arquivo de configurações: `src/utils/constants.py`. Nele é possível:
- Configurar qual o nome do diretório que guarda os dados de exemplo, por meio da variável `FOLDER_NAME`. Padrão `examples`.
- Configurar qual o exemplo que está em execução atualmente, por meio da variável `EXAMPLE_INSTANCE`. Padrão: `1`.
- Configurar quais os endereços de cada SKVS, por meio das variáveis `SERVER_KEY_VALUE_STORE_ADDRESS` e `SERVER_KEY_VALUE_STORE_BASE_PORT`, representando respectivamente o endereço e a porta base. Padrão: `127.0.0.1` e `5000`.
- Configurar qual o endereço do servidor descobridor, por meio das variáveis `SERVER_DISCOVERER_ADDRESS` e `SERVER_DISCOVERER_PORT`, representando respectivamente o endereço e a porta. Padrão: `127.0.0.1` e `5100`.
- Configurar qual o endereço do servidor sequenciador, por meio das variáveis `SERVER_SEQUENCER_ADDRESS` e `SERVER_SEQUENCER_PORT`, representando respectivamente o endereço e a porta. Padrão: `127.0.0.1` e `5200`.
- Configurar quais os endereços de escuta ao número de sequência de cada SKVS, por meio das variáveis `SERVER_KEY_VALUE_STORE_SN_ADDRESS` e `SERVER_KEY_VALUE_STORE_SN_PORT`, representando respectivamente o endereço e a porta. Padrão: `127.0.0.1` e `5300`.
- Consultar o formato das mensagens trocadas entre os integrantes dos sistemas.

## Execução
Para a execução do DUR, é necessária a instalação de algumas bibliotecas listadas no arquivo `requirements.txt`. Para isso, abra um terminal e execute o seguinte comando:
``` bash
make install
```

Para iniciar a execução do sistema, execute o comando para iniciar o servidor descobridor:
``` bash
make runsd
```

Abra outro terminal e execute o comando para iniciar o servidor sequenciador:
``` bash
make runss
```

Para a execução dos servidores, abra outro terminal e execute o comando:
``` bash
make runs <SKVS-id>
```

Por exemplo:
``` bash
make runs 0
```

Para a execução dos clientes, abra outro terminal e execute o comando:
``` bash
make runc <CKVS-id>
```

Por exemplo:
``` bash
make runc 0
```

O cliente é executado em formato de console interativo do Python (REPL), que permite ao usuário executar código Python dinamicamente. Para utilizar o CKVS, é necessário utilizar a variável `db` disponível. As funções disponíveis estão descritas abaixo:
- `db.read('<item-name>')` lê um item do CKVS. Caso esse item já esteja no conjunto de escrita ou leitura do CKVS, é retornado o valor ali salvo. Caso o item ainda não esteja em nenhum, ele é buscado de um SKVS disponível.
- `db.read('<item-name>', <item-value>)` escreve um item no conjunto de escrita do CKVS.
- `db.abort()` aborta a transação atual, limpando os conjuntos de leitura ou escrita e pulando o ID de transação.
- `db.commit()` envia uma requisição de confirmação aos SKVSs, que devem retornar com o resultado da operação - bem-sucedida (commit) ou mal-sucedida (abort). Além disso, independentemente do resultado da transação, os conjuntos de leitura e escrita são limpos e o ID de transação é pulado.

## Limpeza
Para remover os arquivos bytecode compilados, abra um terminal e execute o comando:
``` bash
make clean
```
