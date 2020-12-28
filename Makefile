
.PHONY: test 
test:
	env PYTHONPATH="." pytest-3 -s unit_tests 

.PHONY: run
run:
	export FLASK_APP=gomoku_app.py
	flask run

.PHONY: open
open:
	xdg-open http://127.0.0.1:5000

