from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    more_description = f.read()

setup(
    name='AcquityFileParser',
    version='0.0.1',
    description='A python package for parsing water data',
    package_dir={"":"AcquityFileParser"},
    packages=find_packages(where="AcquityFileParser"),
    author='NickFlores',
    author_email="nick.flores1993@gmail.com",
    license='MIT',
    install_requires=["pydantic>=2.7.4","setuptools>=70.0.0","pandas>=2.2.2","numpy>=2.0.0","scipy>=1.14.0",
    ],
    python_requires='>=3.10',
)