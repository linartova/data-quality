from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import quality_checks_ohdsi as qc


def create_report_ohdsi(con, schema):
    pdf = qc.create_df_omop(con, "person", schema)
    odf = qc.create_df_omop(con, "observation_period", schema)
    cdf = qc.create_df_omop(con, "condition_occurrence", schema)
    sdf = qc.create_df_omop(con, "specimen", schema)
    ddf = qc.create_df_omop(con, "drug_exposure", schema)
    prdf = qc.create_df_omop(con, "procedure_occurrence", schema)

    # Create canvas
    can = canvas.Canvas("plots_ohdsi.pdf", pagesize=letter)
    # create pages
    create_completeness(can, pdf, odf, cdf, sdf, ddf, prdf)
    create_uniqueness(can, pdf, odf, cdf, sdf, ddf, prdf)
    create_warnings(can, pdf, odf, cdf, sdf, ddf, prdf)
    create_reports(can, pdf, odf, cdf, sdf, ddf, prdf)
    # Save PDF
    can.save()


def create_page(can, header, fig, graph_image_name, graph_size):
    # Add text to canvas for page 1
    text_page = "OHDSI data quality checks"
    can.setFont("Helvetica-Bold", 14)
    can.drawString(50, 750, text_page)

    # header
    can.drawString(50, 700, header)
    # todo short description of graph

    # Save Plotly graph as PNG
    fig.write_image("graphs/omop/" + graph_image_name + ".png")

    # Add Plotly graph to the PDF
    can.drawImage("graphs/omop/" + graph_image_name + ".png", 50, 50, width=graph_size[0], height=graph_size[1])

    can.showPage()


def create_completeness(can, pdf, odf, cdf, sdf, ddf, prdf):
    completeness = "completeness"

    person = qc.completeness(pdf)
    person.update_layout(width=400, height=400)
    create_page(can, completeness + " person", person,
                completeness + "_person", (500,500))

    observation = qc.completeness(odf)
    observation.update_layout(width=400, height=400)
    create_page(can, completeness + " observation_period", observation, completeness + "_observation", (500, 500))

    condition = qc.completeness(cdf)
    condition.update_layout(width=400, height=400)
    create_page(can, completeness + " condition_occurrence", condition, completeness + "_condition", (500, 500))

    drugs = qc.completeness(ddf)
    drugs.update_layout(width=400, height=400)
    create_page(can, completeness +" drug_exposure", drugs, completeness + "_drugs", (500, 500))

    specimens = qc.completeness(sdf)
    specimens.update_layout(width=400, height=400)
    create_page(can, completeness + " specimen", specimens, completeness + "_specimens", (500, 500))

    procedures = qc.completeness(prdf)
    procedures.update_layout(width=400, height=400)
    create_page(can, completeness + " procedure_occurrence", procedures, completeness + "_procedures", (500, 500))


def create_uniqueness(can, pdf, odf, cdf, sdf, ddf, prdf):
    uniqueness = "uniqueness"

    person = qc.uniqueness(pdf)
    person.update_layout(width=400, height=400)
    create_page(can, uniqueness + " person", person, uniqueness + "_person", (500,500))

    observation = qc.uniqueness(odf)
    observation.update_layout(width=400, height=400)
    create_page(can, uniqueness + " observation_period", observation, uniqueness + "_observation", (500, 500))

    condition = qc.uniqueness(cdf)
    condition.update_layout(width=400, height=400)
    create_page(can, uniqueness + " condition_occurrence", condition, uniqueness + "_condition", (500, 500))

    drugs = qc.uniqueness(ddf)
    drugs.update_layout(width=400, height=400)
    create_page(can, uniqueness + " drug_exposure", drugs, uniqueness + "_drugs", (500, 500))

    specimens = qc.uniqueness(sdf)
    specimens.update_layout(width=400, height=400)
    create_page(can, uniqueness + " specimen", specimens, uniqueness + "_specimens", (500, 500))

    procedures = qc.uniqueness(prdf)
    procedures.update_layout(width=400, height=400)
    create_page(can, uniqueness+ " procedure_occurrence", procedures, uniqueness + "_procedures", (500, 500))


