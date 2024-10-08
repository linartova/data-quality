import json
import psycopg2
from flask import Flask, redirect, url_for,  render_template, request, session
import os
from export_graphs_fhir import create_report_fhir
from export_graphs_ohdsi import create_report_ohdsi
from load_data_fhir import provide_server_connection, read_xml_and_create_resources
from load_data_ohdsi import load_data
import quality_checks_fhir
import quality_checks_ohdsi as qc_o


app = Flask(__name__)
app.secret_key = "supersecretkey" #TODO

# folder for uploaded files - this part was generated by ChatGPT
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# global variables for servers
fhir = None
omop = None

# home page
@app.route("/")
def home():
    return render_template("start.html")

# provide information
# fhir
@app.route("/why_fhir")
def why_fhir():
    return render_template("why_fhir.html")

@app.route("/about_qc_fhir")
def about_qc_fhir():
    return render_template("about_qc_fhir.html")

@app.route("/about_qc_again_fhir")
def about_qc_again_fhir():
    return render_template("about_qc_again_fhir.html")

# omop
@app.route("/why_omop")
def why_omop():
    return render_template("why_omop.html")

@app.route("/about_qc_omop")
def about_qc_omop():
    return render_template("about_qc_omop.html")

@app.route("/about_qc_again_omop")
def about_qc_again_omop():
    return render_template("about_qc_again_omop.html")

@app.route("/choose_your_path")
def choose_your_path():
    return render_template("choose_your_path.html")

# fhir workflow
@app.route("/provide_data")
def provide_data():
    return render_template("provide_data.html")

@app.route("/check_data_format")
def check_data_format():
    return render_template("check_data_format.html")

@app.route("/provide_server_fhir")
def provide_server_fhir():
    return render_template("provide_server_fhir.html")

@app.route("/connection_fhir")
def connection_fhir():
    return render_template("connection_fhir.html")

@app.route("/run_qc")
def run_qc():
    return render_template("run_qc.html")

@app.route("/dashboard_fhir")
def dashboard_fhir():
    return render_template("dashboard_fhir.html")

# omop workflow
@app.route("/provide_database_omop")
def provide_database_omop():
    return render_template("provide_database_omop.html")

@app.route("/connection_omop")
def connection_omop():
    return render_template("connection_omop.html")

@app.route("/dashboard_omop")
def dashboard_omop():
    return render_template("dashboard_omop.html")

# end
@app.route("/thanks")
def thanks():
    return render_template("thanks.html")

# actions in informative part
@app.route("/FROM_start_TO_provide_data", methods=["POST"])
def from_start_to_provide_data():
    return redirect("provide_data")

