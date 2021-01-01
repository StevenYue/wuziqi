
.PHONY: test 
test:
	env PYTHONPATH="." pytest-3 -s unit_tests 

.PHONY: run
run:
	./main.py

.PHONY: open
open:
	xdg-open http://127.0.0.1:5000

