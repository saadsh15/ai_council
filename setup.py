from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open("requirements.txt") as f:
    requirements = [
        line.strip() for line in f.read().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="the-council",
    version="0.1.0",
    author="The Council Team",
    description="Multi-Agent AI Research Terminal Application",
    packages=find_packages(),
    py_modules=["main"],
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "the-council=main:main",
        ],
    },
    python_requires=">=3.11",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
)
