#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="otter-transcript-downloader", 
    version="1.0.0",
    author="Nick Sullivan",
    author_email="nick@carmentacollective.com",
    description="Beautiful CLI tool for downloading and organizing Otter.ai transcripts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nicksullivan/otter-download",  # Update with actual URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop", 
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Office/Business",
        "Topic :: Text Processing",
        "Topic :: Utilities",
    ],
    keywords="otter.ai transcripts download cli automation",
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0", 
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
    entry_points={
        "console_scripts": [
            "otter-cli=otter_cli.main:cli",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/nicksullivan/otter-download/issues",
        "Source": "https://github.com/nicksullivan/otter-download",
    },
)
