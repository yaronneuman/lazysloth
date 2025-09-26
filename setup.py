#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fastparrot",
    version="1.0.0",
    author="Yaron Neuman",
    author_email="",
    description="CLI-first application for sharing and learning terminal shortcuts and aliases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yaronneuman/fastparrot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "colorama>=0.4.4",
        "watchdog>=2.1.0",
        "psutil>=5.8.0",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "fastparrot=fastparrot.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "fastparrot": ["shells/*.sh", "shells/*.fish", "shells/*.zsh"],
    },
)