# uploaded file handling - this function was generated by ChatGPT
@app.route('/FROM_provide_data_TO_check_data_format', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        session["file_name"] = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return redirect(url_for('check_data_format'))

@app.route("/FROM_check_data_format_TO_why_fhir", methods=["POST"])
def from_check_data_format_to_why_fhir():
    try:
        action = request.form.get('action')

        if action == 'back':
            return redirect(url_for('why_omop'))
        elif action == 'go':
            return redirect(url_for("why_fhir"))

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred", 500
    return redirect(url_for("why_fhir"))

@app.route("/FROM_why_fhir_TO_about_qc_fhir", methods=["POST"])
def from_why_fhir_to_about_qc_fhir():
    return redirect("about_qc_fhir")

@app.route("/FROM_about_qc_fhir_TO_about_qc_again_fhir", methods=["POST"])
def from_about_qc_fhir_to_about_qc_again_fhir():
    return redirect("about_qc_again_fhir")

@app.route("/FROM_about_qc_again_fhir_TO_why_omop", methods=["POST"])
def from_about_qc_again_fhir_to_why_omop():
    return redirect("why_omop")

@app.route("/FROM_why_omop_TO_about_qc_omop", methods=["POST"])
def from_why_omop_to_about_qc_omop():
    return redirect("about_qc_omop")

@app.route("/FROM_about_qc_omop_TO_about_qc_again_omop", methods=["POST"])
def from_about_qc_omop_to_about_qc_again_omop():
    return redirect("about_qc_again_omop")

@app.route("/FROM_about_qc_again_omop_TO_choose_your_path", methods=["POST"])
def from_about_qc_again_omop_to_choose_your_path():
    return redirect("choose_your_path")

@app.route("/choose_your_path_form", methods=["POST"])
def choose_your_path_form():
    try:
        action = request.form.get('action')

        if action == 'fhir':
            session['standard'] = "fhir"
            return redirect(url_for('provide_server_fhir'))
        elif action == 'omop':
            session['standard'] = "omop"
            return redirect(url_for("provide_database_omop"))
        elif action == 'both':
            session['standard'] = "both"
            return redirect(url_for("provide_server_fhir"))


    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred", 500
    return redirect(url_for("choose_your_path"))

# actions in fhir

# server connection handling
@app.route('/provide_server_fhir_form', methods=['POST'])
def provide_server_fhir_form():
    session['url'] = request.form.get('url')
    return redirect(url_for("connection_fhir"))

@app.route("/connection_fhir_form", methods=["POST"])
def connection_fhir_form():
    try:
        action = request.form.get('action')

        if action == 'back':
            return redirect(url_for('provide_server_fhir'))
        elif action == 'next':
            standard = session.get("standard")
            if standard == "fhir":
                return redirect(url_for("run_qc"))
            else:
                return redirect(url_for("provide_database_omop"))

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred", 500
    return redirect(url_for("connection_fhir"))

# actions in omop
@app.route("/FROM_provide_database_omop_TO_connection_omop", methods=["POST"])
def from_provide_database_omop_to_connection_omop():
    try:
        action = request.form.get('action')

        host = request.form.get("host")
        port = request.form.get("port")
        user = request.form.get("user")
        password = request.form.get("password")
        database = request.form.get("database")
        schema = request.form.get("schema")
        ohdsi = {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': database,
        "schema" : schema
        }
        session["ohdsi"] = ohdsi

        if action == "back":
            return redirect(url_for("provide_database_omop"))
        elif action == "next":
            return redirect(url_for("connection_omop"))

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred", 500
    return redirect(url_for("provide_database_omop"))

@app.route("/connection_omop_form", methods=["POST"])
def connection_omop_form():
    try:
        action = request.form.get('action')

        if action == 'back':
            return redirect(url_for('connection_omop'))
        elif action == 'continue':
            return redirect(url_for('run_qc'))

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred", 500
    return redirect(url_for("connection_omop"))

# run quality checks
@app.route("/run_qc_form", methods=["POST"])
def run_qc_form():
    standard = session.get("standard")
    input_file = session.get("file_name")
    if standard == "fhir":
        graphs = fire()
        return render_template('dashboard_fhir.html', graphs=graphs)
    elif standard == "omop":
        ohdsi = session.get("ohdsi")
        graphs = omop_workflow(ohdsi, input_file)
        return render_template('dashboard_omop.html', graphs=graphs)
    elif standard == "both":
        graphs = fire()
        return render_template('dashboard_fhir.html', graphs=graphs)

@app.route('/go_to_dashboard_fhir', methods=['POST'])
def go_to_dashboard_fhir():
    graphs = []

    # Load all JSON files from the directory
    for file_name in os.listdir('plotly_graphs_fhir'):
        if file_name.endswith('.json'):
            with open(os.path.join('plotly_graphs_fhir', file_name)) as f:
                graphs.append(json.load(f))

    # Pass the graphs to the template
    return render_template('dashboard_fhir.html', graphs=graphs)

@app.route('/go_to_dashboard_omop', methods=['POST'])
def go_to_dashboard_omop():
    graphs = []

    # Load all JSON files from the directory
    for file_name in os.listdir('plotly_graphs_omop'):
        if file_name.endswith('.json'):
            with open(os.path.join('plotly_graphs_omop', file_name)) as f:
                graphs.append(json.load(f))

    # Pass the graphs to the template
    return render_template('dashboard_omop.html', graphs=graphs)

# graphs generation
def fire():
    url = session.get("url")
    file_name = session.get("file_name")

    # server
    smart_client = provide_server_connection(url)

    # store resources
    read_xml_and_create_resources(file_name, smart_client)

    # create graphs
    pdf = quality_checks_fhir.create_patient_data_frame(smart_client.server)
    sdf = quality_checks_fhir.create_specimen_data_frame(smart_client.server)
    cdf = quality_checks_fhir.create_condition_data_frame(smart_client.server)

    graphs = []

    p_completeness = quality_checks_fhir.completeness(pdf).to_json()
    graphs.append(p_completeness)
    s_completeness = quality_checks_fhir.completeness(sdf).to_json()
    graphs.append(s_completeness)
    c_completeness = quality_checks_fhir.completeness(cdf).to_json()
    graphs.append(c_completeness)

    p_uniqueness = quality_checks_fhir.uniqueness(pdf, "patient").to_json()
    graphs.append(p_uniqueness)
    s_uniqueness = quality_checks_fhir.uniqueness(pdf, "specimen").to_json()
    graphs.append(s_uniqueness)
    c_uniqueness = quality_checks_fhir.uniqueness(pdf, "condition").to_json()
    graphs.append(c_uniqueness)

    p_conformance = quality_checks_fhir.conformance_patient(pdf).to_json()
    graphs.append(p_conformance)
    c_conformance = quality_checks_fhir.conformance_condition(cdf).to_json()
    graphs.append(c_conformance)
    s_conformance = quality_checks_fhir.conformance_specimen(sdf).to_json()
    graphs.append(s_conformance)

    s_conformance_r = quality_checks_fhir.conformance_relational(sdf, smart_client.server).to_json()
    graphs.append(s_conformance_r)
    c_conformance_r = quality_checks_fhir.conformance_relational(cdf, smart_client.server).to_json()
    graphs.append(c_conformance_r)
    conformance_c = quality_checks_fhir.conformance_computational(pdf, sdf, cdf).to_json()
    graphs.append(conformance_c)

    age_at_primary_diagnosis = quality_checks_fhir.age_at_primary_diagnosis(pdf, cdf).to_json()
    graphs.append(age_at_primary_diagnosis)
    diagnosis_in_future = quality_checks_fhir.diagnosis_in_future(cdf).to_json()
    graphs.append(diagnosis_in_future)
    missing_collection_collectedDateTime = quality_checks_fhir.missing_collection_collectedDateTime(pdf, sdf).to_json()
    graphs.append(missing_collection_collectedDateTime)
    # TODO problem here
    # patients_without_specimen_type_text = quality_checks_fhir.patients_without_specimen_type_text(pdf, cdf).to_json()
    # graphs.append(patients_without_specimen_type_text)
    patients_without_condition_values = quality_checks_fhir.patients_without_condition_values(pdf, cdf).to_json()
    graphs.append(patients_without_condition_values)

    # TODO chatGPT
    # Directory to store the JSON files
    os.makedirs('plotly_graphs_fhir', exist_ok=True)

    # Save each graph as a separate JSON file
    for i, graph_json in enumerate(graphs):
        with open(f'plotly_graphs_fhir/graph_{i}.json', 'w') as f:
            json.dump(graph_json, f)

    # create report
    # create_report_fhir(smart_client.server)
    return graphs

def omop_workflow(ohdsi, input_file):
    schema = ohdsi.pop("schema")
    load_data(ohdsi, input_file, schema)

    # dashboard viz
    con = psycopg2.connect(**ohdsi)
    graphs = []

    pdf = qc_o.create_df_omop(con, "person", schema)
    odf = qc_o.create_df_omop(con, "observation_period", schema)
    cdf = qc_o.create_df_omop(con, "condition_occurrence", schema)
    sdf = qc_o.create_df_omop(con, "specimen", schema)
    ddf = qc_o.create_df_omop(con, "drug_exposure", schema)
    prdf = qc_o.create_df_omop(con, "procedure_occurrence", schema)

    graphs.append(qc_o.completeness(pdf).to_json())
    graphs.append(qc_o.completeness(odf).to_json())
    graphs.append(qc_o.completeness(cdf).to_json())
    graphs.append(qc_o.completeness(sdf).to_json())
    graphs.append(qc_o.completeness(ddf).to_json())
    graphs.append(qc_o.completeness(prdf).to_json())

    graphs.append(qc_o.uniqueness(pdf).to_json())
    graphs.append(qc_o.uniqueness(pdf).to_json())
    graphs.append(qc_o.uniqueness(pdf).to_json())
    graphs.append(qc_o.uniqueness(pdf).to_json())
    graphs.append(qc_o.uniqueness(pdf).to_json())
    graphs.append(qc_o.uniqueness(pdf).to_json())

    # warnings
    graphs.append(qc_o.observation_end_precedes_condition_start(cdf, odf).to_json())
    graphs.append(qc_o.observation_end_equals_condition_start(cdf, odf).to_json())
    graphs.append(qc_o.too_young_person(pdf,cdf).to_json())
    graphs.append(qc_o.observation_end_in_the_future(odf).to_json())
    graphs.append(qc_o.condition_start_in_the_future(cdf).to_json())
    graphs.append(qc_o.missing_drug_exposure_info(ddf).to_json())
    graphs.append(qc_o.sus_pharma(ddf).to_json())
    graphs.append(qc_o.sus_pharma_other(ddf).to_json())
    graphs.append(qc_o.drug_end_before_start(ddf).to_json())
    # TODO solve problem, function returns tuple
    # graphs.append(qc_o.therapy_start_before_diagnosis(cdf, ddf, prdf).to_json())
    # graphs.append(qc_o.treatment_start_in_the_future(ddf, prdf).to_json())
    graphs.append(qc_o.drug_exposure_end_in_the_future(ddf).to_json())
    graphs.append(qc_o.sus_early_pharma(cdf, ddf).to_json())
    graphs.append(qc_o.sus_short_pharma(cdf, ddf).to_json())

    # reports
    graphs.append(qc_o.missing_specimen_date(pdf, sdf).to_json())
    graphs.append(qc_o.patients_without_specimen_source_id(pdf, sdf).to_json())
    graphs.append(qc_o.patients_without_specimen_source_value_concept_id(pdf, sdf).to_json())
    graphs.append(qc_o.patients_without_condition_values(pdf, cdf).to_json())
    graphs.append(qc_o.patients_without_surgery_values(pdf, prdf).to_json())
    graphs.append(qc_o.missing_patient_and_diagnostic_values(pdf, prdf).to_json())
    graphs.append(qc_o.missing_targeted_therapy_values(pdf, prdf).to_json())
    graphs.append(qc_o.missing_pharmacotherapy_value(pdf, ddf).to_json())
    graphs.append(qc_o.missing_radiation_therapy_values(pdf, prdf).to_json())
    graphs.append(qc_o.counts_of_records(pdf, odf, cdf, sdf, ddf, prdf).to_json())
    graphs.append(qc_o.get_patients_without_surgery(pdf, prdf).to_json())

    # TODO chatGPT
    # Directory to store the JSON files
    os.makedirs('plotly_graphs_omop', exist_ok=True)

    # Save each graph as a separate JSON file
    for i, graph_json in enumerate(graphs):
        with open(f'plotly_graphs_omop/graph_{i}.json', 'w') as f:
            json.dump(graph_json, f)

    # create report
    # con = psycopg2.connect(**ohdsi)
    # create_report_ohdsi(con, schema)
    return graphs

if __name__ == "__main__":
    app.run()
