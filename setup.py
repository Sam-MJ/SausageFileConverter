from Cython.Build import cythonize
from setuptools import setup

modules = [
    "mainwindow.py",
    "metadata_v2.py",
    "worker.py",
    "telem.py",
]

setup(ext_modules=cythonize(modules))
