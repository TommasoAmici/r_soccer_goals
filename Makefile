.PHONY: venv test venv_clean

BIN = .venv/bin
PY = ${BIN}/python -B
PIP_INSTALL = ${BIN}/pip install
PYTEST = ${PY} -m pytest

venv: .venv/touchfile

# touching a file makes it possible to run this rule only when requirements.txt changes
.venv/touchfile: requirements.txt requirements_test.txt requirements_dev.txt
	[ -d .venv ] || python3 -m venv .venv
	${PIP_INSTALL} --upgrade pip wheel
	${PIP_INSTALL} -r requirements.txt
	${PIP_INSTALL} -r requirements_test.txt
	${PIP_INSTALL} -r requirements_dev.txt
	touch .venv/touchfile

venv_clean:
	[ -d .venv ] && rm -rf .venv

test: venv
	${PYTEST} tests.py $(args)

# run tests and drop into a console on the first fail
test_debug: venv
	${PYTEST} tests.py -x --pdb $(args)

build:
	docker build -t r_soccer_goals .

run: venv
	${PY} main.py
