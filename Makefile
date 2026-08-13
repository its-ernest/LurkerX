.PHONY: help build up down logs apk clean validate-build validate-up validate-down validate-logs

IMAGE := lurkerx
VALIDATION_IMAGE := lurkerx-validation

help:
	@echo "Usage:"
	@echo "  make build             - Build server image"
	@echo "  make up                - Start all services (server + validation)"
	@echo "  make down              - Stop all services"
	@echo "  make logs              - Tail all service logs"
	@echo "  make logs-server       - Tail server logs"
	@echo "  make logs-validation   - Tail validation logs"
	@echo "  make apk               - Rebuild APK inside server container"
	@echo "  make clean             - Stop services and remove containers/images"
	@echo "  make validate-build    - Build validation service image"
	@echo "  make validate-up       - Start validation service only"
	@echo "  make validate-down     - Stop validation service"
	@echo "  make validate-logs     - Tail validation logs"

build:
	docker compose build server

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

logs-server:
	docker compose logs -f server

logs-validation:
	docker compose logs -f validation

apk:
	docker compose exec server python -m packager

validate-build:
	docker compose build validation

validate-up:
	docker compose up -d --build validation

validate-down:
	docker compose stop validation
	docker compose rm -f validation

validate-logs:
	docker compose logs -f validation

clean:
	docker compose down -v
	-docker rmi $(IMAGE)
	-docker rmi $(VALIDATION_IMAGE)
