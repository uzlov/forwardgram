# Create .env and docker-compose.override.yml files, if they not exists.
$(shell cp -n \.env.default \.env)
$(shell cp -n \.\/docker-compose\.override\.default\.yml \.\/docker-compose\.override\.yml)

include .env

# Get local values only once.
LOCAL_UID := $(shell id -u)
LOCAL_GID := $(shell id -g)

# Evaluate recursively.
CUID ?= $(LOCAL_UID)
CGID ?= $(LOCAL_GID)

# Network name is sanitized.
COMPOSE_NET_NAME := $(shell echo $(COMPOSE_PROJECT_NAME) | tr '[:upper:]' '[:lower:]'| sed -E 's/[^a-z0-9]+//g')_front

.PHONY: include session up down rebuild stop restart exec

all: | include down up

include:
ifeq ($(strip $(COMPOSE_PROJECT_NAME)), projectname)
$(error Project name can not be default, please edit ".env" and set COMPOSE_PROJECT_NAME variable.)
endif

up:
	docker-compose up -d --remove-orphans --force-recreate

down:
	@echo "Removing containers for $(COMPOSE_PROJECT_NAME)"
	docker-compose down -v --remove-orphans

rebuild: down
	docker-compose up -d --remove-orphans --build

stop:
	docker-compose stop app

restart:
	docker-compose restart app

ifeq (exec,$(firstword $(MAKECMDGOALS)))
  EXEC_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(EXEC_ARGS):;@:)
endif

exec:
	docker-compose exec -u$(CUID):$(CGID) $(EXEC_ARGS) sh
