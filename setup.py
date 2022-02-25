#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup

__PATH__ = os.path.abspath(os.path.dirname(__file__))


def read_readme():
    with open("README.md") as f:
        readme_string = f.read()
    src_img_path = """<img src="./docs/npustat.png" width="80%" height="80%" alt="npustat png" align=center />"""
    tar_img_path = """<img src="https://user-images.githubusercontent.com/50796589/147898619-79ada678-6709-48f2-bdb5-9366f0db2ee0.png" width="80%" height="80%" alt="npustat png" align=center />"""
    readme_string = re.sub(src_img_path, tar_img_path, readme_string)
    return readme_string


def read_version():
    # importing npustat causes an ImportError :-)
    __PATH__ = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(__PATH__, "npustat/__init__.py")) as f:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  f.read(), re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find __version__ string")


__version__ = read_version()
print(f"version: {__version__}")

setup_requires = []

install_requires = [
    "six>=1.7",
    "blessed>=1.17.1",  # GH-126
]

setup(
    name="npustat",
    version=__version__,
    license="MIT",
    description="An utility to monitor Huawei Atlas status and usage",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/wmc1992/npustat",
    author="wmc1992",
    author_email="m18810541081@163.com",
    keywords="atlas npu monitoring npustat",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Monitoring",
    ],
    packages=["npustat"],
    install_requires=install_requires,
    setup_requires=setup_requires,
    entry_points={
        "console_scripts": ["npustat=npustat:main"],
    },
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.6",
)
