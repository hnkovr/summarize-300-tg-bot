
install:
	python -m venv .venv &&\
	source .venv/bin/activate &&\
	pip install -r requirements.txt

run:
	clear
	set -ex
	python app/main.py

run2:
	clear
	set -ex
	python app/main2.py