def create_warnings(can, pdf, odf, cdf, sdf, ddf, prdf):
    observation_precedes = qc.observation_end_precedes_condition_start(cdf, odf)
    observation_precedes.update_layout(width=400, height=400)
    create_page(can, "observation_end_precedes_condition_start",
                observation_precedes, "observation_end_precedes_condition_start",
                (500, 500))

    observation_equals = qc.observation_end_equals_condition_start(cdf, odf)
    observation_equals.update_layout(width=400, height=400)
    create_page(can, "observation_end_equals_condition_start",
                observation_equals, "observation_end_equals_condition_start",
                (500, 500))

    young = qc.too_young_person(pdf, cdf)
    young.update_layout(width=400, height=400)
    create_page(can, "too_young_person",
                young, "too_young_person",
                (500, 500))

    observation_future = qc.observation_end_in_the_future(odf)
    observation_future.update_layout(width=400, height=400)
    create_page(can, "observation_end_in_the_future",
                observation_future, "observation_end_in_the_future",
                (500, 500))

    condition_future = qc.condition_start_in_the_future(cdf)
    condition_future.update_layout(width=400, height=400)
    create_page(can, "condition_start_in_the_future",
                condition_future, "condition_start_in_the_future",
                (500, 500))

    missing_drug = qc.missing_drug_exposure_info(ddf)
    missing_drug.update_layout(width=400, height=400)
    create_page(can, "missing_drug_exposure_info",
                missing_drug, "missing_drug_exposure_info",
                (500, 500))

    sus_pharma = qc.sus_pharma(ddf)
    sus_pharma.update_layout(width=400, height=400)
    create_page(can, "sus_pharma",
                sus_pharma, "sus_pharma",
                (500, 500))

    sus_pharma_other = qc.sus_pharma_other(ddf)
    sus_pharma_other.update_layout(width=400, height=400)
    create_page(can, "sus_pharma_other",
                sus_pharma_other, "sus_pharma_other",
                (500, 500))

    drug_before = qc.drug_end_before_start(ddf)
    drug_before.update_layout(width=400, height=400)
    create_page(can, "drug_end_before_start",
                drug_before, "drug_end_before_start",
                (500, 500))

    therapy_before_1, therapy_before_2 = qc.therapy_start_before_diagnosis(cdf, ddf, prdf)
    therapy_before_1.update_layout(width=400, height=400)
    therapy_before_2.update_layout(width=400, height=400)
    create_page(can, "therapy_start_before_diagnosis",
                therapy_before_1, "therapy_start_before_diagnosis",
                (500, 500))
    create_page(can, "therapy_start_before_diagnosis",
                therapy_before_2, "therapy_start_before_diagnosis",
                (500, 500))

    treatment_future_1, treatment_future_2  = qc.treatment_start_in_the_future(ddf, prdf)
    treatment_future_1.update_layout(width=400, height=400)
    treatment_future_2.update_layout(width=400, height=400)
    create_page(can, "treatment_start_in_the_future",
                treatment_future_1, "treatment_start_in_the_future",
                (500, 500))
    create_page(can, "treatment_start_in_the_future",
                treatment_future_2, "treatment_start_in_the_future",
                (500, 500))

    drug_future = qc.drug_exposure_end_in_the_future(ddf)
    drug_future.update_layout(width=400, height=400)
    create_page(can, "drug_exposure_end_in_the_future",
                drug_future, "drug_exposure_end_in_the_future",
                (500, 500))

    sus_early = qc.sus_early_pharma(cdf, ddf)
    sus_early.update_layout(width=400, height=400)
    create_page(can, "sus_early_pharma",
                sus_early, "sus_early_pharma",
                (500, 500))

    sus_short = qc.sus_short_pharma(cdf, ddf)
    sus_short.update_layout(width=400, height=400)
    create_page(can, "sus_short_pharma",
                sus_short, "sus_short_pharma",
                (500, 500))


