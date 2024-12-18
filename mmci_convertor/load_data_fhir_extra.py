from fhirclient import client
import xml.etree.ElementTree as ElementTree
import fhirclient.models.patient as p
import fhirclient.models.observation as o
import fhirclient.models.condition as c
import fhirclient.models.specimen as s
import fhirclient.models.procedure as pro
import fhirclient.models.period as period
import fhirclient.models.annotation as anno
from fhirclient.models.fhirdate import FHIRDate
from fhirclient.models.quantity import Quantity
from fhirclient.models.meta import Meta
import fhirclient.models.codeableconcept as codeAbleConcept
from fhirclient.models.coding import Coding
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.specimen import SpecimenCollection
from fhirclient.models.identifier import Identifier
from datetime import timedelta, datetime
from fhir_classes_extra import *
from quality_checks_fhir_extra import *


def provide_server_connection(url):
    """
    Connects to FHIR server.

    :param url: The url of FHIR server.
    :return:
        FHIR client.
    """
    settings = {
        'app_id': 'my_web_app',
        'api_base': url
    }
    smart = client.FHIRClient(settings=settings)
    assert not smart.ready
    smart.prepare()
    assert smart.ready
    assert smart.authorize_url is None
    return smart


def read_xml_and_create_resources(file_name, smart):
    """
    Parse input file, process data, store them on FHIR server.

    :param file_name: The path of input file.
    :param smart: FHIR client.
    :return:
        None
    """
    tree = ElementTree.parse("uploads/" + file_name)
    root = tree.getroot()
    namespace = "{http://registry.samply.de/schemata/import_v1}"
    result = []
    for element in root.iter():
        if element.tag == namespace + "BHPatient":
            # patient
            if element.find(namespace + "Identifier") is not None:
                patient_id = element.find(namespace + "Identifier").text
            else:
                patient_id = None
            form = element.find(namespace +
                                "Locations").find(namespace +
                                                  "Location").find(namespace +
                                                                   "BasicData").find(namespace +
                                                                                     "Form")
            sex = form.find(namespace + "Dataelement_85_1")
            if sex is not None:
                sex = sex.text
            if form.find(namespace + "Dataelement_3_1") is not None:
                age_at_primary_diagnostic = form.find(namespace + "Dataelement_3_1").text
            else:
                age_at_primary_diagnostic = None
            if form.find(namespace + "Dataelement_5_2") is not None:
                vital_status = form.find(namespace + "Dataelement_5_2").text
            else:
                vital_status = None
            if form.find(namespace + "Dataelement_7_2") is not None:
                overall_survival = form.find(namespace + "Dataelement_7_2").text
            else:
                overall_survival = None
            if form.find(namespace + "Dataelement_6_3") is not None:
                last_update = form.find(namespace + "Dataelement_6_3").text
            else:
                last_update = None
            time_observation = TimeObservation(overall_survival, last_update)

            if form.find(namespace + "Dataelement_51_3") is not None:
                date_diagnosis = form.find(namespace + "Dataelement_51_3").text
                diagnosis = datetime.strptime(date_diagnosis, "%Y-%m-%d")
            else:
                diagnosis = None

            if diagnosis is not None and age_at_primary_diagnostic is not None:
                birth_date = FHIRDate(str(diagnosis.year - int(age_at_primary_diagnostic)))
            else:
                birth_date = None

            if vital_status != "ALIVE":
                deceased_boolean = True
                if form.find(namespace + "Dataelement_6_3") is not None:
                    timestamp = form.find(namespace + "Dataelement_6_3").text
                else:
                    timestamp = None
            else:
                deceased_boolean = False
                timestamp = None
            patient = Patient(patient_id, deceased_boolean, timestamp, sex, birth_date)

            # recurrence
            recurrence = form.find(namespace + "Dataelement_4_3")
            if recurrence is not None:
                recurrence = recurrence.text

            # condition
            date_diagnosis = form.find(namespace + "Dataelement_51_3")
            if date_diagnosis is not None:
                date_diagnosis = date_diagnosis.text
            events = element.find(namespace + "Locations").find(namespace + "Location").find(namespace + "Events")

            # tnm
            (localization, tnm_t, tnm_n, tnm_m, stage,
             uicc_version, grade, morphology) = find_histopathology(namespace, events)
            tnm_t_code, tnm_t_display = map_tnm_pt(tnm_t)
            tnm_n_code, tnm_n_display = map_tnm_pn(tnm_n)
            tnm_m_code, tnm_m_display = map_tnm_pm(tnm_m)
            stage_code, stage_display = map_stage(stage)
            uicc_code, uicc_display = map_uicc(uicc_version)
            grade_code, grade_display = map_grade(grade)
            morphology_code, morphology_display = map_morphology(morphology)

            tnm = TNM(tnm_t_code, tnm_t_display, tnm_n_code, tnm_n_display, tnm_m_code,
                      tnm_m_display, stage_code, stage_display, uicc_code, uicc_display,
                      grade_code, grade_display, morphology_code, morphology_display)

            # response
            responses = find_response(namespace, events, diagnosis)

            # surgery
            surgeries = find_surgeries(namespace, events, diagnosis)

            # radiation_therapy
            radiations = find_radiation(namespace, events, diagnosis)

            # targeted_therape
            targeteds = find_targeteds(namespace, events, diagnosis)

            # specimen
            specimens = find_specimens(namespace, events)

            record = Record(patient, recurrence, time_observation, responses,
                           surgeries, radiations, targeteds, tnm,
                           Condition(localization, date_diagnosis),
                           specimens)
            result.append(record)
    create_files(result, smart)
    return None


def map_tnm_pt(tumor):
    """
    Map original value of "Primary Tumor" dataelement into FHIR code and display.
    Args:
        tumor: original value of "Primary Tumor"

    Returns: code and display values based on original value

    """
    tumor = tumor.split("-")[1][1:]
    codes = {"TX","T0","Ta","Tis","Tis(LAMN)","Tis(DCIS)",
             "Tis(LCIS)","Tis(Paget)","Tis(pu)","Tis(pd)",
             "T1","T1mi","T1a","T1a1","T1a2","T1b","T1b1",
             "T1b2","T1c","T1c1","T1c2","T1c3","T1d","T2",
             "T2a","T2a1","T2a2","T2b","T2c","T2d","T3",
             "T3a","T3b","T3c","T3d","T3e","T4","T4a","T4b",
             "T4c","T4d","T4e"}
    for code in codes:
        if tumor == code:
            return code, code
    return None, None


