import os
import platform
import sys

import warnings

try:
    import setuptools
    from setuptools import setup
except ImportError:
    setuptools = None
    from distutils.core import setup

kwargs = {}

with open('chipmunks/__init__.py') as f:
    ns = {}
    exec(f.read(), ns)
    version = ns['version']

with open('README.md') as f:
    kwargs['long_description'] = f.read()

if setuptools is not None:
    python_requires = ">= 3.5"
    kwargs['python_requires'] = python_requires

setup(
    name = 'chipmunks',
    version = version,
    packages = ['chipmunks', 'chipmunks.test'],
    package_data = {
        'chipmunks': ['nginx_localtion.jinja'],
        'chipmunks.test': ['conf.d/ucenter.conf', 'ucenter_generated.conf', 'mconf.d/.gitkeep', 'nginx_mock.pid'],
    },
    author = 'Galilio',
    author_email = '514058722@qq.com',
    url = 'http://git.lingmao.tech/xiaoym/chipmunks',
    description = (
        'Chipmunks is lightweight api gateway based on nginx.'
    ),
    install_requires = [
        "Jinja2>=2.11.2",
        "etcd3>=0.12.0",
        "docker>=4.3.1"
    ],
    entry_points = {
        'console_scripts': ['munks=chipmunks.cli:main']
    },
    **kwargs
)