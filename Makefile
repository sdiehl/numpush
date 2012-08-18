all:
	python setup.py build_ext --inplace --debug

valgrind:
	pvalgrind python runtests.py

clean:
	python setup.py clean
