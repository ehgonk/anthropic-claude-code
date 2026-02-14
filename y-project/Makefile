.PHONY: setup backend frontend seed clean

# === Setup completo ===
setup: setup-backend setup-frontend

setup-backend:
	cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt

setup-frontend:
	cd frontend && npm install

# === Rodar ===
backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# === Dados ===
seed:
	cd backend && .venv/bin/python -m app.seed

# === Build ===
build-frontend:
	cd frontend && npm run build

# === Limpar ===
clean:
	rm -rf backend/.venv frontend/node_modules data/raw data/processed *.db backend/*.db
