"""
Setup script for MOT OCR System.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# Remove comments and empty lines
requirements = [req for req in requirements if req and not req.startswith('#')]

setup(
    name="mot-ocr-system",
    version="1.0.0",
    author="MOT OCR Team",
    author_email="contact@motocr.com",
    description="High-accuracy MOT reminder data extraction using Vision-Language Models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kaiteddy/MOTCHECK",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.4.0",
            "mkdocstrings>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mot-ocr=src.api.main:main",
            "mot-ocr-test=test_system:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords=[
        "ocr", "vision", "language-models", "mot", "automotive", 
        "text-extraction", "ai", "machine-learning", "dvla"
    ],
    project_urls={
        "Bug Reports": "https://github.com/kaiteddy/MOTCHECK/issues",
        "Source": "https://github.com/kaiteddy/MOTCHECK",
        "Documentation": "https://github.com/kaiteddy/MOTCHECK/blob/main/docs/api_documentation.md",
    },
)
