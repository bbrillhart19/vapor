#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="vapor",
    version="0.0.1",
    description="Personalized AI Companion for Steam",
    author="Brett Brillhart",
    author_email="bbrillhart19@gmail.com",
    url="https://github.com/bbrillhart19/vapor",
    install_requires=[
        "python-steam-api",
        "chromadb",
        "networkx",
        "asyncio",
    ],
    extras_require={
        "dev": [
            "black",
            "pytest",
            "pytest-coverage",
        ]
    },
    packages=find_packages(),
)
