from setuptools import setup, find_packages

setup(
    name="vector_search",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sentence-transformers==2.5.1",
        "faiss-cpu==1.7.4",
        "numpy>=1.24.0",
        "torch>=2.0.0",
    ],
    python_requires=">=3.8",
) 