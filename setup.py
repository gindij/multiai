from setuptools import setup, find_packages

setup(
    name="multi-ai",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    description="Compare responses from multiple AI models",
    author="jackgindi",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "python-dotenv>=1.0.0",
        "openai>=1.3.5",
        "anthropic",
        "jinja2",
        "pydantic>=2.4.2",
        "httpx>=0.25.1",
        "markdown2",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
