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
        "License :: OSI Approved :: GNU General Public License v3.0",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "pyaemet"},
    packages=setuptools.find_packages(where="pyaemet"),
    python_requires=">=3.6",
)
