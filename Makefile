# AssetDNA Makefile for Docker operations

.PHONY: help build up down restart logs shell clean migrate test

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "AssetDNA Docker Management"
	@echo "=========================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${GREEN}%-15s${NC} %s\n", $$1, $$2}'
	@echo ""
	@echo "Ports:"
	@echo "  ${YELLOW}10001${NC} - Main Application"
	@echo "  ${YELLOW}10432${NC} - PostgreSQL"
	@echo "  ${YELLOW}10379${NC} - Redis"
	@echo "  ${YELLOW}10050${NC} - pgAdmin"
	@echo "  ${YELLOW}10080${NC} - Nginx HTTP"
	@echo "  ${YELLOW}10443${NC} - Nginx HTTPS"

build: ## Build all containers
	@echo "${YELLOW}Building containers...${NC}"
	docker-compose build

up: ## Start all services
	@echo "${GREEN}Starting AssetDNA...${NC}"
	docker-compose up -d
	@echo "${GREEN}Services started!${NC}"
	@echo ""
	@echo "Access points:"
	@echo "  Main App:  http://localhost:10001"
	@echo "  pgAdmin:   http://localhost:10050"
	@echo "  API Docs:  http://localhost:10001/docs"

down: ## Stop all services
	@echo "${YELLOW}Stopping AssetDNA...${NC}"
	docker-compose down

restart: ## Restart all services
	@echo "${YELLOW}Restarting AssetDNA...${NC}"
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-app: ## Show logs from app only
	docker-compose logs -f assetdna

shell: ## Open shell in app container
	docker-compose exec assetdna /bin/bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U assetdna -d assetdna

migrate: ## Run database migrations
	@echo "${YELLOW}Running migrations...${NC}"
	docker-compose exec assetdna alembic upgrade head

clean: ## Clean up volumes and containers
	@echo "${RED}Warning: This will delete all data!${NC}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "${GREEN}Cleanup complete${NC}"; \
	fi

status: ## Show status of all services
	@echo "${YELLOW}Service Status:${NC}"
	@docker-compose ps

test: ## Run tests
	@echo "${YELLOW}Running tests...${NC}"
	docker-compose exec assetdna pytest

backup: ## Backup database
	@echo "${YELLOW}Backing up database...${NC}"
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U assetdna assetdna > backups/assetdna_$$(date +%Y%m%d_%H%M%S).sql
	@echo "${GREEN}Backup saved to backups/assetdna_$$(date +%Y%m%d_%H%M%S).sql${NC}"

restore: ## Restore database from backup
	@echo "${YELLOW}Available backups:${NC}"
	@ls -la backups/*.sql
	@read -p "Enter backup filename: " backup; \
	docker-compose exec -T postgres psql -U assetdna assetdna < $$backup