all:
	python setup.py build_ext --inplace

valgrind:
	pvalgrind python runtests.py

clean:
	python setup.py clean
