from spire.pdf.common import *
from spire.pdf import *


def create_pdf_ohdsi():
    # Create a PdfDocument object
    doc = PdfDocument()
    # Load an SVG file
    doc.LoadFromSvg("fig1.svg")

    # Save the SVG file to PDF format
    doc.SaveToFile("OHDSI_report.pdf", FileFormat.PDF)
    # Close the PdfDocument object
    doc.Close()


def create_pdf_fhir():
    # Create a PdfDocument object
    doc = PdfDocument()
    # Load an SVG file
    doc.LoadFromSvg("con_comp_fhir.svg")

    # Save the SVG file to PDF format
    doc.SaveToFile("FHIR_report.pdf", FileFormat.PDF)
    # Close the PdfDocument object
    doc.Close()