def create_reports(can, pdf, odf, cdf, sdf, ddf, prdf):
    specimen_date = qc.missing_specimen_date(pdf, sdf)
    specimen_date.update_layout(width=400, height=400)
    create_page(can, "missing_specimen_date",
                specimen_date, "missing_specimen_date",
                (500, 500))

    specimen_source = qc.patients_without_specimen_source_id(pdf, sdf)
    specimen_source.update_layout(width=400, height=400)
    create_page(can, "patients_without_specimen_source_id",
                specimen_source, "patients_without_specimen_source_id",
                (500, 500))

    specimen_source_value = qc.patients_without_specimen_source_value_concept_id(pdf, sdf)
    specimen_source_value.update_layout(width=400, height=400)
    create_page(can, "patients_without_specimen_source_value_concept_id",
                specimen_source_value, "patients_without_specimen_source_value_concept_id",
                (500, 500))

    condition_values = qc.patients_without_condition_values(pdf, cdf)
    condition_values.update_layout(width=400, height=400)
    create_page(can, "patients_without_condition_values",
                condition_values, "patients_without_condition_values",
                (500, 500))

    surgery_values = qc.patients_without_surgery_values(pdf, prdf)
    surgery_values.update_layout(width=400, height=400)
    create_page(can, "patients_without_surgery_values",
                surgery_values, "patients_without_surgery_values",
                (500, 500))

    diagnostic_values = qc.missing_patient_and_diagnostic_values(pdf, prdf)
    diagnostic_values.update_layout(width=400, height=400)
    create_page(can, "missing_patient_and_diagnostic_values",
                diagnostic_values, "missing_patient_and_diagnostic_values",
                (500, 500))

    targeted_values = qc.missing_targeted_therapy_values(pdf, prdf)
    targeted_values.update_layout(width=400, height=400)
    create_page(can, "missing_targeted_therapy_values",
                targeted_values, "missing_targeted_therapy_values",
                (500, 500))

    missing_pharma_values = qc.missing_pharmacotherapy_value(pdf, ddf)
    missing_pharma_values.update_layout(width=400, height=400)
    create_page(can, "missing_pharmacotherapy_value",
                missing_pharma_values, "missing_pharmacotherapy_value",
                (500, 500))

    radiation_values = qc.missing_radiation_therapy_values(pdf, prdf)
    radiation_values.update_layout(width=400, height=400)
    create_page(can, "missing_radiation_therapy_values",
                radiation_values, "missing_radiation_therapy_values",
                (500, 500))

    statistic = qc.counts_of_records(pdf, odf, cdf, sdf, ddf, prdf)
    statistic.update_layout(width=400, height=400)
    create_page(can, "counts_of_records",
                statistic, "counts_of_records",
                (500, 500))

    without_surgery = qc.get_patients_without_surgery(pdf, prdf)
    without_surgery.update_layout(width=400, height=400)
    create_page(can, "get_patients_without_surgery",
                without_surgery, "get_patients_without_surgery",
                (500, 500))


# if __name__ == '__main__':
#
#     ohdsi = {}
#     con = psycopg2.connect(**ohdsi)
#     pdf = qc.create_df_omop(con, "person", "ohdsi_demo").dropna(axis=1, how='all')
#     odf = qc.create_df_omop(con, "observation_period", "ohdsi_demo").dropna(axis=1, how='all')
#     cdf = qc.create_df_omop(con, "condition_occurrence", "ohdsi_demo").dropna(axis=1, how='all')
#     sdf = qc.create_df_omop(con, "specimen", "ohdsi_demo").dropna(axis=1, how='all')
#     ddf = qc.create_df_omop(con, "drug_exposure", "ohdsi_demo").dropna(axis=1, how='all')
#     prdf = qc.create_df_omop(con, "procedure_occurrence", "ohdsi_demo").dropna(axis=1, how='all')
#
#     create_report_ohdsi(con, "")