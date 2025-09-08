from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="screentime2notion",
    version="1.0.0",
    author="Felipe Icarus",
    author_email="felipe@icarus.com",
    description="Sync macOS Screen Time data to Notion with weekly aggregation and smart categorization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/screentime2notion",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/screentime2notion/issues",
        "Source": "https://github.com/yourusername/screentime2notion",
        "Documentation": "https://github.com/yourusername/screentime2notion#readme",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["config/*.json"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Utilities",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=[
        "notion-client>=2.0.0",
        "pandas>=2.0.0",
        "click>=8.0.0",
        "python-dotenv>=1.0.0",
        "pytz>=2023.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-mock>=3.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "screentime2notion=src.main:cli",
        ],
    },
    keywords="screentime, notion, macos, productivity, tracking, automation",
)