def map_tnm_pn(nodes):
    """
    Map original value of "Regional lymph nodes" dataelement into FHIR code and display.
    Args:
        original value of "Regional lymph nodes"

    Returns: code and display values based on original value

    """
    nodes = nodes.split("-")[1][1:]
    codes = {"Nx","N0","N1", "N1(mi)","N1a","N1b","N1c","N2",
             "N2a","N2b","N2c","N3","N3a","N3b","N3c"}
    if nodes == "NX":
        return "NX", "Nx"
    for code in codes:
        if nodes == code:
            if code == "N1(mi)":
                return code, "N1mi"
            else:
                return code, code
    return None, None


def map_tnm_pm(metastasis):
    """
    Map original value of "Distant metastasis" dataelement into FHIR code and display.
    Args:
        metastasis: original value of "Distant metastasis"

    Returns: code and display values based on original value

    """
    metastasis = metastasis.split("-")[1][1:]
    codes = {"M0","M1","M1a","M1b","M1c","M1d","MX"}
    for code in codes:
        if metastasis == code:
            return code, code
    return None, None


def map_stage(stage):
    """
    Map original value of "Stage" dataelement into FHIR code and display.
    Args:
        stage: original value of "Stage"

    Returns: code and display values based on original value

    """
    stage = stage.split("-")[1][1:]
    codes = {"X","0","0a","0is","I","IA1","IA2","IA3",
             "IB","IB1","IB2","IC","IS","II","IIA",
             "IIA1","IIA2","IIB","IIC","III","IIIA",
             "IIIA1","IIIA2","IIIB","IIIC","IIIC1",
             "IIIC2","IV","IVA","IVB","IVC"}
    # probably error in data
    if stage.find("II A") != -1:
        return "IIA", "Stage " + "IIA"
    for code in codes:
        if stage == code:
            if code == "X":
                return "okk", "Stage X"
            return code, "Stage " + code
    return 0, "unkown"


def map_uicc(uicc_version):
    """
    Map original value of "UICC version" dataelement into FHIR code and display.
    Args:
        uicc_version: original value of "UICC version"

    Returns: code and display values based on original value

    """
    codes = {"6th" : ("444256004", "American Joint Commission on Cancer, Cancer Staging Manual, 6th edition neoplasm staging system (tumor staging)"),
             "7th" : ("443830009", "American Joint Commission on Cancer, Cancer Staging Manual, 7th edition neoplasm staging system (tumor staging)"),
             "8th" : ("897275008", "American Joint Commission on Cancer, Cancer Staging Manual, 8th edition neoplasm staging system (tumor staging)"),
             "9th" : ("1269566009", "American Joint Commission on Cancer, Cancer Staging Manual, 9th version neoplasm staging system (tumor staging)")}
    for code in codes.keys():
        if uicc_version.find(code) != -1:
            return codes.get(code)
    return None, None


def map_grade(grade):
    """
    Map original value of "Grade" dataelement into FHIR code and display.
    Args:
        grade: original value of "Grade"

    Returns: code and display values based on original value

    """
    codes = {"GX" : ("12619005", "GX grade (finding)"),
             "G1" : ("54102005", "G1 grade (finding)"),
             "G2" : ("1663004", "G2 grade (finding)"),
             "G3" : ("61026006", "G3 grade (finding)")}
    for code in codes.keys():
        if grade.find(code) != -1:
            return codes.get(code)
    return None, None


def map_morphology(morphology):
    """
    Map original value of "Morphology" dataelement into FHIR code and display.
    Args:
        morphology: original value of "Morphology"

    Returns: code and display values based on original value

    """
    codes = {"Adenocarcinoma" : ("1187332001", "Adenocarcinoma (morphologic abnormality)"),
             "Mucinous carcinoma" : ("72495009", "Mucinous adenocarcinoma (morphologic abnormality)"),
             "Signet-ring cell carcinoma" : ("87737001", "Signet ring cell carcinoma (morphologic abnormality)"),
             "Medullary carcinoma" : ("32913002", "Medullary carcinoma (morphologic abnormality)"),
             "Other" : ("0", "Other")}
    for code in codes.keys():
        if morphology.find(code) != -1:
            return codes.get(code)
    return None, None


def map_surgery(primary_surgery, secondary_surgery):
    """
    Map original value of "Surgery type" dataelement and "Other surgery type" dataelement,
     if there is any, into FHIR code and display.
    Args:
        primary_surgery: original value of "Surgery type"
        secondary_surgery: original value of "Other surgery type"

    Returns: code, display and note values based on original value

    """
    code_mapping = {"Abdomino-perineal resection": 265414003,
                    "Anterior resection of rectum": 4558008,
                    "Endo-rectal tumor resection": None,
                    "Left hemicolectomy": 315324009,
                    "Low anteroir colon resection": None,
                    "Pan-procto colectomy": None,
                    "Right hemicolectomy": 235326000,
                    "Sigmoid colectomy": 84604002,
                    "Total colectomy": 26390003,
                    "Transverse colectomy": 26925005}
    note = "Other surgery type not found." if secondary_surgery is None else "Other surgery type: " + secondary_surgery
    for code in code_mapping.keys():
        if primary_surgery == code:
            if (primary_surgery == "Endo-rectal tumor resection"
                    or primary_surgery == "Low anteroir colon resection"
                    or primary_surgery == "Pan-procto colectomy"):
                return "Unknown (qualifier value)", 261665006, "Possible surgery type: Endo-rectal tumor resection, Low anteroir colon resection, Pan-procto colectomy. Mapping unavailable."
            result = code, code_mapping.get(code), note
            if result[0] == "Abdomino-perineal resection":
                result = "Abdominoperineal resection of rectum", 265414003, note
            if result[0] == "Left hemicolectomy":
                result = "Left hemicolectomy with anastomosis", 315324009, note
            return result
    return "Unknown (qualifier value)", 261665006, note


