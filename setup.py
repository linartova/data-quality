from setuptools import setup

setup(
    name="mmci_convertor",
    version="1.0.0",
    description="""
        Convertion tool for the MMCI CRC-cohort data.
        The input is xml file and access data to FHIR server and OMOP database.
        The output is quality control of data and conversion of data to provided FHIR server and OMOP database.
        The tool provide guidance user interface.
    """,
    author="Martina Linartová",
    author_email="martina.linartova@gmail.com",
    packages=["mmci_convertor"],
    install_requires=[
        "psycopg2",
        "fhirclient",
        "reportlab",
        "pandas",
        "plotly",
        "flask"
    ],
)
