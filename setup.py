"""
Setup script for SecureAttend

This helps with proper package installation and path resolution.
"""

from setuptools import setup, find_packages

setup(
    name="secureattend",
    version="0.1.0",
    description="PKI-based access control and attendance system",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "cryptography>=41.0.0",
        "qrcode[pil]>=7.4.2",
        "click>=8.1.7",
        "requests>=2.31.0",
    ],
)