def find_surgeries(namespace, events, initial_diagnosis):
    """
    Find all surgeries for one patient.

    Args:
        namespace: The namespace of file.
        events: XML element, where Surgery can be stored.
        initial_diagnosis: Date of first diagnosis.

    Returns: List of all surgeries for one patient, stored in Surgery class.

    """
    result = []
    for event in events.findall(namespace + "Event"):

        if event.attrib.get("eventtype") == "Surgery":
            primary_surgery = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_49_1")
            if primary_surgery is not None:
                primary_surgery = primary_surgery.text
            secondary_surgery_node = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_67_1")
            secondary_surgery = None if secondary_surgery_node is None else secondary_surgery_node.text
            surgery_name, surgery_code, note = map_surgery(primary_surgery, secondary_surgery)
            start_week = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_8_3")
            if start_week is not None:
                start_week = int(start_week.text)
                date = initial_diagnosis + timedelta(weeks=start_week)
                time = date.strftime("%Y-%m-%d")
            else:
                time = None
            radicality = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_9_2")
            if radicality is not None:
                radicality = radicality.text
            surgery_radicality_name, surgery_radicality_code = mapp_surgery_radicality(radicality)
            location = event.find(namespace + "LogitudinalData").find(namespace + "Form").find(
                namespace + "Dataelement_93_1")
            if location is not None:
                location = location.text
            else:
                location = None
            body_site_code = body_site_mapping_codes(location)
            body_site_name = body_site_mapping_names(location)
            if surgery_code is not None:
                result.append(Surgery(time, surgery_name, surgery_code, surgery_radicality_name, surgery_radicality_code, body_site_name, body_site_code, note))
    return result


def find_radiation(namespace, events, initial_diagnosis):
    """
    Find all radiation therapies for one patient.

    Args:
        namespace: The namespace of file.
        events: XML element, where Radiation Therapy can be stored.
        initial_diagnosis: Date of first diagnosis.

    Returns: List of all radiation therapies for one patient, stored in Radiation Therapy class.

    """
    result = []
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Radiation therapy":
            start_week = event.find(namespace + "LogitudinalData").find(namespace + "Form5").find(
                namespace + "Dataelement_12_4")
            if start_week is not None:
                start_week = int(start_week.text)
            end_week = event.find(namespace + "LogitudinalData").find(namespace + "Form5").find(
                namespace + "Dataelement_13_2")
            if end_week is not None:
                end_week = int(end_week.text)
            start_date = initial_diagnosis + timedelta(weeks=start_week)
            end_date = initial_diagnosis + timedelta(weeks=end_week)
            start = FHIRDate(start_date.strftime("%Y-%m-%d"))
            end = FHIRDate(end_date.strftime("%Y-%m-%d"))
            result.append(RadiationTherapy(start, end))
    return result


def find_targeteds(namespace, events, initial_diagnosis):
    """
    Find all targeted therapies for one patient.

    Args:
        namespace: The namespace of file.
        events: XML element, where Targeted Therapy can be stored.
        initial_diagnosis: Date of first diagnosis.

    Returns: List of all targeted therapies for one patient, stored in Targeted Therapy class.

    """
    result = []
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Targeted Therapy":
            start_week = event.find(namespace + "LogitudinalData").find(namespace + "Form6").find(
                namespace + "Dataelement_35_3")
            if start_week is not None:
                start_week = int(start_week.text)
            end_week = event.find(namespace + "LogitudinalData").find(namespace + "Form6").find(
                namespace + "Dataelement_36_1")
            if end_week is not None:
                end_week = int(end_week.text)
            start_date = initial_diagnosis + timedelta(weeks=start_week)
            end_date = initial_diagnosis + timedelta(weeks=end_week)
            start = FHIRDate(start_date.strftime("%Y-%m-%d"))
            end = FHIRDate(end_date.strftime("%Y-%m-%d"))
            result.append(TargetedTherapy(start, end))
    return result


def map_response(response):
    """
    Map original value of "Response to therapy" form into FHIR code and display.
    Args:
        response: original value of "Response to therapy"

    Returns: code and display values based on original value

    """
    mapping = {"Specific response - Complete response" : (371001000, "Patient cured (finding)"),
               "Specific response - Partial response" : (268910001, "Patient's condition improved (finding)"),
               "Specific response - Stable disease" : (359746009, "Patient's condition stable (finding)"),
               "Specific response - Progressive disease" : (271299001, "Patient's condition worsened (finding)")}
    if response is None:
        return None, None
    for message in mapping.keys():
        if response.find(message) != -1:
            return mapping.get(message)
    return None, None


def find_response(namespace, events, initial_diagnosis):
    """
    Find all "Response to therapy" forms for one patient.

    Args:
        namespace: The namespace of file.
        events: XML element, where Targeted Therapy can be stored.
        initial_diagnosis: Date of first diagnosis.

    Returns: List of all "Response to therapy" forms for one patient, stored in "Response" class.

    """
    result = []
    for event in events.findall(namespace + "Event"):

        if event.attrib.get("eventtype") == "Response to therapy":
            content = event.find(namespace + "LogitudinalData").find(namespace + "Form4").find(
                namespace + "Dataelement_33_1")
            if content is not None:
                content = content.text
            time = event.find(namespace + "LogitudinalData").find(namespace + "Form4").find(
                namespace + "Dataelement_34_1")
            if time is not None:
                time = int(time.text)
            time = initial_diagnosis + timedelta(weeks=time)
            time = time.strftime("%Y-%m-%d")
            code, display = map_response(content)
            result.append(Response(code, display, time))
    return result

def body_site_mapping_codes(location):
    """
    Map original value of "Location of the tumor" dataelement into FHIR code.
    Args:
        location: original value of "Location of the tumor"

    Returns: code value based on original value

    """
    codes_mapping = {"C18.0": 32713005,
                     "C18.1": None,
                     "C18.2": 9040008,
                     "C18.3": 48338005,
                     "C18.4": 485005,
                     "C18.5": 72592005,
                     "C18.6": 32622004,
                     "C18.7": 60184004,
                     "C18.8": None,
                     "C18.9": None,
                     "C19": 49832006,
                     "C20": 34402009}
    for code in codes_mapping.keys():
        if location.find(code) != -1:
            return codes_mapping.get(code)
    return None


def body_site_mapping_names(location):
    """
    Map original value of "Location of the tumor" dataelement into FHIR display.
    Args:
        location: original value of "Location of the tumor"

    Returns: display value based on original value

    """
    codes_mapping = {"C18.0": "Cecum structure",
                     "C18.1": None,
                     "C18.2": "Ascending colon structure",
                     "C18.3": "Structure of right colic flexur",
                     "C18.4": "Transverse colon structure",
                     "C18.5": "Structure of left colic flexure",
                     "C18.6": "Descending colon structure",
                     "C18.7": "Sigmoid colon structure",
                     "C18.8": None,
                     "C18.9": None,
                     "C19": "Structure of rectosigmoid junction",
                     "C20": "Rectum structure"}
    for code in codes_mapping.keys():
        if location.find(code) != -1:
            return codes_mapping.get(code)
    return None


def mapp_surgery_radicality(radicality):
    """
    Map original value of "Surgery radicality" form into FHIR code and display.
    Args:
        radicality: original value of "Surgery radicality"

    Returns: code and display values based on original value

    """
    codes = {"R0": ("Residual tumor stage R0 (finding)", 258254000),
             "R1": ("Residual tumor stage R1 (finding)", 278271003),
             "R2": ("Residual tumor stage R2 (finding)", 278272005)}
    if radicality in codes.keys():
        return codes.get(radicality)
    return None, None


