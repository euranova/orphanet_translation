from setuptools import setup, find_packages

exec(open('orphanet_translation/version.py').read())

setup(
    name="orphanet_translation",
    version=__version__,
    packages=find_packages(),

    description="",
    keywords="biomedical, ontology, translation, wikidata, orphanet",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
