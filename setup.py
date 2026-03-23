import sys
import os
from setuptools import setup, Extension
import pybind11

if sys.platform == "win32":
    cpp_args = ['/openmp', '/O2', '/EHsc', '/std:c++17']
    link_args = ['/openmp']
else:
    cpp_args = ['-fopenmp', '-O3', '-std=c++17']
    link_args = ['-fopenmp']

ext_modules = [
    Extension(
        'monte_carlo_cpp',
        ['cpp/monte_carlo.cpp'],
        include_dirs=[pybind11.get_include()],
        language='c++',
        extra_compile_args=cpp_args,
        extra_link_args=link_args,
    ),
]

setup(
    name='monte_carlo_cpp',
    version='2.1',
    ext_modules=ext_modules,
    zip_safe=False,
)