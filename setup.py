#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

# 读取 README 文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取 requirements
requirements = [
    "dash>=2.0.0",
    "dash-bootstrap-components==2.0.3", 
    "dash-ace",
    "pandas>=1.0.0",
    "plotly>=5.0.0",
    "numpy>=1.20.0",
]

setup(
    name="archdash",
    version="0.0.1",
    author="readm",
    author_email="assasaki@163.com",
    description="A powerful architectural calculation tool for building and analyzing complex calculation graphs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Readm/ArchDash",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers", 
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Dash",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "archdash": [
            "assets/*",
        ],
    },
    entry_points={
        "console_scripts": [
            "archdash=archdash.app:main",
        ],
    },
    keywords="dash, visualization, calculation, architecture, graph, analysis",
    project_urls={
        "Bug Reports": "https://github.com/Readm/ArchDash/issues",
        "Source": "https://github.com/Readm/ArchDash",
        "Documentation": "https://github.com/Readm/ArchDash/blob/main/README.md",
    },
)