def find_specimens(namespace, events):
    """
    Create a list of all specimens of one patient.

    :param namespace: The namespace of file.
    :param events: XML element, where Specimens can be stored.
    :return:
        List of all specimens.
    """
    result = []
    for event in events.findall(namespace + "Event"):
        if "eventtype" in event.attrib and event.attrib.get("eventtype") == "Sample":

            sample = event.find(namespace + "LogitudinalData").find(namespace + "Form1")
            year_of_sample_connection = sample.find(namespace + "Dataelement_89_3")
            if year_of_sample_connection is not None:
                year_of_sample_connection = FHIRDate(year_of_sample_connection.text)
            sample_material_type = sample.find(namespace + "Dataelement_54_2")
            if sample_material_type is not None:
                sample_material_type = sample_material_type.text
            preservation_mode = sample.find(namespace + "Dataelement_55_2")
            if preservation_mode is not None:
                preservation_mode = preservation_mode.text
            identifier = sample.find(namespace + "Dataelement_56_2")
            if identifier is not None:
                identifier = identifier.text

            code, display = specimen_mapping(sample_material_type, preservation_mode)

            result.append(Specimen(identifier, code, display, year_of_sample_connection))
    return result


def specimen_mapping(sample_material_type, preservation_mode):
    """
    Map original value of "Material type" dataelement and "Preservation mode" dataelement into FHIR code and display.
    Args:
        sample_material_type: original value of "Material type"
        preservation_mode: original value of "Preservation mode"

    Returns: code and display values based on original value

    """
    if sample_material_type == "Tumor" and preservation_mode == "Cryopreservation":
        return "tumor-tissue-frozen", "Tumor tissue (frozen)"
    if sample_material_type == "Tumor" and preservation_mode == "FFPE":
        return "tumor-tissue-ffpe", "Tumor tissue (FFPE)"
    if sample_material_type == "Tumor" and preservation_mode == "Other":
        return "tissue-other", "Other tissue storage"
    if sample_material_type == "Healthy colon tissue" and preservation_mode == "Cryopreservation":
        return "normal-tissue-frozen", "Normal tissue (frozen)"
    if sample_material_type == "Healthy colon tissue" and preservation_mode == "FFPE":
        return "normal-tissue-ffpe", "Normal tissue (FFPE)"
    if sample_material_type == "Healthy colon tissue" and preservation_mode == "Other":
        return "tissue-other", "Other tissue storage"
    if sample_material_type == "Other" and preservation_mode == "Cryopreservation":
        return "other-tissue-frozen", "Other tissue (frozen)"
    if sample_material_type == "Other" and preservation_mode == "FFPE":
        return "other-tissue-ffpe", "Other tissue (FFPE)"
    if sample_material_type == "Other" and preservation_mode == "Other":
        return "tissue-other", "Other tissue storage"
    return None, None


def find_histopathology(namespace, events):
    """
    Find a localization of primary tumor in form Histopathology.

    :param namespace: The namespace of file.
    :param events: XML element, where Histopathology can be stored.
    :return:
        The element with localization of primary tumor.
    """
    for event in events.findall(namespace + "Event"):
        if event.attrib.get("eventtype") == "Histopathology":
            localization =  event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_92_1")
            if localization is not None:
                localization = localization.text
            uicc_version = event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_73_3")
            if uicc_version is not None:
                uicc_version = uicc_version.text
            tnm_t = event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_71_1")
            if tnm_t is not None:
                tnm_t = tnm_t.text
            tnm_n = event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_77_1")
            if tnm_n is not None:
                tnm_n = tnm_n.text
            tnm_m = event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_75_1")
            if tnm_m is not None:
                tnm_m = tnm_m.text
            stage = event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_70_2")
            if stage is not None:
                stage = stage.text
            grade = event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_83_1")
            if grade is not None:
                grade = grade.text
            morphology = event.find(namespace + "LogitudinalData").find(namespace + "Form2").find(
                namespace + "Dataelement_91_1")
            if morphology is not None:
                morphology = morphology.text
            return localization, tnm_t, tnm_n, tnm_m, stage, uicc_version, grade, morphology


def create_resources(record, smart_client):
    """
    Create and store resources for one patient on FHIR server.

    :param record: The instance of class Record.
    :param smart_client: The FHIR client.
    :return:
        patient_url: The url of Resource Patient.
        time_observation_url: The url of Resource Observation. (TimeObservation)
        responses_url: The url of Resource Observation. (Response)
        surgeries_url: The url of Resource Procedure. (Surgery)
        radiations_url: The url of Resource Procedure. (RadiationTherapy)
        targeteds_url: The url of Resource Procedure. (TargetedTherapy)
        tnm_url: The url of Resource Observation. (TNM)
        condition_url: The url of Resource Condition.
        specimen_urls: The urls of Resources Specimen.
    """
    patient_url = create_patient(record.patient, smart_client)
    recurrence_url = None
    if record.recurrence is not None:
        recurrence_url = create_recurrence_observation(record.recurrence, patient_url, smart_client)
    time_observation_url = create_time_observation(record.time_observation, patient_url, smart_client)
    responses_url = []
    for response in record.responses:
        responses_url.append(create_response(response, patient_url, smart_client))
    surgeries_url = []
    for surgery in record.surgeries:
        surgeries_url.append(create_surgery(surgery, patient_url, smart_client))
    radiations_url = []
    for radiation in record.radiations:
        radiations_url.append(create_radiation_therapy(radiation, patient_url, smart_client))
    targeteds_url = []
    for targeted in record.targeteds:
        targeteds_url.append(create_targeted(targeted, patient_url, smart_client))
    tnm_url = create_tnm(record.tnm, patient_url, smart_client)
    condition_url = create_condition(record.condition, patient_url, smart_client)
    specimen_urls = []
    for specimen in record.specimens:
        specimen_urls.append(create_specimen(patient_url, specimen, smart_client))
    return (patient_url, recurrence_url, time_observation_url, responses_url, surgeries_url,
            radiations_url, targeteds_url, tnm_url, condition_url, specimen_urls)


