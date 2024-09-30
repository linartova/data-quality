from flask import Flask, redirect, url_for,  render_template, request, session
import os
from load_data_fhir import provide_server_connection, read_xml_and_create_resources
from visualization_fhir import create_report_fhir
import quality_checks_fhir


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

@app.route("/errors_fhir")
def errors_fhir():
    return  render_template("errors_fhir.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/failures_fhir")
def failures_fhir():
    return render_template("failures_fhir")

# omop workflow
@app.route("/provide_database_omop")
def provide_database_omop():
    return render_template("provide_database_omop.html")

@app.route("/connection_omop")
def connection_omop():
    return render_template("connection_omop.html")

@app.route("/run_qc_omop")
def run_qc_omop():
    return render_template("run_qc_omop.html")

@app.route("/errors_omop")
def errors_omop():
    return  render_template("errors_omop.html")

@app.route("/failures_omop")
def failures_omop():
    return render_template("failures_omop")

# end
@app.route("/thanks")
def thanks():
    return render_template("thanks.html")

# actions in informative part
@app.route("/get-started", methods=["POST"])
def get_started():
    return redirect("provide_data")

@app.route("/go_to_about_qc_fhir", methods=["POST"])
def go_to_about_qc_fhir():
    return redirect("about_qc_fhir")

@app.route("/go_to_about_qc_again_fhir", methods=["POST"])
def go_to_about_qc_again_fhir():
    return redirect("about_qc_again_fhir")

@app.route("/go_to_why_omop", methods=["POST"])
def go_to_why_omop():
    return redirect("why_omop")

@app.route("/go_to_about_qc_omop", methods=["POST"])
def go_to_about_qc_omop():
    return redirect("about_qc_omop")

@app.route("/go_to_about_qc_again_omop", methods=["POST"])
def go_to_about_qc_again_omop():
    return redirect("about_qc_again_omop")

@app.route("/go_to_choose_your_path", methods=["POST"])
def go_to_choose_your_path():
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
@app.route("/go_to_provide_server_fhir", methods=["POST"])
def go_to_provide_server_fhir():
    try:
        action = request.form.get('action')

        if action == 'again':
            return redirect(url_for('why_omop'))
        elif action == 'next':
            return redirect(url_for("why_fhir"))

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred", 500
    return redirect(url_for("why_fhir"))

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

@app.route("/run_qc_form", methods=["POST"])
def run_qc_form():
    standard = session.get("standard")
    if standard == "omop":
        return redirect(url_for("errors_omop"))
    else:
        return redirect(url_for("errors_fhir"))

@app.route("/go_to_omop_errors", methods=["POST"])
def go_to_omop_errors():
    graphs = fire()

    standard = session.get("standard")
    if standard == "fhir":
        return render_template('dashboard.html', graphs=graphs)
    else:
        return redirect(url_for("errors_omop"))

# actions in omop
@app.route("/go_to_connection_omop", methods=["POST"])
def go_to_connection_omop():
    try:
        action = request.form.get('action')

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

        if action == 'again':
            return redirect(url_for('connection_omop'))
        elif action == 'continue':
            return redirect(url_for('run_qc'))

    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred", 500
    return redirect(url_for("connection_omop"))

@app.route("/run_qc_omop_form", methods=["POST"])
def run_qc_omop_form():
    return redirect("errors_omop")

@app.route("/go_to_dashboard", methods=["POST"])
def go_to_dashboard():
    return redirect("dashboard")

@app.route("/go_to_end", methods=["POST"])
def go_to_end():
    return redirect("thanks")

# uploaded file handling - this function was generated by ChatGPT
@app.route('/go_to_check_data_format', methods=['POST'])
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

# TODO delete uploads in the end

# server connection handling
@app.route('/get_server_url', methods=['POST'])
def get_server_url():
    session['url'] = request.form.get('url')
    return redirect(url_for("connection_fhir"))

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

    # create report
    # create_report_fhir(smart_client.server)
    return graphs


if __name__ == "__main__":
    app.run()
