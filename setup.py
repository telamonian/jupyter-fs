# *****************************************************************************
#
# Copyright (c) 2019, the jupyter-fs authors.
#
# This file is part of the jupyter-fs library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.

from jupyter_packaging import (
    combine_commands,
    create_cmdclass,
    ensure_python,
    ensure_targets,
    get_version,
    install_npm,
    skip_if_exists
)
from pathlib import Path
import setuptools

ensure_python(('>=3.6',))

# project name is also name of labextension npm package
name = labext_name = 'jupyter-fs'
# relative paths to python pkg dir and labextension pkg dir
js_pkg, py_pkg = Path('js'), Path('jupyterfs')
# relative path to labextension dist that gets built at the root of the python package
labext_dist = py_pkg/'labextension'
# Representative files that should exist after a successful build
jstargets = [labext_dist/"package.json"]
version = get_version(str(py_pkg / '_version.py'))
# POSIX_PREFIX/APP_SUFFIX determines the install location of the labextension dist
APP_SUFFIX = Path('share/jupyter/labextensions/')
# POSIX_PREFIX/CON_SUFFIX determines the install location of the labextension dist
APP_SUFFIX = Path('share/jupyter/labextensions/')

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

data_files_spec = [
    # distribute the labextension dist via the data_files of the python package
    (str(SUFFIX/labext_name), str(labext_dist), '**'),
    # include a record of installation method (ie pip) in the labextension install
    (str(SUFFIX/labext_name), '.', 'install.json')
    # config to enable server extension 'for free' on normal pip install:
    ('etc/jupyter', 'jupyter-config/**/*', '*'),
]
package_data_spec = {name: ["*"]}

cmdclass = create_cmdclass("jsdeps",
    package_data_spec=package_data_spec,
    data_files_spec=data_files_spec
)
js_command = combine_commands(
    install_npm(js_pkg, build_cmd='build:labextension', npm=['jlpm']),
    ensure_targets(jstargets),
)
cmdclass["jsdeps"] = js_command if Path(".git").exists() else skip_if_exists(jstargets, js_command)

requires = [
    'fs>=2.4.11',
    'fs-s3fs>=1.1.1',
    'fs.smbfs>=0.6.3',
    'jupyterlab>=3.0.0',
    'jupyter_server>=1.8.0',
]

test_requires = [
    'boto3',
    'docker',
    'fs-miniofs',
    'mock',
    'pysmb',
    'pytest',
    'pytest-cov',
]

dev_requires = test_requires + [
    'autopep8>=1.5',
    'bump2version>=1.0.0',
    'flake8>=3.7.8',
    'mock',
    'pytest',
    'pytest-cov>=2.6.1',
    'pytest-xdist',
    'Sphinx>=1.8.4',
    'sphinx-markdown-builder>=0.5.2',
]


with open('README.md', 'r') as fh:
    long_description = fh.read()

setup_args = dict(
    name=name,
    version=version,
    description='A Filesystem-like mult-contents manager backend for Jupyter',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jpmorganchase/jupyter-fs',
    author='jupyter-fs authors',
    license='Apache 2.0',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Framework :: Jupyter',
    ],
    cmdclass=cmdclass,
    keywords='jupyter jupyterlab',
    packages=setuptools.find_packages(exclude=('js', 'js.*')),
    install_requires=requires,
    extras_require={'dev': dev_requires, 'test': test_requires},
    include_package_data=True,
    zip_safe=False,
)

if __name__ == '__main__':
    setuptools.setup(**setup_args)
