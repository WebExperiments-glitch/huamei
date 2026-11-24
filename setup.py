"""Huamei install script.

Layout note: the repository root itself is the `huamei` package (it contains __init__.py).
We map it explicitly so `pip install -e .` exposes it correctly.
"""
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

subpackages = find_packages(exclude=["tests", "tests.*"])
# find_packages() skips the repo root; add it explicitly via package_dir mapping
packages = ["huamei"] + ["huamei." + p for p in subpackages]

setup(
    name="huamei",
    version="0.1.0",
    description="A unified dialogue data refinery with a three-level tower and anti-AI-tone judge",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=packages,
    package_dir={"huamei": "."},
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
