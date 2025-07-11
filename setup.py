from setuptools import setup, find_packages
import os

# 读取 README 文件
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 读取 requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="archdash",
    version="1.1.0",
    author="Your Name",  # 请替换为您的名字
    author_email="your.email@example.com",  # 请替换为您的邮箱
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
            "*.md",
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