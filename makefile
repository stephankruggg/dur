PYTHON=python3
SERVER_DISCOVERER_SCRIPT=src/server_discoverer_main.py
SERVER_SEQUENCER_SCRIPT=src/server_sequencer_main.py
CLIENT_SCRIPT=src/client_main.py
SERVER_SCRIPT=src/server_main.py

.PHONY: help install runss runsd runs runc clean

help:
	@echo "Uso: make [comando] (ID)"
	@echo "Comandos:"
	@echo "  install - Instala as dependências do projeto"
	@echo "  runss - Executa o server_sequencer_main.py"
	@echo "  runsd - Executa o server_discoverer_main.py"
	@echo "  runs - Executa o server_main.py com o ID passado por argumento"
	@echo "  runc - Executa o client_main.py com o ID passado por argumento"
	@echo "  clean - Remove arquivos temporários"

install:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

runsd:
	$(PYTHON) $(SERVER_DISCOVERER_SCRIPT)

runss:
	$(PYTHON) $(SERVER_SEQUENCER_SCRIPT)

runs:
	$(PYTHON) $(SERVER_SCRIPT) $(filter-out $@,$(MAKECMDGOALS))

runc:
	$(PYTHON) $(CLIENT_SCRIPT) $(filter-out $@,$(MAKECMDGOALS))

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

# Prevents make from interpreting the arguments as make targets
%:
	@: