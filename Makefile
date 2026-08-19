.PHONY: install index app dashboard evaluate evaluate-llm test clean

# ============================================================
# INSTALL DEPENDENCIES
# ============================================================

install:
	uv sync


# ============================================================
# BUILD / INGEST PRODUCT INDEX
# ============================================================

index:
	uv run python build_index.py


# ============================================================
# RUN SHOPPING ASSISTANT
# ============================================================

app:
	uv run streamlit run app.py


# ============================================================
# RUN MONITORING DASHBOARD
# ============================================================

dashboard:
	uv run streamlit run monitoring_dashboard.py


# ============================================================
# RETRIEVAL EVALUATION
# ============================================================

evaluate:
	uv run python evaluate.py


# ============================================================
# LLM EVALUATION
# ============================================================

evaluate-llm:
	uv run python evaluate_llm.py


# ============================================================
# RUN TESTS
# ============================================================

test:
	uv run pytest


# ============================================================
# CLEAN GENERATED FILES
# ============================================================

clean:
	@echo Cleaning Python cache files...

	@powershell -Command "Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"

	@powershell -Command "Get-ChildItem -Path . -Recurse -File -Filter *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue"