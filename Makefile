.PHONY: start stop restart status logs clean

# Default target when you just type 'make'
all: status

start:
	@./scripts/start.sh

stop:
	@./scripts/stop.sh

restart: stop start

status:
	@./scripts/status.sh

# View live logs of all services simultaneously
logs:
	@tail -f logs/*.log

# Clean up logs and temporary state files
clean: stop
	@echo "🧹 Cleaning up logs and state files..."
	@rm -rf logs/*
	@rm -rf .pids/*
	@rm -f langgraph_checkpoints.sqlite
	@echo "Clean complete."