from setuptools import find_packages, setup
import os

path: str = "requirements.txt"
install_requires = []
if os.path.isfile(path):
    with open(path, "r") as file:
        install_requires = file.read().splitlines()

setup(
    name="btc-mcp",
    version="0.0.1",
    author="Noah Lisin",
    author_email="noah.g.lisin@vanderbilt.edu",
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires=">=3.13",
    package_dir={"": "src"},
    description="Interact with a network of MCP servers without human intervention.",
    url="https://github.com/noahl25/btc-mcp",
    install_requires=install_requires,
)