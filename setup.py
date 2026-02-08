"""Setup script for Canvas CLI."""

from setuptools import setup, find_packages

setup(
    name="canvas-cli",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
        "pyyaml>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "canvas=canvas_cli.cli:main",
        ],
    },
    author="Canvas CLI Contributors",
    description="Faculty-friendly CLI for pulling and pushing Canvas LMS content with Codex workflows",
    url="https://github.com/Brehove/canvas-cli-for-codex",
    license="MIT",
    python_requires=">=3.9",
)
