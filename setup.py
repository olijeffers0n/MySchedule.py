from setuptools import setup, find_packages

version = ""
with open("./schedule/__init__.py") as input_file:
    for line in input_file.readlines():
        if line.startswith("__version__"):
            version = line.strip("__version__ =").strip().strip('"')
            break

with open("README.md", errors='ignore') as input_file:
    readme = input_file.read()

setup(
    name='MySchedule.py',
    author='olijeffers0n',
    author_email='pleaseUseMyDiscord@Please.com',
    version=version,
    include_package_data=True,
    packages=find_packages(include=['schedule', 'schedule.*']),
    license='MIT',
    description='A Python wrapper for the McDonalds Myschedule',
    long_description=readme,
    long_description_content_type='text/markdown',
    install_requires=[
        "requests",
        "datetime",
        "bs4",
        "pybase64",
    ],
    python_requires='>=3.7.0',
)
