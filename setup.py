from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="webfly",
    version="1.0.0",
    author="Anonymous-beta & Victor410fer",
    description="Aggressive Web Reconnaissance & Exploitation Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/anonymous-beta/WebFly",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "aiofiles>=0.8.0",
        "beautifulsoup4>=4.10.0",
        "colorama>=0.4.4",
        "fastapi>=0.85.0",
        "uvicorn>=0.18.0",
        "pydantic>=1.10.0",
        "pyyaml>=6.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "webfly=webfly.cli:main",
        ],
    },
)
