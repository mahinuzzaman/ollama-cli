from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="olla-cli",
    version="0.1.0",
    author="Mahinuzzaman",
    author_email="",
    description="A coding assistant command line tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mahinuzzaman/ollama-cli",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
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
        "pyyaml>=6.0",
        "ollama>=0.2.0",
        "aiohttp>=3.8.0",
        "prompt_toolkit>=3.0.0",
        "pygments>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "olla-cli=olla_cli.cli:main",
        ],
    },
)