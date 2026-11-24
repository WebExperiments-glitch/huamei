"""Huamei 安装脚本。"""
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="huamei",
    version="0.1.0",
    description="A unified dialogue data refinery with a three-level tower and anti-AI-tone judge",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pyarrow>=14.0",
        "pyyaml>=6.0",
        "datatrove>=0.10",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
