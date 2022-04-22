import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyaemet",
    version="1.0.2",
    author="Jaimedgp",
    author_email="jaime.diez.gp@gmail.com",
    description="Python package to interact with the AEMET API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='AEMET, Meteorology, API, AEMET OpenData',
    url="https://pypi.org/project/pyaemet/",
    project_urls={
        "Source": "https://github.com/Jaimedgp/pyAEMET",
        "Bug Tracker": "https://github.com/Jaimedgp/pyAEMET/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires = [
        "setuptools>=42",
        "wheel",
        "numpy",
        "pandas",
        "requests",
        "geocoder",
        "python-dateutil",
    ],
    # include=['pyaemet',
    #          'pyaemet.types_classes',
    #          'pyaemet.utilities']
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={'pyaemet': ['data/*.*', 'data/*/*.*']},
    python_requires=">=3.6",
    zip_safe=False,
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='pyaemet.tests',
)
