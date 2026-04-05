activate:
	. .venv/bin/activate
clean:
	rm -rf __pycache__ .venv
install: venv activate
	.venv/bin/pip install -e .
run:
	.venv/bin/echo-protocol-generate
check:
	python3 -m echo_run.cli --check
test:
	python3 -m unittest discover -s tests -v
venv:
	python3 -m venv .venv
