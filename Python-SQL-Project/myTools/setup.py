import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="myTools-r.adamczyk",
    version="0.0.1",
    author="Raphaël Adamczyk",
    author_email="raphael.adamczyk@edu.dsti.institute",
    description="myTools offers utility classes and functions for dealing with the DSTI combined SQL & Python project",
    url="",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
)
