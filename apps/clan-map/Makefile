.PHONY: help build run stop clean test dev docker-build docker-run docker-stop

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Run development server
	python app.py

build: ## Build Docker image
	docker build -t clan-map:latest .

run: build ## Build and run Docker container
	docker run -d --name clan-map -p 5010:5010 clan-map:latest
	@echo "🚀 Application running at http://localhost:5010"

stop: ## Stop and remove Docker container
	docker stop clan-map 2>/dev/null || true
	docker rm clan-map 2>/dev/null || true

clean: stop ## Clean up Docker resources
	docker rmi clan-map:latest 2>/dev/null || true

test: ## Run basic tests
	python -c "import app; import map_generator; print('✅ All imports successful')"

compose-up: ## Start with docker-compose
	docker-compose up -d
	@echo "🚀 Application running at http://localhost:5010"

compose-down: ## Stop docker-compose services
	docker-compose down

logs: ## Show container logs
	docker logs clan-map -f 2>/dev/null || docker-compose logs -f

install: ## Install dependencies
	pip install -r requirements.txt

freeze: ## Update requirements.txt
	pip freeze > requirements.txt
