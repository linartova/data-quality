from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import quality_checks_fhir as qc


def create_report_fhir(server):
    pdf = qc.create_patient_data_frame(server)
    sdf = qc.create_specimen_data_frame(server)
    cdf = qc.create_condition_data_frame(server)

    # Create canvas
    can = canvas.Canvas("plots_fhir.pdf", pagesize=letter)
    # create pages
    create_dq_checks(can, pdf, cdf, sdf, server)
    create_warnings(can, pdf, cdf, sdf)
    create_reports(can, pdf, cdf, sdf)
    # Save PDF
    can.save()


def create_page(can, header, fig, graph_image_name, graph_size):
    # Add text to canvas for page 1
    text_page = "FHIR data quality checks"
    can.setFont("Helvetica-Bold", 14)
    can.drawString(50, 750, text_page)

    # header
    can.drawString(50, 700, header)
    # todo short description of graph

    # Save Plotly graph as PNG
    fig.write_image(graph_image_name + ".png")

    # Add Plotly graph to the PDF
    can.drawImage(graph_image_name + ".png", 50, 50, width=graph_size[0], height=graph_size[1])

    can.showPage()

def create_dq_checks(can, pdf, cdf, sdf, server):
    completeness = "completeness"

    person = qc.completeness(pdf)
    person.update_layout(width=400, height=400)
    create_page(can, completeness + " person", person,
                completeness + "_person", (500,500))

    condition = qc.completeness(cdf)
    condition.update_layout(width=400, height=400)
    create_page(can, completeness + " condition", condition, completeness + "_condition", (500, 500))

    specimens = qc.completeness(sdf)
    specimens.update_layout(width=400, height=400)
    create_page(can, completeness + " specimen", specimens, completeness + "_specimens", (500, 500))

    uniqueness = "uniqueness"

    person = qc.uniqueness(pdf, "person")
    person.update_layout(width=400, height=400)
    create_page(can, uniqueness + " person", person, uniqueness + "_person", (500, 500))

    condition = qc.uniqueness(cdf, "condition")
    condition.update_layout(width=400, height=400)
    create_page(can, uniqueness + " condition", condition, uniqueness + "_condition", (500, 500))

    specimens = qc.uniqueness(sdf, "specimen")
    specimens.update_layout(width=400, height=400)
    create_page(can, uniqueness + " specimen", specimens, uniqueness + "_specimens", (500, 500))

    qc.conformance_patient(pdf)
    qc.conformance_condition(cdf)
    qc.conformance_specimen(sdf)

    qc.conformance_relational(sdf, server)
    qc.conformance_relational(cdf, server)
    qc.conformance_computational(pdf, sdf, cdf)

def create_warnings(can, pdf, cdf, sdf):
    young = qc.age_at_primary_diagnosis(pdf, cdf)
    young.update_layout(width=400, height=400)
    create_page(can, "age_at_primary_diagnosis",
                young, "age_at_primary_diagnosis",
                (500, 500))

    diagnosis_in_future = qc.diagnosis_in_future(cdf)
    diagnosis_in_future.update_layout(width=400, height=400)
    create_page(can, "diagnosis_in_future",
                diagnosis_in_future, "diagnosis_in_future",
                (500, 500))


def create_reports(can, pdf, cdf, sdf):
    missing_collection_collectedDateTime = qc.missing_collection_collectedDateTime(pdf, sdf)
    missing_collection_collectedDateTime.update_layout(width=400, height=400)
    create_page(can, "missing_collection_collectedDateTime",
                missing_collection_collectedDateTime, "missing_collection_collectedDateTime",
                (500, 500))

    patients_without_specimen_type_text = qc.patients_without_specimen_type_text(pdf, sdf)
    patients_without_specimen_type_text.update_layout(width=400, height=400)
    create_page(can, "patients_without_specimen_type_text",
                patients_without_specimen_type_text, "patients_without_specimen_type_text",
                (500, 500))