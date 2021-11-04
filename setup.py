import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyAEMET-Jaimedgp",
    version="0.0.1",
    author="Jaime Diez",
    author_email="jaime.diez.gp@gmail.com",
    description="Python package to interact with the AEMET API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Jaimedgp/pyAEMET",
    project_urls={
        "Bug Tracker": "https://github.com/Jaimedgp/pyAEMET/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires = [
        #"setuptools>=42",
        #"wheel",
        "numpy>=1.18.1",
        "pandas>=1.0.1",
        "requests>=2.7.0",
        "geocoder>=1.38.1",
        #"python-dateutil>=2.7.0",
    ],
    #package_dir={"": "pyaemet"},
    packages=setuptools.find_packages(include=['pyaemet']),
    python_requires=">=3.6",
    zip_safe=False,
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='pyaemet.tests',
)