def create_patient(patient_info, smart_client):
    """
    Create and store the Resource Patient on FHIR server.

    :param patient_info: The instance of class Patient.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Patient.
    """
    patient = p.Patient()
    if patient_info.birth_date is not None:
        patient.birthDate = patient_info.birth_date
    if patient_info.sex is not None:
        patient.gender = patient_info.sex
    if patient_info.deceased_boolean:
        patient.deceasedBoolean = patient_info.deceased_boolean
    if patient_info.timestamp is not None:
        patient.deceasedDateTime = FHIRDate(patient_info.timestamp)
    patient.identifier = [Identifier()]
    if patient_info.identifier is not None:
        patient.identifier[0].value = patient_info.identifier

    response = store_resources(smart_client, patient, "Patient")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id+16].decode("utf-8")


def create_recurrence_observation(recurrence_observation, patient_id, smart_client):
    """
    Create and store the Resource Observation on FHIR server.
    The resource should represent recurrence observation.

    Args:
        recurrence_observation: The recurrence diagnosis time interval.
        patient_id: The url of patient subject.
        smart_client: The FHIR client.

    Returns:
        The url of Resource Observation.
    """
    observation = o.Observation()

    # status
    observation.status = "final"

    # code
    code = Coding()
    code.system = "http://loinc.org"
    code.code = "21983-2"
    code.display = "Recurrence type first episode Cancer"

    code_wrapper = codeAbleConcept.CodeableConcept()
    code_wrapper.coding = [code]

    observation.code = code_wrapper

    # subject
    observation.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # valueQuantity
    value = Quantity()
    value.value = float(recurrence_observation)
    value.unit = "wk"
    value.system = "http://unitsofmeasure.org"
    value.code = "wk"

    observation.valueQuantity = value

    response = store_resources(smart_client, observation, "Observation")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id+16].decode("utf-8")


def create_time_observation(time_observation, patient_id, smart_client):
    """
    Create and store the Resource Observation on FHIR server.
    The resource should represent time observation.

    :param time_observation: The instance of class TimeObservation.
    :param patient_id: The url of patient subject.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Observation.
    """
    observation = o.Observation()

    # status
    observation.status = "final"

    # code
    code = Coding()
    code.system = "http://snomed.info/sct"
    code.code = "445320007"
    code.display = "Survival time (observable entity)"

    code_wrapper = codeAbleConcept.CodeableConcept()
    code_wrapper.coding = [code]

    observation.code = code_wrapper

    # subject
    observation.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # effectiveDateTime
    if time_observation.last_update is not None:
        observation.effectiveDateTime = FHIRDate(time_observation.last_update)

    # valueQuantity
    value = Quantity()
    if time_observation is not None:
        value.value = float(time_observation.overall_survival)
    else:
        value.value = 0
    value.unit = "wk"
    value.system = "http://unitsofmeasure.org"
    value.code = "wk"

    observation.valueQuantity = value

    response = store_resources(smart_client, observation, "Observation")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id+16].decode("utf-8")


def create_tnm(tnm, patient_id, smart_client):
    """
    Create and store the Resource Observation on FHIR server.
    The resource should represent tnm and other information about histopathology of primary findings.

    :param tnm: The instance of class TNM.
    :param patient_id: The url of patient subject.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Observation.
    """
    observation = o.Observation()

    # profile
    meta = Meta()
    meta.profile = ["https://www.vision-zero-oncology.de/fhir/StructureDefinition/uicc-tnm"]

    # status
    observation.status = "final"

    # code
    organization = Coding()
    organization.system = "http://snomed.info/sct"
    organization.code = "258235000"
    organization.display = "International Union Against Cancer (tumor staging)"

    group = Coding()
    group.system = "http://loinc.org"
    group.code = "21908-9"
    group.display = "Stage group.clinical Cancer"

    code = codeAbleConcept.CodeableConcept()
    code.coding = [organization, group]

    observation.code = code

    # subject
    observation.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # method
    uicc_version = Coding()
    uicc_version.code = "unknown"
    uicc_version.display = "unknown"
    uicc_version.system = "http://snomed.info/sct"
    if tnm.uicc_version_code is not None:
        uicc_version.code = tnm.uicc_version_code
    if tnm.uicc_version_display is not None:
        uicc_version.display = tnm.uicc_version_display

    method = codeAbleConcept.CodeableConcept()
    method.coding = [uicc_version]

    observation.method = method

    # valueCodeableConcept - stage
    stage = Coding()
    stage.code = "unknown"
    stage.display = "unknown"
    stage.system = "urn:oid:2.16.840.1.113883.15.16"
    if tnm.uicc_stage_code is not None:
        stage.code = tnm.uicc_stage_code
    if tnm.uicc_stage_display is not None:
        stage.display = tnm.uicc_stage_display

    value_codeable_concept = codeAbleConcept.CodeableConcept()
    value_codeable_concept.coding = [stage]

    observation.valueCodeableConcept = value_codeable_concept

    # components - TNM
    observation.component = []
    # T code
    pt_coding = Coding()
    pt_coding.system = "http://loinc.org"
    pt_coding.code = "21899-0"
    pt_coding.display = "Primary tumor.pathology Cancer"

    pt_wrapper = codeAbleConcept.CodeableConcept()
    pt_wrapper.coding = [pt_coding]

    component_t = o.ObservationComponent()
    component_t.code = pt_wrapper

    # T value
    pt_value_coding = Coding()
    pt_value_coding.code = "Unknown"
    pt_value_coding.display = "Unknown"
    pt_value_coding.system = "urn:oid:2.16.840.1.113883.15.16"
    if tnm.pT_code is not None:
        pt_value_coding.code = tnm.pT_code
    if tnm.pT_display is not None:
        pt_value_coding.display = tnm.pT_display

    pt_value_wrapper = codeAbleConcept.CodeableConcept()
    pt_value_wrapper.coding = [pt_value_coding]

    component_t.valueCodeableConcept = pt_value_wrapper

    # N code
    pn_coding = Coding()
    pn_coding.system = "http://loinc.org"
    pn_coding.code = "21900-6"
    pn_coding.display = "Regional lymph nodes.pathology [Class] Cancer"

    pn_wrapper = codeAbleConcept.CodeableConcept()
    pn_wrapper.coding = [pn_coding]

    component_n = o.ObservationComponent()
    component_n.code = pn_wrapper
    observation.component.append(component_n)

    # N value
    pn_value_coding = Coding()
    pn_value_coding.code = "unknown"
    pn_value_coding.display = "unknown"
    pn_value_coding.system = "urn:oid:2.16.840.1.113883.15.16"
    if tnm.pN_code is not None:
        pn_value_coding.code = tnm.pN_code
    if tnm.pN_display is not None:
        pn_value_coding.display = tnm.pN_display

    pn_value_wrapper = codeAbleConcept.CodeableConcept()
    pn_value_wrapper.coding = [pn_value_coding]

    component_n.valueCodeableConcept = pn_value_wrapper

    # M code
    pm_coding = Coding()
    pm_coding.system = "http://loinc.org"
    pm_coding.code = "21901-4"
    pm_coding.display = "Distant metastases.pathology [Class] Cancer"

    pm_wrapper = codeAbleConcept.CodeableConcept()
    pm_wrapper.coding = [pm_coding]

    component_m = o.ObservationComponent()
    component_m.code = pm_wrapper

    # M value
    pm_value_coding = Coding()
    pm_value_coding.code = "unknown"
    pm_value_coding.display = "unknown"
    pm_value_coding.system = "urn:oid:2.16.840.1.113883.15.16"
    if tnm.pM_code is not None:
        pm_value_coding.code = tnm.pM_code
    if tnm.pM_display is not None:
        pm_value_coding.display = tnm.pM_display

    pm_value_wrapper = codeAbleConcept.CodeableConcept()
    pm_value_wrapper.coding = [pm_value_coding]

    component_m.valueCodeableConcept = pm_value_wrapper

    # morphology
    morpho_coding = Coding()
    morpho_coding.system = "http://snomed.info/sct"
    morpho_coding.code = "1284862009"
    morpho_coding.display = "Histologic type of primary malignant neoplasm of cecum and/or colon and/or rectum (observable entity)"

    morpho_wrapper = codeAbleConcept.CodeableConcept()
    morpho_wrapper.coding = [morpho_coding]

    component_morpho = o.ObservationComponent()
    component_morpho.code = morpho_wrapper

    # morphology value
    morpho_value_coding = Coding()
    morpho_value_coding.code = "unknown"
    morpho_value_coding.display = "unknown"
    morpho_value_coding.system = "http://snomed.info/sct"
    if tnm.morphology_code is not None:
        morpho_value_coding.code = tnm.morphology_code
    if tnm.morphology_display is not None:
        morpho_value_coding.display = tnm.morphology_display

    morpho_value_wrapper = codeAbleConcept.CodeableConcept()
    morpho_value_wrapper.coding = [morpho_value_coding]

    component_morpho.valueCodeableConcept = morpho_value_wrapper

    # grade
    grade_coding = Coding()
    grade_coding.system = "http://snomed.info/sct"
    grade_coding.code = "395557000"
    grade_coding.display = "Tumor finding (finding)"

    grade_wrapper = codeAbleConcept.CodeableConcept()
    grade_wrapper.coding = [grade_coding]

    component_grade = o.ObservationComponent()
    component_grade.code = grade_wrapper

    # grade value
    grade_value_coding = Coding()
    grade_value_coding.code = "unknown"
    grade_value_coding.display = "unknown"
    grade_value_coding.system = "http://snomed.info/sct"
    if tnm.grade_code is not None:
        grade_value_coding.code = tnm.grade_code
    if tnm.grade_display is not None:
        grade_value_coding.display = tnm.grade_display

    grade_value_wrapper = codeAbleConcept.CodeableConcept()
    grade_value_wrapper.coding = [grade_value_coding]

    component_grade.valueCodeableConcept = grade_value_wrapper

    # add all
    observation.component = [component_t, component_n, component_m, component_morpho, component_grade]

    response = store_resources(smart_client, observation, "Observation")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id+16].decode("utf-8")


