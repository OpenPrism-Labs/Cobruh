#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="lightning-cobruh-template",
    version="0.1.0",
    description="A template for PyTorch Lightning projects using Cobruh for configuration",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/lightning-cobruh-template",
    install_requires=["lightning", "cobruh"],
    packages=find_packages(),
    # use this to customize global commands available in the terminal after installing the package
    entry_points={
        "console_scripts": [
            "train_command = src.train:main",
            "eval_command = src.eval:main",
        ]
    },
)
