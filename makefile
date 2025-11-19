activate:
	. .venv/bin/activate
clean:
	rm -rf __pycache__ .venv
install: venv activate
	pip install -r requirements.txt
venv:
	python3 -m venv .venv