def create_surgery(surgery_info, patient_id, smart_client):
    """
    Create and store the Resource Procedure on FHIR server.
    The resource should represent surgery.

    :param surgery_info: The instance of class Surgery.
    :param patient_id: The url of patient subject.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Procedure.
    """
    surgery = pro.Procedure()

    # status
    surgery.status = "final"

    # code
    if surgery_info.surgery_code is not None and surgery_info.surgery_name is not None:
        coding = Coding()
        coding.code = str(surgery_info.surgery_code)
        coding.display = surgery_info.surgery_name
        coding.system = "http://snomed.info/sct"

        clinical_status = codeAbleConcept.CodeableConcept()
        clinical_status.coding = [coding]

        surgery.code = clinical_status

    # subject
    surgery.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # performedPeriod
    if surgery_info.start is not None:
        performed_period = period.Period()
        performed_period.start = FHIRDate(surgery_info.start)

        surgery.performedPeriod = performed_period

    # bodySite
    if surgery_info.body_site_code is not None and surgery_info.body_site_name is not None:
        coding = Coding()
        coding.code = str(surgery_info.body_site_code)
        coding.display = surgery_info.body_site_name
        coding.system = "http://snomed.info/sct"

        body_site = codeAbleConcept.CodeableConcept()
        body_site.coding = [coding]

        surgery.bodySite = [body_site]

    #  outcome
    if surgery_info.surgery_radicality_name and surgery_info.surgery_radicality_code:
        coding = Coding()
        coding.code = str(surgery_info.surgery_radicality_code)
        coding.display = surgery_info.surgery_radicality_name
        coding.system = "http://snomed.info/sct"

        radicality = codeAbleConcept.CodeableConcept()
        radicality.coding = [coding]

        surgery.outcome = radicality

    # note
    if surgery_info.note is not None:
        note = anno.Annotation()
        note.text = surgery_info.note

        surgery.note = [note]

    response = store_resources(smart_client, surgery, "Procedure")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def create_radiation_therapy(radiation_info, patient_id, smart_client):
    """
    Create and store the Resource Procedure on FHIR server.
    The resource should represent surgery.

    :param radiation_info: The instance of class RadiationTherapy.
    :param patient_id: The url of patient subject.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Procedure.
    """
    radiation = pro.Procedure()

    # status
    radiation.status = "completed"

    # code
    coding = Coding()
    coding.code = "108290001"
    coding.display = "Radiation therapy"
    coding.system = "http://snomed.info/sct"

    code = codeAbleConcept.CodeableConcept()
    code.coding = [coding]

    radiation.code = code

    # subject
    radiation.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # start
    radiation_period = period.Period()
    if radiation_info.start is not None:
        radiation_period.start = radiation_info.start

    # end
    if radiation_info.end is not None:
        radiation_period.end = radiation_info.end

    radiation.performedPeriod = radiation_period

    response = store_resources(smart_client, radiation, "Procedure")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def create_response(response_info, patient_id, smart_client):
    """
    Create and store the Resource Observation on FHIR server.
    The resource should represent Response to Therapy.

    :param response_info: The instance of class Response.
    :param patient_id: The url of patient subject.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Observation.
    """
    observation = o.Observation()

    # status
    observation.status = "final"

    # category
    coding = Coding()
    coding.code = "therapy"
    coding.display = "Therapy"
    coding.system = "http://terminology.hl7.org/CodeSystem/observation-category"

    category = codeAbleConcept.CodeableConcept()
    category.coding = [coding]

    observation.category = [category]

    # code
    coding = Coding()
    coding.code = "100633-7"
    coding.display = "Rapid response team Hospital Progress note"
    coding.system = "http://loinc.org"

    code = codeAbleConcept.CodeableConcept()
    code.coding = [coding]

    observation.code = code

    # subject
    observation.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # effectiveDateTime
    if response_info.time is not None:
        observation.effectiveDateTime = FHIRDate(response_info.time)

    # valueCodeableConcept
    if response_info.code is not None and response_info.display is not None:
        coding = Coding()
        coding.code = str(response_info.code)
        coding.display = response_info.display
        coding.system = "http://snomed.info/sct"

        valueCodeableConcept = codeAbleConcept.CodeableConcept()
        valueCodeableConcept.coding = [coding]

        observation.valueCodeableConcept = valueCodeableConcept

    response = store_resources(smart_client, observation, "Observation")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def create_condition(condition_info, patient_id, smart_client):
    """
    Create and store the Resource Condition on FHIR server.

    :param condition_info: The instance of class Condition.
    :param patient_id: The url of relevant Resource Patient.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Condition.
    """
    condition = c.Condition()
    if condition_info.date_diagnosis is not None:
        condition.recordedDate = FHIRDate(condition_info.date_diagnosis)

    # Clinical Status

    coding = Coding()
    coding.code = "unknown"
    coding.display = "Unknown"
    coding.system = "http://terminology.hl7.org/CodeSystem/condition-clinical"

    clinical_status = codeAbleConcept.CodeableConcept()
    clinical_status.coding = [coding]

    condition.clinicalStatus = clinical_status

    # onsetDateTime
    if condition_info.date_diagnosis is not None:
        date_time = FHIRDate(condition_info.date_diagnosis)
        condition.onsetDateTime = date_time

    # subject (patient)
    condition.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # code
    mapping = {"C18.0": "Malignant neoplasm of cecum",
               "C18.1": "Malignant neoplasm of appendix",
               "C18.2": "Malignant neoplasm of ascending colon",
               "C18.3": "Malignant neoplasm of hepatic flexure",
               "C18.4": "Malignant neoplasm of transverse colon",
               "C18.5": "Malignant neoplasm of splenic flexure",
               "C18.6": "Malignant neoplasm of descending colon",
               "C18.7": "Malignant neoplasm of sigmoid colon",
               "C18.8": "Malignant neoplasm of overlapping sites of colon",
               "C18.9": "Malignant neoplasm of colon, unspecified",
               "C19": "Malignant neoplasm of rectosigmoid junction",
               "C20": "Malignant neoplasm of rectum"}
    if condition_info.histopathology is not None:
        diagnosis_index = condition_info.histopathology.find("C", -5)
        code = condition_info.histopathology[diagnosis_index:]
        coding = Coding()
        coding.code = code
        coding.display = mapping[code]
        coding.system = "http://hl7.org/fhir/sid/icd-10"

        text = code + ": " + mapping[code]

        code_in_json = codeAbleConcept.CodeableConcept()
        code_in_json.text = text
        code_in_json.coding = [coding]

        condition.code = code_in_json

    response = store_resources(smart_client, condition, "Condition")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def create_specimen(patient_id, specimen_info, smart_client):
    """
    Create and store the Resource Specimen on FHIR server.

    :param patient_id: The url of relevant Resource Patient.
    :param specimen_info: The instance of class Specimen.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Specimen.
    """
    specimen = s.Specimen()

    # collection collected
    if specimen_info.year_of_sample_connection is not None:
        collection = SpecimenCollection()
        collection.collectedDateTime = specimen_info.year_of_sample_connection
        specimen.collection = collection

    # identifier
    if specimen_info.identifier:
        identifier = Identifier()
        identifier.value = specimen_info.identifier
        specimen.identifier = [identifier]

    # type.coding (code, display, system)
    if specimen_info.sample_material_type_code is not None and specimen_info.sample_material_type_display is not None:
        coding = Coding()
        coding.code = specimen_info.sample_material_type_code
        coding.display = specimen_info.sample_material_type_display
        coding.system = "“https://fhir.bbmri.de/CodeSystem/SampleMaterialType"

        type = codeAbleConcept.CodeableConcept()
        type.coding = [coding]

        specimen.type = type

    # subject
    specimen.subject = FHIRReference({'reference': "Patient/" + patient_id})

    response = store_resources(smart_client, specimen, "Specimen")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def create_targeted(targeted_info, patient_id, smart_client):
    """
    Create and store the Resource Procedure on FHIR server.
    The resource should represent surgery.

    :param targeted_info: The instance of class TargetedTherapy.
    :param patient_id: The url of patient subject.
    :param smart_client: The FHIR client.
    :return:
        The url of Resource Procedure.
    """
    targeted = pro.Procedure()

    # status
    targeted.status = "unknown"

    # code
    coding = Coding()
    coding.code = "targeted-therapy"
    coding.display = "Targeted therapy"
    coding.system = "http://hl7.org/fhir/uv/ichom-breast-cancer/CodeSystem/TreatmentTypesCodeSystem"

    code = codeAbleConcept.CodeableConcept()
    code.coding = [coding]

    targeted.code = code

    # subject
    targeted.subject = FHIRReference({'reference': "Patient/" + patient_id})

    # start
    targeted_period = period.Period()
    if targeted_info.start is not None:
        targeted_period.start = targeted_info.start

    # end
    if targeted_info.end is not None:
        targeted_period.end = targeted_info.end

    targeted.performedPeriod = targeted_period

    # note
    note = anno.Annotation()
    note.text = "Code for targeted therapy is taken from breast cancer codes."

    response = store_resources(smart_client, targeted, "Procedure")
    resource_on_server = response.content
    index_id = resource_on_server.rfind(b'"id"') + 6
    return resource_on_server[index_id:index_id + 16].decode("utf-8")


