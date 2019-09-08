#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup


with open("README.rst") as readme_file:
    readme = readme_file.read()

requirements = [
    "Adafruit-PCA9685>=1.0.1",
    "adafruit-circuitpython-pca9685>=3.2.5",
    "Click>=7.0",
    "RPi.GPIO>=0.7.0",
    "pygame>=1.9.6",
]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]

setup(
    author="Ellen Juhlin",
    author_email="elj@users.noreply.github.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Liftaway Project",
    # entry_points={"console_scripts": ["liftaway=liftaway.cli:main"]},
    entry_points={"console_scripts": ["liftaway=liftaway.lift_main:main"]},
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords="liftaway",
    name="liftaway",
    packages=find_packages(),
    package_data={"liftaway": ["data/*.wav"]},
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/elj/liftaway",
    version="0.1.0",
    zip_safe=False,
)
