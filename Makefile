dev:
	docker compose up --build

stop:
	docker compose down

logs:
	docker compose logs -f

test:
	pytest --cov=src --cov-report=term-missing

create:
	docker build -t rag-agent:latest .
	docker save -o rag_agent_image.tar rag-agent:latest

clean:
	docker compose down -v
	docker image rm rag-agent:latest || true
	docker image prune -f