.PHONY: dev setup-entrypoint prepare-dirs setup-wait-script stop logs test create clean
dev: setup-entrypoint prepare-dirs setup-wait-script
	docker compose up --build

prepare-dirs:
	@echo "🛠️  Creating necessary data directories with correct permissions"
	@for dir in logs chroma_store models sample_data; do \
		if [ ! -d $$dir ]; then \
			echo "📁 Creating $$dir"; \
			mkdir -p $$dir; \
		else \
			echo "✅ $$dir already exists"; \
		fi; \
		chmod -R 775 $$dir; \
	done


setup-entrypoint:
	@echo "🛠️  Setting up Ollama entrypoint scripts"
	@mkdir -p .scripts
	@echo '#!/bin/sh' > .scripts/ollama-entrypoint.sh
	@echo 'ollama serve &' >> .scripts/ollama-entrypoint.sh
	@echo 'until ollama list >/dev/null 2>&1; do' >> .scripts/ollama-entrypoint.sh
	@echo '  echo "Waiting for Ollama server to respond..."' >> .scripts/ollama-entrypoint.sh
	@echo '  sleep 1' >> .scripts/ollama-entrypoint.sh
	@echo 'done' >> .scripts/ollama-entrypoint.sh
	@echo 'ollama pull phi3' >> .scripts/ollama-entrypoint.sh
	@echo 'wait' >> .scripts/ollama-entrypoint.sh
	@chmod +x .scripts/ollama-entrypoint.sh

setup-wait-script:
	@echo "🛠️  Setting up wait-for-phi3 script"
	@mkdir -p .scripts
	@echo '#!/bin/sh' > .scripts/wait-for-phi3.sh
	@echo 'OLLAMA_HOST=$${OLLAMA_CLIENT_URL:-http://ollama:11434}' >> .scripts/wait-for-phi3.sh
	@echo 'MODEL_NAME=$${OLLAMA_MODEL_NAME:-phi3}' >> .scripts/wait-for-phi3.sh
	@echo 'echo "Waiting for Ollama model '\''$$MODEL_NAME'\'' to be ready..."' >> .scripts/wait-for-phi3.sh
	@echo 'until curl -s "$$OLLAMA_HOST/api/models" | grep "$$MODEL_NAME" > /dev/null; do' >> .scripts/wait-for-phi3.sh
	@echo '  echo "Model $$MODEL_NAME not available yet, waiting 5 seconds..."' >> .scripts/wait-for-phi3.sh
	@echo '  sleep 5' >> .scripts/wait-for-phi3.sh
	@echo 'done' >> .scripts/wait-for-phi3.sh
	@echo 'echo "Model $$MODEL_NAME is ready! Starting rag-app..."' >> .scripts/wait-for-phi3.sh
	@echo 'exec "$$@"' >> .scripts/wait-for-phi3.sh
	@chmod +x .scripts/wait-for-phi3.sh

stop:
	docker compose down
	@echo "Cleaning up entrypoint scripts"
	@rm -rf .scripts  

logs:
	docker compose logs -f

test:
	pytest --cov=src --cov-report=term-missing

create:
	docker build -t ra_agent-rag-app:latest .
	docker save -o ra_agent_image.tar ra_agent-rag-app:latest

clean:
	docker compose down -v
	docker image rm ra_agent-rag-app:latest || true
	docker image prune -f
	@echo "Cleaning up entrypoint scripts"
	@rm -rf .scripts   