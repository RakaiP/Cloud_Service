from setuptools import setup, find_packages

setup(
    name="cloudservice-client",
    version="0.1.0",
    description="Client SDK for Cloud File Service",
    author="Rakai Andaru Priandra",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
    ],
    python_requires=">=3.7",
)
