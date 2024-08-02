from Cython.Build import cythonize
from setuptools import setup

modules = [
    "src/mainwindow.py",
    "src/metadata_v2.py",
    "src/worker.py",
    "src/telem.py",
    "src/file_tree.py",
]

setup(ext_modules=cythonize(modules))
