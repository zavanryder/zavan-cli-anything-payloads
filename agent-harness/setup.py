from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-payloads",
    version="1.0.0",
    description="CLI harness for PayloadsAllTheThings — search, extract, and export security payloads",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-payloads=cli_anything.payloads.payloads_cli:main",
        ],
    },
    python_requires=">=3.10",
)
