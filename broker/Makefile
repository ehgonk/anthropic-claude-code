.PHONY: setup backend frontend seed clean build-frontend

# Setup
setup: setup-backend setup-frontend

setup-backend:
	cd backend && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt

setup-frontend:
	cd frontend && npm install

# Run
backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

frontend:
	cd frontend && npm run dev

# Seed demo data
seed:
	cd backend && .venv/bin/python3 -m app.seed

# Build
build-frontend:
	cd frontend && npm run build

# Screenshot
screenshot:
	cd frontend && npm run screenshot

# Clean
clean:
	rm -rf backend/.venv frontend/node_modules data/*.db backend/__pycache__ backend/app/__pycache__