def store_resources(smart_client, file, type):
    """
    Store resources on FHIR server.

    :param smart_client: The FHIR client.
    :param file: FHIR model, precursor of FHIR json.
    :param type: Type of Resource.
    :return:
    """
    server = smart_client.server
    resource = file.as_json()
    return server.post_json(path=type, resource_json=resource)

def create_files(data, smart_client):
    """
    Create files with Resurces IDs for further processing.

    :param data: Data prepared in the list of instances of classes: Patient, Condition, Specimen.
    :param smart_client: The FHIR client.
    :return:
        None
    """
    # resources
    patients = []
    recurrence = []
    time_observations = []
    surgeries = []
    radiations = []
    targeteds = []
    responses = []
    tnms = []
    conditions = []
    specimens = []
    for record in data:
        (patient_url, recurrence_url, time_observation_url, responses_url, surgeries_url, radiations_url,
         targeteds_url, tnm_url, condition_url, specimen_urls) = create_resources(record, smart_client)
        patients.append(patient_url)
        time_observations.append(time_observation_url)
        if recurrence_url is not None:
            recurrence.append(recurrence_url)
        tnms.append(tnm_url)
        surgeries += surgeries_url
        radiations += radiations_url
        targeteds += targeteds_url
        responses += responses_url
        conditions.append(condition_url)
        specimens += specimen_urls
    file_patients_ids = open("patients_ids.txt", "w")
    file_recurrence_ids = open("recurrence_ids.txt", "w")
    file_time_observation_ids = open("time_observation_ids.txt", "w")
    file_tnm_ids = open("tnm_ids.txt", "w")
    file_surgery_ids = open("surgery_ids.txt", "w")
    file_radiation_ids = open("radiation_ids.txt", "w")
    file_targeteds_ids = open("targeteds_ids.txt", "w")
    file_response_ids = open("response_ids.txt", "w")
    file_conditions_ids = open("conditions_ids.txt", "w")
    file_specimens_ids = open("specimens_ids.txt", "w")
    for record in patients:
        file_patients_ids.write(record + "\n")
    for record in recurrence:
        file_recurrence_ids.write(record + "\n")
    for record in time_observations:
        file_time_observation_ids.write(record + "\n")
    for record in tnms:
        file_tnm_ids.write(record + "\n")
    for record in surgeries:
        file_surgery_ids.write(record + "\n")
    for record in radiations:
        file_radiation_ids.write(record + "\n")
    for record in targeteds:
        file_targeteds_ids.write(record + "\n")
    for record in responses:
        file_response_ids.write(record + "\n")
    for record in conditions:
        file_conditions_ids.write(record + "\n")
    for record in specimens:
        file_specimens_ids.write(record + "\n")
    file_patients_ids.close()
    file_time_observation_ids.close()
    file_tnm_ids.close()
    file_surgery_ids.close()
    file_radiation_ids.close()
    file_targeteds_ids.close()
    file_response_ids.close()
    file_conditions_ids.close()
    file_specimens_ids.close()
    return None


