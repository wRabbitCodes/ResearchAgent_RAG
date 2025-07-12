.PHONY: dev setup-ollama-entrypoint prepare-dirs setup-wait-script stop logs test create clean

run-with-ollama: setup-ollama-entrypoint prepare-dirs setup-wait-script check-backend

run: prepare-dirs
	docker compose -f docker-compose.base.yaml up --build;

check-backend:
	@echo "Checking LLM_BACKEND from .env (defaults to OLLAMA_BACKEND)..."
	@BACKEND=$$(grep -E '^LLM_BACKEND=' .env 2>/dev/null | cut -d '=' -f2 | tr -d '\r'); \
	[ -z "$$BACKEND" ] && BACKEND="OLLAMA_BACKEND"; \
	echo "Using backend: $$BACKEND"; \
	if [ "$$BACKEND" = "OLLAMA_BACKEND" ]; then \
		docker compose -f docker-compose.base.yaml -f docker-compose.ollama.yaml up --build; \
	elif [ "$$BACKEND" = "LLAMA_CPP_BACKEND" ]; then \
		docker compose -f docker-compose.base.yaml -f docker-compose.llamacpp.yaml up --build; \
	else \
		echo "Unknown backend: $$BACKEND. Use OLLAMA_BACKEND or LLAMA_CPP_BACKEND"; \
	fi
	exit 1;

prepare-dirs:
	@echo "Creating necessary data directories with correct permissions"
	@for dir in logs chroma_store models sample_data; do \
		if [ ! -d $$dir ]; then \
			echo "Creating $$dir"; \
			mkdir -p $$dir; \
		else \
			echo "$$dir already exists"; \
		fi; \
		chmod -R 775 $$dir; \
	done


setup-ollama-entrypoint:
	@echo "Setting up Ollama entrypoint script with preload"
	@mkdir -p .scripts
	@echo '#!/bin/sh' > .scripts/ollama-entrypoint.sh
	@echo 'ollama serve &' >> .scripts/ollama-entrypoint.sh
	@echo 'until ollama list >/dev/null 2>&1; do' >> .scripts/ollama-entrypoint.sh
	@echo '  echo "Waiting for Ollama server to respond..."' >> .scripts/ollama-entrypoint.sh
	@echo '  sleep 1' >> .scripts/ollama-entrypoint.sh
	@echo 'done' >> .scripts/ollama-entrypoint.sh
	@echo 'MODEL_NAME=$${OLLAMA_MODEL_NAME:-phi3}' >> .scripts/ollama-entrypoint.sh
	@echo 'echo "Pulling model: $$MODEL_NAME..."' >> .scripts/ollama-entrypoint.sh
	@echo 'ollama pull "$$MODEL_NAME"' >> .scripts/ollama-entrypoint.sh
	@echo 'echo "Warming up model $$MODEL_NAME..."' >> .scripts/ollama-entrypoint.sh
	@echo 'ollama run "$$MODEL_NAME" "Hello" > /dev/null' >> .scripts/ollama-entrypoint.sh
	@echo 'echo "Model $$MODEL_NAME is preloaded and ready."' >> .scripts/ollama-entrypoint.sh
	@echo 'wait' >> .scripts/ollama-entrypoint.sh
	@chmod +x .scripts/ollama-entrypoint.sh


setup-wait-script:
	@echo "Setting up wait-for-phi3 script"
	@mkdir -p .scripts

	@# Read values from .env or use default
	@OLLAMA_HOST=$$(grep -E '^OLLAMA_CLIENT_URL=' .env 2>/dev/null | cut -d '=' -f2 | tr -d '\r'); \
	MODEL_NAME=$$(grep -E '^OLLAMA_MODEL_NAME=' .env 2>/dev/null | cut -d '=' -f2 | tr -d '\r'); \
	[ -z "$$OLLAMA_HOST" ] && OLLAMA_HOST="http://ollama:11434"; \
	[ -z "$$MODEL_NAME" ] && MODEL_NAME="phi3"; \
	echo '#!/bin/sh' > .scripts/wait-for-phi3.sh; \
	echo "OLLAMA_HOST=$$OLLAMA_HOST" >> .scripts/wait-for-phi3.sh; \
	echo "MODEL_NAME=$$MODEL_NAME" >> .scripts/wait-for-phi3.sh; \
	echo 'echo "Waiting for Ollama model '\''$$MODEL_NAME'\'' to be ready..."' >> .scripts/wait-for-phi3.sh; \
	echo 'until curl -s "$$OLLAMA_HOST/api/tags" | grep "$$MODEL_NAME" > /dev/null; do' >> .scripts/wait-for-phi3.sh; \
	echo '  echo "Model $$MODEL_NAME not available yet, waiting 5 seconds..."' >> .scripts/wait-for-phi3.sh; \
	echo '  sleep 5' >> .scripts/wait-for-phi3.sh; \
	echo 'done' >> .scripts/wait-for-phi3.sh; \
	echo 'echo "Model $$MODEL_NAME is ready! Starting rag-app..."' >> .scripts/wait-for-phi3.sh; \
	echo 'exec "$$@"' >> .scripts/wait-for-phi3.sh

	@chmod +x .scripts/wait-for-phi3.sh


stop:
	@echo "Stopping all containers..."
	docker compose -f docker-compose.base.yaml -f docker-compose.ollama.yaml down || true
	docker compose -f docker-compose.base.yaml -f docker-compose.llamacpp.yaml down || true
	@echo "Cleaning up entrypoint scripts"
	@rm -rf .scripts

logs:
	@echo "Streaming logs based on backend..."
	@BACKEND=$$(grep -E '^LLM_BACKEND=' .env 2>/dev/null | cut -d '=' -f2 | tr -d '\r' || echo "OLLAMA_BACKEND"); \
	if [ "$$BACKEND" = "OLLAMA_BACKEND" ]; then \
		docker compose -f docker-compose.base.yaml -f docker-compose.ollama.yaml logs -f; \
	elif [ "$$BACKEND" = "LLAMA_CPP_BACKEND" ]; then \
		docker compose -f docker-compose.base.yaml -f docker-compose.llamacpp.yaml logs -f; \
	else \
		echo "Unknown backend: $$BACKEND. Use OLLAMA_BACKEND or LLAMA_CPP_BACKEND"; \
		exit 1; \
	fi

test:
	pytest --cov=src --cov-report=term-missing

create:
	docker build -t research_agent-rag-app:latest .
	docker save -o research_agent_image.tar research_agent-rag-app:latest

clean:
	@echo "Cleaning up containers, images, and volumes..."
	docker compose -f docker-compose.base.yaml -f docker-compose.ollama.yaml down -v || true
	docker compose -f docker-compose.base.yaml -f docker-compose.llamacpp.yaml down -v || true
	docker image rm research_agent-rag-app:latest || true
	docker image prune -f
	@echo "Cleaning up entrypoint scripts"
	@rm -rf .scripts