.PHONY: cythonize clean_c_files move_py_files pyinstaller_pc pyinstaller_mac clean_pyd_files move_back_py_files all

pc: cythonize clean_c_files move_py_files pyinstaller_pc clean_pyd_files move_back_py_files

mac: cythonize clean_c_files move_py_files pyinstaller_mac clean_pyd_files move_back_py_files

cythonize:
	python setup.py build_ext --inplace

clean_c_files:
	$(RM) src/*.c

files = mainwindow.py metadata_v2.py telem.py worker.py
move_py_files:
	for file in $(files); do \
		mv src/$$file "build"; \
	done

pyinstaller_mac:
	pyinstaller mac_onefile_app.spec

pyinstaller_pc:
	pyinstaller app-custom.spec

clean_pyd_files:
	$(RM) src/*.pyd
	$(RM) src/*.so

move_back_py_files:
	for file in $(files); do \
		mv build/$$file "src"; \
	done