def create_graphs_extra(file_name, client):
    """
    Store data from file_name in provided server, then create
    pandas dataframes and run all quality checks from quality_checks_fhir_extra.py

    Args:
        file_name: Name of input file with data.
        client: FHIR client.

    Returns:
        List of figures from data quality checks.

    """
    read_xml_and_create_resources(file_name, client)

    patient_df = create_patient_data_frame(client.server)
    recurrence_df = create_recurrence_df(client.server)
    tnm_df = create_tnm_dataframe(client.server)
    time_df = create_time_observation_df(client.server)
    response_df = create_response_df(client.server)
    radiation_df = create_radiation_df(client.server)
    targeted_df = create_targeted_therapy_dataframe(client.server)
    surgery_df = create_surgery_df(client.server)
    specimen_df = create_specimen_data_frame(client.server)
    condition_df = create_condition_data_frame(client.server)

    graphs = [
    # completeness
    completeness(patient_df),
    completeness(recurrence_df),
    completeness(tnm_df),
    completeness(time_df),
    completeness(response_df),
    completeness(radiation_df),
    completeness(targeted_df),
    completeness(surgery_df),
    completeness(specimen_df),
    completeness(condition_df),

    # warnings:
    last_update_before_initial_diagnosis(condition_df, time_df),
    vital_check_date_is_equal_to_initial_diagnosis_date(condition_df, time_df),
    suspicious_survival_information(condition_df, time_df),
    age_at_primary_diagnosis(patient_df, condition_df),
    suspiciously_long_survival(patient_df, time_df, condition_df),

    vital_status_timestamp_missing(patient_df, time_df),
    vital_status_timestamp_is_in_the_future(time_df),
    diagnosis_in_future(condition_df),
    surgery_and_histological_location_do_not_match_only_one(condition_df, surgery_df),
    surgery_and_histological_location_do_not_match_multiple(condition_df, surgery_df),

    mismatch_between_surgery_location_and_surgery_type(surgery_df),
    end_time_is_before_start_time(radiation_df),
    end_time_is_before_start_time(targeted_df),
    event_starts_or_ends_after_survival_of_patient_procedure(patient_df, radiation_df, time_df, condition_df),
    event_starts_or_ends_after_survival_of_patient_procedure(patient_df, targeted_df, time_df, condition_df),

    event_starts_or_ends_after_survival_of_patient(patient_df, surgery_df, time_df, condition_df),
    event_starts_or_ends_after_survival_of_patient(patient_df, response_df, time_df, condition_df),
    start_of_response_to_therapy_is_before_diagnosis(response_df, condition_df),
    patient_died_but_last_response_is_complete(patient_df, response_df),
    start_of_response_to_therapy_is_in_the_future(response_df),

    start_of_therapy_is_before_diagnosis(radiation_df, condition_df),
    start_of_therapy_is_before_diagnosis(targeted_df, condition_df),
    start_of_therapy_is_before_diagnosis(surgery_df, condition_df),
    start_of_treatment_is_in_the_future(radiation_df, condition_df),
    start_of_treatment_is_in_the_future(targeted_df, condition_df),

    start_of_treatment_is_in_the_future(surgery_df, condition_df),
    end_of_treatment_is_in_the_future(radiation_df),
    end_of_treatment_is_in_the_future(targeted_df),
    non_surgery_therapy_starts_and_ends_in_week_0_since_initial_diagnosis(radiation_df, condition_df),
    non_surgery_therapy_starts_and_ends_in_week_0_since_initial_diagnosis(targeted_df, condition_df),

    mismatch_between_provided_and_computed_stage_value(tnm_df),
    sus_tnm_combo_for_uicc_version_or_uncomputable_stage(tnm_df),
    pnx_and_missing_uicc_stage(tnm_df),

    # reports:
    create_plot_without_preservation_mode(patient_df, specimen_df),
    create_plots_without_response_to_therapy(patient_df, response_df),
    get_patients_with_preservation_mode_but_without_ffpe(patient_df, specimen_df),
    treatment_after_complete_response_without_recurrence_diagnosis(patient_df, response_df, condition_df, recurrence_df)
    ]

    for i in range(len(graphs)):
        graphs[i] = graphs[i].to_json()

    return graphs
