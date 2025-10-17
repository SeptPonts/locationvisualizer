.PHONY: install
install:
	uv sync
	uv run pre-commit install

.PHONY: run
run:
	uv run python src/main.py

.PHONY: format
format:
	uv run ruff format src/
	uv run ruff check --fix src/

.PHONY: lint
lint:
	@echo "Checking code formatting..."
	uv run ruff format --check src/
	uv run ruff check src/
	@echo "Code formatting is correct!"

.PHONY: geocode
geocode:
	uv run python src/geocode.py data/hotels_sample.csv output/hotels.json

.PHONY: render-map
render-map:
	uv run python src/render_map.py

.PHONY: serve
serve:
	@echo "启动本地服务器..."
	@echo "访问: http://localhost:8000/web/map.html"
	python -m http.server 8000