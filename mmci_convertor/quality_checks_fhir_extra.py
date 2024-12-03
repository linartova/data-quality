import pandas as pd
import plotly.express as px
from _datetime import datetime
from load_data_fhir_extra import provide_server_connection, read_xml_and_create_resources


def create_patient_data_frame(server):
    """
    Convert FHIR resources Patient into pandas dataframe.

    Args:
        server: FHIR server.

    Returns:
        Dataframe.

    """
    all_dict = { "subject" : [],
                "gender" : [],
                "birthDate" : [],
                "deceasedBoolean" : [],
                "deceasedDateTime" : [],
                "identifier" : []
                }
    all_times = pd.DataFrame(all_dict)
    with open('patients_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Patient/' + id)

            # subject
            result["subject"] = id

            # gender
            gender = data.pop("gender")
            result["gender"] = gender

            # birthDate
            birth_date = data.pop("birthDate")
            result["birthDate"] = birth_date

            # deceasedBoolean
            deceased_boolean = data.pop("deceasedBoolean")
            result["deceasedBoolean"] = deceased_boolean

            # deceasedDateTime
            deceased_date_time = None if deceased_boolean is False else data.pop("deceasedDateTime")
            result["deceasedDateTime"] = deceased_date_time

            # identifier
            identifier_wrapper = data.pop("identifier").pop()
            identifier = identifier_wrapper.pop("value")
            result["identifier"] = identifier

            next_df = pd.DataFrame([result])
            all_times = pd.concat([all_times, next_df])
    all_times['birthDate'] = pd.to_datetime(all_times['birthDate'])
    all_times['deceasedDateTime'] = pd.to_datetime(all_times['deceasedDateTime'])
    return all_times


def create_tnm_dataframe(server):
    """
    Convert FHIR resources Observation representing TNM and
     other histopathology information into pandas dataframe.

    Args:
        server: FHIR server.

    Returns:
        Dataframe.

    """
    all_dict = {"method_coding_code" : [],
                "method_coding_display" : [],
                "subject" : [],
                "stage_code" : [],
                "stage_display" : [],
                "t_coding_code" : [],
                "t_coding_display" : [],
                "n_coding_code" : [],
                "n_coding_display" : [],
                "m_coding_code" : [],
                "m_coding_display" : [],
                "morpho_coding_code" : [],
                "morpho_coding_display" : [],
                "grade_coding_code" : [],
                "grade_coding_display" : []
                }
    all_tnm = pd.DataFrame(all_dict)
    with open('tnm_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Observation/' + id)

            # method
            method = data.pop("method")
            method_coding = method.pop("coding").pop()
            result["method_coding_code"] = method_coding.pop("code")
            result["method_coding_display"] = method_coding.pop("display")

            # subject
            subject = data.pop("subject")
            reference = subject.pop("reference")
            result["subject"] = reference

            # stage
            value = data.pop("valueCodeableConcept")
            coding = value.pop("coding").pop()
            if "code" in coding.keys():
                stage_code = coding.pop("code")
            else:
                stage_code = None
            if "display" in coding.keys():
                stage_display = coding.pop("display")
            else:
                stage_display = None
            result["stage_code"] = stage_code
            result["stage_display"] = stage_display

            component = data.pop("component")

            # grade
            grade = component.pop()
            grade_value = grade.pop("valueCodeableConcept")
            grade_coding = grade_value.pop("coding").pop()
            grade_coding_code = grade_coding.pop("code")
            grade_coding_display = grade_coding.pop("display")
            result["grade_coding_code"] = grade_coding_code
            result["grade_coding_display"] = grade_coding_display

            # morphology
            morpho = component.pop()
            morpho_value = morpho.pop("valueCodeableConcept")
            morpho_coding = morpho_value.pop("coding").pop()
            morpho_coding_code = morpho_coding.pop("code")
            morpho_coding_display = morpho_coding.pop("display")
            result["morpho_coding_code"] = morpho_coding_code
            result["morpho_coding_display"] = morpho_coding_display

            # M
            m = component.pop()
            m_value = m.pop("valueCodeableConcept")
            m_coding = m_value.pop("coding").pop()
            m_coding_code = m_coding.pop("code")
            m_coding_display = m_coding.pop("display")
            result["m_coding_code"] = m_coding_code
            result["m_coding_display"] = m_coding_display

            # N
            n = component.pop()
            n_value = n.pop("valueCodeableConcept")
            n_coding = n_value.pop("coding").pop()
            n_coding_code = n_coding.pop("code")
            n_coding_display = n_coding.pop("display")
            result["n_coding_code"] = n_coding_code
            result["n_coding_display"] = n_coding_display

            # T
            t = component.pop()
            t_value = t.pop("valueCodeableConcept")
            t_coding = t_value.pop("coding").pop()
            t_coding_code = t_coding.pop("code")
            t_coding_display = t_coding.pop("display")
            result["t_coding_code"] = t_coding_code
            result["t_coding_display"] = t_coding_display

            next_df = pd.DataFrame([result])
            all_tnm = pd.concat([all_tnm, next_df])
    return all_tnm


def create_time_observation_df(server):
    """
    Convert FHIR resources Observation representing
     time information into pandas dataframe.

    Args:
        server: FHIR server.

    Returns:
        Dataframe.

    """
    all_dict = {"last_update" : [],
                "subject" : [],
                "overall_survival" : []
                }
    all_times = pd.DataFrame(all_dict)
    with open('time_observation_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Observation/' + id)

            # last_update
            last_update = data.pop("effectiveDateTime")
            result["last_update"] = last_update

            # subject
            subject = data.pop("subject")
            reference = subject.pop("reference")
            result["subject"] = reference

            # overall_survival
            value_quantity = data.pop("valueQuantity")
            value = value_quantity.pop("value")
            result["overall_survival"] = value

            next_df = pd.DataFrame([result])
            all_times = pd.concat([all_times, next_df])
    all_times['last_update'] = pd.to_datetime(all_times['last_update'])
    return all_times


def create_radiation_df(server):
    """
    Convert FHIR resources Procedure representing
     Radiation Therapy into pandas dataframe.

    Args:
        server: FHIR server.

    Returns:
        Dataframe.

    """
    all_dict = {"subject" : [],
                "start" : [],
                "end" : []
                }
    all_times = pd.DataFrame(all_dict)
    with open('radiation_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Procedure/' + id)

            # TODO subject
            subject = data.pop("subject")
            reference = subject.pop("reference")
            result["subject"] = reference

            # start
            performed_period = data.pop("performedPeriod")
            start = performed_period.pop("start")
            result["start"] = start

            # end
            end = performed_period.pop("end")
            result["end"] = end

            next_df = pd.DataFrame([result])
            all_times = pd.concat([all_times, next_df])
    all_times['start'] = pd.to_datetime(all_times['start'])
    all_times['end'] = pd.to_datetime(all_times['end'])
    return all_times


def create_response_df(server):
    """
    Convert FHIR resources Observation representing
     response to therapy into pandas dataframe.

    Args:
        server: FHIR server.

    Returns:
        Dataframe.

    """
    all_dict = {"subject": [],
                "date": [],
                "code": [],
                "display": []
                }
    all_times = pd.DataFrame(all_dict)
    with open('response_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Observation/' + id)

            # subject
            subject = data.pop("subject")
            reference = subject.pop("reference")
            result["subject"] = reference

            # date
            date = data.pop("effectiveDateTime")
            result["date"] = date

            # code
            value = data.pop("valueCodeableConcept")
            coding = value.pop("coding").pop()
            code = coding.pop("code")
            result["code"] = code

            # display
            display = coding.pop("display")
            result["display"] = display

            next_df = pd.DataFrame([result])
            all_times = pd.concat([all_times, next_df])
    all_times['date'] = pd.to_datetime(all_times['date'])
    return all_times


def create_surgery_df(server):
    """
    Convert FHIR resources Procedure representing
     Surgery into pandas dataframe.

    Args:
        server: FHIR server.

    Returns:
        Dataframe.

    """
    all_dict = {"subject": [],
                "surgery_code": [],
                "surgery_display": [],
                "start": [],
                "body_site_code": [],
                "body_site_display": [],
                "outcome_code": [],
                "outcome_display": [],
                "note_text": []
                }
    all_times = pd.DataFrame(all_dict)
    with open('surgery_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Procedure/' + id)

            # subject
            subject = data.pop("subject")
            reference = subject.pop("reference")
            result["subject"] = reference

            # surgery code
            surgery_code = data.pop("code")
            coding = surgery_code.pop("coding").pop()
            code = coding.pop("code")
            result["surgery_code"] = code

            # surgery display
            display = coding.pop("display")
            result["surgery_display"] = display

            # start
            performed_period = data.pop("performedPeriod")
            start = performed_period.pop("start")
            result["start"] = start

            # bodySite code
            body_site = data.pop("bodySite").pop()
            body_site_coding = body_site.pop("coding").pop()
            body_site_code = body_site_coding.pop("code")
            result["body_site_code"] = body_site_code

            # bodySite display
            if "display" in body_site_coding:
                body_site_display = body_site_coding.pop("display")
            else:
                body_site_display = None
            result["body_site_display"] = body_site_display

            # outcome_code
            outcome = data.pop("outcome")
            outcome_coding = outcome.pop("coding").pop()
            outcome_code = outcome_coding.pop("code")
            result["outcome_code"] = outcome_code

            # outcome display
            outcome_display = outcome_coding.pop("display")
            result["outcome_display"] = outcome_display

            # note
            note = data.pop("note").pop()
            note_text = note.pop("text")
            result["note_text"] = note_text

            next_df = pd.DataFrame([result])
            all_times = pd.concat([all_times, next_df])
    all_times['start'] = pd.to_datetime(all_times['start'])
    return all_times


def create_specimen_data_frame(server):
    """
    Create data frame from Resource Specimen.

    :param server: FHIR server.
    :return:
        Specimen data frame.
    """
    all_dict = {"collected_date_time": [],
                "identifier": [],
                "type_code": [],
                "type_display" : [],
                "subject" : []
                }
    all_times = pd.DataFrame(all_dict)
    with open('specimens_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Specimen/' + id)

            # collection collected
            collection = data.pop("collection")
            collected_date_time = collection.pop("collectedDateTime")
            result["collected_date_time"] = collected_date_time

            # identifier
            identifier_wrapper = data.pop("identifier").pop()
            identifier = identifier_wrapper.pop("value")
            result["identifier"] = identifier

            # type code
            type = data.pop("type")
            type_coding = type.pop("coding").pop()
            type_code = type_coding.pop("code")
            result["type_code"] = type_code

            # type display
            type_display = type_coding.pop("display")
            result["type_display"] = type_display

            # subject
            subject = data.pop("subject")
            reference = subject.pop("reference")
            result["subject"] = reference

            next_df = pd.DataFrame([result])
            all_times = pd.concat([all_times, next_df])
    all_times['collected_date_time'] = pd.to_datetime(all_times['collected_date_time'])
    return all_times


def create_condition_data_frame(server):
    """
    Create data frame from Resource Condition.

    :param server: FHIR server.
    :return:
        Condition data frame.
    """
    all_dict = {"recorded_date": [],
                "onset_date_time": [],
                "code_code": [],
                "code_display" : [],
                "subject" : []
                }
    all_times = pd.DataFrame(all_dict)
    with open('conditions_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Condition/' + id)

            # recordedDate
            recorded_date = data.pop("recordedDate")
            result["recorded_date"] = recorded_date

            # onsetDateTime
            onset_date_time = data.pop("onsetDateTime")
            result["onset_date_time"] = onset_date_time

            # code
            code = data.pop("code")
            code_coding = code.pop("coding").pop()
            code_code = code_coding.pop("code")
            result["code_code"] = code_code

            # display
            code_display = code_coding.pop("display")
            result["code_display"] = code_display

            # subject
            subject = data.pop("subject")
            reference = subject.pop("reference")
            result["subject"] = reference

            next_df = pd.DataFrame([result])
            all_times = pd.concat([all_times, next_df])
    all_times['recorded_date'] = pd.to_datetime(all_times['recorded_date'])
    all_times['onset_date_time'] = pd.to_datetime(all_times['onset_date_time'])
    return all_times


def create_targeted_therapy_dataframe(server):
    """
   Convert FHIR resources Procedure representing
    Targeted Therapy into pandas dataframe.

    Args:
        server: FHIR server.

    Returns:
        Dataframe.

    """
    all_dict = {"subject": [],
                "start": [],
                "end": []
                }
    all_times = pd.DataFrame(all_dict)
    with open('targeteds_ids.txt', 'r') as ids:
        for id in ids:
            result = {}
            id = id[:-1]
            data = server.request_json('http://localhost:8080/fhir/Procedure/' + id)

            # TODO subject
            subject = data.pop("subject")
            reference = subject.pop("reference")
            result["subject"] = reference

            # start
            performed_period = data.pop("performedPeriod")
            start = performed_period.pop("start")
            result["start"] = start

            # end
            end = performed_period.pop("end")
            result["end"] = end

            next_df = pd.DataFrame([result])
            all_times = pd.concat([all_times, next_df])
    all_times['start'] = pd.to_datetime(all_times['start'])
    all_times['end'] = pd.to_datetime(all_times['end'])
    return all_times


def completeness(df):
    """
    Data quality check for completeness.

    :param df: Input data frame
    :return:
        Graph of completeness.
    """
    missing_values = pd.isnull(df).sum()
    fig = px.scatter(missing_values)
    fig.update_layout(xaxis_title='count of missing values', yaxis_title='attribute', title="Missing values",
                      showlegend=False)
    return fig


def uniqueness(df, name):
    """
    Data quality check for uniqueness.

    :param df: Input data frame
    :param name: Name of processed data frame.
    :return:
        Graph of uniqueness.
    """
    df = df.copy()
    count_of_rows = df.shape[0]
    df.drop(columns="meta_versionId", inplace=True)
    df.drop(columns="meta_lastUpdated", inplace=True)
    df.drop(columns="id", inplace=True)

    count_of_duplicates = df.duplicated().sum()
    result = {
        "Duplicates": ["Unique rows", "Duplicated"],
        "Count": [count_of_rows - count_of_duplicates, count_of_duplicates]
    }
    dff = pd.DataFrame(result)
    fig = px.pie(dff, values='Count', names='Duplicates', title='Duplicated values')

    df.to_csv("reports/fhir/extra/uniqueness" + name + ".csv", index=False)
    return fig

def conformance_patient(df):
    """
    Data quality check for conformance of Resource Patient.

    :param df: Patient data frame.
    :return:
        Graph of conformance.
    """
    # gender
    count_of_rows = df.shape[0]
    gender_check_count = df["gender"].isin(["male", "female", "other", "unknown"]).sum()

    # birthDate
    df["birthDate"] = pd.to_datetime(df["birthDate"], errors="coerce")
    birth_date_check = df.isnull()["birthDate"].sum()

    result = {
        "Records": ["Number of records", "Invalid gender", "Invalid birth date"],
        "Count": [count_of_rows, count_of_rows - gender_check_count, birth_date_check]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig



def conformance_condition(df):
    """
    Data quality check for conformance of Resource Conformance.

    :param df: Conformance data frame.
    :return:
        Graph of conformance.
    """
    count_of_rows = df.shape[0]

    # recordedDate
    df["recordedDate"] = pd.to_datetime(df["recordedDate"],
                                        errors="coerce")
    recorded_date_check = df.isnull()["recordedDate"].sum()

    # onsetDateTime
    df["onsetDateTime"] = pd.to_datetime(df["onsetDateTime"],
                                         errors="coerce")
    onset_date_time_check = df.isnull()["onsetDateTime"].sum()

    # clinical Status
    clinical_status_coding_code_check = df[
        "clinicalStatus_coding_code"].isin(
        ["active", "recurrence", "relapse", "inactive",
         "remission", "resolved", "unknown"]).sum()

    clinical_status_coding_display_check = df[
        "clinicalStatus_coding_display"].isin(
        ["active", "recurrence", "relapse", "inactive",
         "remission", "resolved", "unknown"]).sum()

    # coding system
    code_coding_code_check = df["code_coding_code"].isin(["C18.0",
               "C18.1", "C18.2", "C18.3", "C18.4", "C18.5", "C18.6",
               "C18.7", "C18.8", "C18.9", "C19", "C20"]).sum()

    code_coding_display_check = df["code_coding_display"].isin([
        "Malignant neoplasm of cecum",
        "Malignant neoplasm of appendix",
        "Malignant neoplasm of ascending colon",
        "Malignant neoplasm of hepatic flexure",
        "Malignant neoplasm of transverse colon",
        "Malignant neoplasm of splenic flexure",
        "Malignant neoplasm of descending colon",
        "Malignant neoplasm of sigmoid colon",
        "Malignant neoplasm of overlapping sites of colon",
        "Malignant neoplasm of colon, unspecified",
        "Malignant neoplasm of rectosigmoid junction",
        "Malignant neoplasm of rectum"]).sum()

    code_text_check = df["code_text"].isin([
        "C18.0 Malignant neoplasm of cecum",
        "C18.1 Malignant neoplasm of appendix",
        "C18.2 Malignant neoplasm of ascending colon",
        "C18.3 Malignant neoplasm of hepatic flexure",
        "C18.4 Malignant neoplasm of transverse colon",
        "C18.5 Malignant neoplasm of splenic flexure",
        "C18.6 Malignant neoplasm of descending colon",
        "C18.7 Malignant neoplasm of sigmoid colon",
        "C18.8 Malignant neoplasm of overlapping sites of colon",
        "C18.9 Malignant neoplasm of colon, unspecified",
        "C19 Malignant neoplasm of rectosigmoid junction",
        "C20 Malignant neoplasm of rectum"
    ]).sum()

    result = {
        "Records": ["Number of records", "recorded_date_check",
                    "onset_date_time_check", "clinical_status_coding_code_check",
                    "clinical_status_coding_display_check", "code_coding_code_check",
                    "code_coding_display_check", "code_text_check"],
        "Count": [count_of_rows, recorded_date_check,
                  onset_date_time_check, count_of_rows - clinical_status_coding_code_check,
                  clinical_status_coding_display_check, count_of_rows - code_coding_code_check,
                  count_of_rows - code_coding_display_check, code_text_check]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


def conformance_specimen(df):
    """
    Data quality check for conformance of Resource Specimen.

    :param df: Specimen data frame.
    :return:
        Graph of conformance.
    """
    count_of_rows = df.shape[0]

    # type text
    type_text_check = df["type_text"].isin(["Tumor", "Other", "Healthy colon tissue"]).sum()

    # collected Date Time
    df["collection_collectedDateTime"] = \
        pd.to_datetime(df["collection_collectedDateTime"], errors="coerce")
    collection_collectedDateTime_check = df.isnull()["collection_collectedDateTime"].sum()

    result = {
        "Records": ["Number of records", "type_text_check", "collection_collectedDateTime_check"],
        "Count": [count_of_rows, count_of_rows - type_text_check, collection_collectedDateTime_check]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


def conformance_relational(df, server):
    """
    Data quality check for relational conformance of Resource.

    :param df: Data frame.
    :param server: FHIR server.
    :return:
        Graph of relational conformance.
    """
    count_of_rows = df.shape[0]
    count_of_invalid_references = 0

    for index in df.index:
        link = df['id'][index]
        subject_reference = df['subject_reference'][index]
        resource_type = df["resourceType"][index]
        try:
            server.request_json('http://localhost:8080/fhir/' + subject_reference)
        except:
            count_of_invalid_references += 1
    result = {
        "Records": ["Number of records", "Invalid references"],
        "Count": [count_of_rows, count_of_invalid_references]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


def get_birthDay(pdf, subject_reference):
    """
    Helper function for conformance_computational.

    :param pdf: Patient data frame.
    :param subject_reference: Patient id.
    :return:
        Birthday of Patient.
    """
    subject_reference_split = subject_reference.split("/")
    patient_id = None
    if len(subject_reference_split) == 2:
        patient_id = subject_reference_split[1]
    birthDate = None
    if patient_id is not None:
        patient = pdf.loc[pdf['id'] == patient_id]
        if not patient.empty:
            patient = patient.iloc[0]
            birthDate = patient['birthDate']
    return birthDate


def conformance_computational(pdf, sdf, cdf):
    """
    Data quality check for computational conformance

    :param pdf: Patient data frame.
    :param sdf: Specimen data frame.
    :param cdf: Condition data frame.
    :return:
        Graph of computational conformance.
    """
    count_invalid_collection_collectedDateTime = 0
    for index in sdf.index:
        collection_collectedDateTime = sdf["collection_collectedDateTime"][index]
        subject_reference = sdf['subject_reference'][index]
        birthDay = get_birthDay(pdf, subject_reference)
        if birthDay is not None:
            if birthDay > collection_collectedDateTime:
                count_invalid_collection_collectedDateTime += 1

    onsetDateTime_count = 0
    recordedDate_count = 0
    for index in cdf.index:
        onsetDateTime = cdf["onsetDateTime"][index]
        recordedDate = cdf["recordedDate"][index]

        if index < len(sdf.index):
            subject_reference = sdf['subject_reference'][index]
            birthDay = get_birthDay(pdf, subject_reference)
        if birthDay is not None:
            if birthDay > onsetDateTime:
                onsetDateTime_count += 1
            if birthDay > recordedDate:
                recordedDate_count += 1

    result = {
        "Records": ["Number of records in specimens",
                    "Invalid collection_collectedDateTime",
                    "Number of records in conditions",
                    "Invalid onsetDateTime", "Invalid recordedDate"],
        "Count": [sdf.shape[0], count_invalid_collection_collectedDateTime,
                  cdf.shape[0], onsetDateTime_count, recordedDate_count]
    }
    dff = pd.DataFrame(result)
    fig = px.scatter(dff, x='Records', y='Count')
    return fig


# original checks
# warnings
# 1
def last_update_before_initial_diagnosis(cdf, odf):
    """
    Warning # 1
    Original warning type: "Vital check date precedes initial diagnosis date"

    Args:
        cdf: Condition data frame.
        odf: Time Observation data frame.

    Returns:
        Graph of result.

    """
    cdf_copy = cdf.copy()
    odf_copy = odf.copy()
    result = pd.merge(cdf_copy, odf_copy, how="inner", on=["subject"])
    result["fromDiagToVitalCheckWeeks"] = result["last_update"] < result["recorded_date"]

    all = result.shape[0]
    failures = result.fromDiagToVitalCheckWeeks.sum()

    # filter all failures
    failed_rows = result.loc[result.fromDiagToVitalCheckWeeks]
    failed_rows.to_csv('reports/fhir/extra/last_update_before_initial_diagnosis.csv', index=False)

    result = {
        "Records": ["Number of records", "last_update_before_initial_diagnosis"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 2
def vital_check_date_is_equal_to_initial_diagnosis_date(cdf, odf):
    """
    Warning # 2
    Original warning type: "Vital check date is equal to initial diagnosis date"

    Args:
        cdf: Condition data frame.
        odf: Time Observation data frame.

    Returns:
        Graph of result.
    """
    cdf_copy = cdf.copy()
    odf_copy = odf.copy()
    result = pd.merge(cdf_copy, odf_copy, how="inner", on=["subject"])
    result["fromDiagToVitalCheckWeeks"] = result["last_update"] == result["recorded_date"]

    all = result.shape[0]
    failures = result.fromDiagToVitalCheckWeeks.sum()

    # filter all failures
    failed_rows = result.loc[result.fromDiagToVitalCheckWeeks]
    failed_rows.to_csv('reports/fhir/extra/vital_check_date_is_equal_to_initial_diagnosis_date.csv', index=False)

    result = {
        "Records": ["Number of records", "vital_check_date_is_equal_to_initial_diagnosis_date"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig

def calculate_days(row):
    # if pd.isna(row['last_update']) or pd.isna(row['recorded_date']):
    #     return None
    return (row["last_update"] - row["recorded_date"]).days


# 3
def suspicious_survival_information(cdf, odf):
    """
    Warning # 3
    Original warning type: "Suspicious survival information"

    Args:
        cdf: Condition data frame.
        odf: Time Observation data frame.

    Returns:
        Graph of result.

    """
    cdf_copy = cdf.copy()
    odf_copy = odf.copy()
    result = pd.merge(cdf_copy, odf_copy, how="inner", on=["subject"])
    result["fromDiagToVitalCheckWeeks"] = result["last_update"] > result["recorded_date"]

    result['last_update'] = pd.to_datetime(result['last_update'])
    result['recorded_date'] = pd.to_datetime(result['recorded_date'])
    result["delta"] = (result['last_update'] - result["recorded_date"]).dt.days

    result["survivalToVitalRatio"] = (result["overall_survival"] /
                                      ( result["delta"] / 7))
    result["survival_check"] = result["survivalToVitalRatio"] > 3
    result["result"] = (result["survival_check"] & result["fromDiagToVitalCheckWeeks"])

    all = result.shape[0]
    failures = result.result.sum()

    # filter all failures
    failed_rows = result.loc[result.result]
    failed_rows.to_csv('reports/fhir/extra/suspicious_survival_information.csv', index=False)

    result = {
        "Records": ["Number of records", "suspicious_survival_information"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig

# 4
def age_at_primary_diagnosis(pdf, cdf):
    """
    Warning # 4
    Original warning type: "Suspiciously young patient"

    :param pdf: Patient data frame.
    :param cdf: Condition data frame.
    :return:
        Graph of result.
    """
    cdf_copy = cdf.copy()
    cdf_copy["subject"] = cdf_copy["subject"].apply(lambda x: x.split("/")[1])
    pdf_copy = pdf.copy()
    merged_df = pd.merge(pdf_copy, cdf_copy, how="left", on="subject")
    count_of_rows = merged_df.shape[0]
    merged_df["age_at_diagnosis"] = merged_df["onset_date_time"] - merged_df["birthDate"]
    incorrect_df = merged_df.loc[merged_df['age_at_diagnosis'] < pd.Timedelta(days=15*365.25)]
    incorrect_count = incorrect_df.shape[0]

    incorrect_df.to_csv('reports/fhir/extra/too_young_patients.csv', index=False)
    result = {
        "Records": ["Number of records", "too_young_patient"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 5
def suspiciously_long_survival(pdf, odf, cdf):
    """
    Warning # 5
    Original warning type: "Suspiciously long survival"

    Args:
        pdf: Patient data frame.
        cdf: Condition data frame.
        odf: Time Observation data frame.

    Returns:
        Graph of result.

    """
    pdf_copy = pdf.copy()
    odf_copy = odf.copy()
    odf_copy["subject"] = odf_copy["subject"].apply(lambda x: x.split("/")[1])
    cdf_copy = cdf.copy()
    cdf_copy["subject"] = cdf_copy["subject"].apply(lambda x: x.split("/")[1])
    result = pd.merge(pdf_copy, odf_copy, how="inner", on=["subject"])
    result = pd.merge(result, cdf_copy, how="inner", on=["subject"])
    all = result.shape[0]

    result["age_at_diagnosis"] = result["recorded_date"] - result["birthDate"]
    result["age_at_diagnosis"] = result['age_at_diagnosis'].apply(lambda x: x.total_seconds() / 86400 / 365)
    result["check"] = ((result["overall_survival"] > 4000) | ((result['age_at_diagnosis'] + result["overall_survival"]/52 >= 100) & (result["age_at_diagnosis"] < 95)))


    failures = result["check"].sum()

    # filter all failures
    failed_rows = result.loc[result.check]
    failed_rows.to_csv('reports/fhir/extra/suspiciously_long_survival.csv', index=False)

    result = {
        "Records": ["Number of records", "suspiciously_long_survival"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 6
def vital_status_timestamp_missing(pdf, odf):
    """
    Warning # 6
    Original warning type: "Vital status timestamp missing"

    Args:
        pdf: Patient data frame.
        odf: Time Observation data frame.

    Returns:
        Graph of result.

    """
    pdf_copy = pdf.copy()
    odf_copy = odf.copy()
    odf_copy["subject"] = odf_copy["subject"].apply(lambda x: x.split("/")[1])
    result = pd.merge(pdf_copy, odf_copy, how="inner", on=["subject"])
    all = result.shape[0]
    result = result[result['deceasedBoolean'].notnull()]
    result = result[result['last_update'].isnull()]

    failures = result.shape[0]

    # filter all failures
    failed_rows = result
    failed_rows.to_csv('reports/fhir/extra/vital_status_timestamp_missing.csv', index=False)

    result = {
        "Records": ["Number of records", "vital_status_timestamp_missing"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 7
def vital_status_timestamp_is_in_the_future(odf):
    """
    Warning # 7
    Original warning type: "Vital status timestamp is in the future"

    Args:
        odf: Time Observation data frame.

    Returns:
        Graph of result.

    """
    result = odf.copy()
    result = result[result['last_update'].notnull()]
    result["future"] = result["last_update"] > datetime.now()

    all = result.shape[0]
    failures = result.future.sum()

    # filter all failures
    failed_rows = result[result["future"] == True]
    failed_rows.to_csv('reports/fhir/extra/vital_status_timestamp_is_in_the_future.csv', index=False)

    result = {
        "Records": ["Number of records", "vital_status_timestamp_is_in_the_future"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 8
def diagnosis_in_future(cdf):
    """
    Warning # 8
    Original warning type: "Initial diagnosis date is in the future"

    :param cdf: Condition data frame.
    :return:
        Graph of result.
    """
    now = datetime.now()
    cdf_copy = cdf.copy()
    count_of_rows = cdf_copy.shape[0]
    cdf_copy = cdf_copy[cdf_copy['recorded_date'].notnull()]
    cdf_copy["diagnosis_in_future"] = cdf_copy["recorded_date"] > now
    incorrect_count = cdf_copy["diagnosis_in_future"].sum()

    filter_ddf = cdf_copy[cdf_copy['diagnosis_in_future'] == True]
    filter_ddf.to_csv('reports/fhir/extra/diagnosis_in_future.csv', index=False)
    result = {
        "Records": ["Number of records", "diagnosis_in_future"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


def match_surgery_location_and_histo_location(row):
    """
    Check if codes of surgery location and histology location match.

    Args:
        row: Row in data frame.

    Returns:
        Result of match.
    """
    surgery_loc = row["code_code"]
    histology_loc = row["body_site_code"]
    codes = {"C18.0": 32713005,
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
    if surgery_loc in codes.keys():
        return histology_loc == codes.get(surgery_loc)
    return False


# 13
def surgery_and_histological_location_do_not_match_only_one(cdf, sdf):
    """
    Warning # 13
    Original warning type: "Surgery and histological location do not match"

    Args:
        cdf: Condition data frame.
        sdf: Surgery data frame.

    Returns:
        Graph of result.

    """
    cdf_copy = cdf.copy()
    sdf_copy = sdf.copy()
    result = pd.merge(cdf_copy, sdf_copy, how="right", on=["subject"])
    all = result.shape[0]
    result = result[result['code_code'].notnull()]
    result['count'] = result['subject'].map(result['subject'].value_counts())
    result = result[result['count'] == 1]

    result_result = []
    for index, row in result.iterrows():
        result_result.append(match_surgery_location_and_histo_location(row))
    result["result"] = pd.Series(result_result)

    failures = result.result.sum()

    # filter all failures
    failed_rows = result[result["result"] == True]
    failed_rows.to_csv('reports/fhir/extra/surgery_and_histological_location_do_not_match_only_one.csv', index=False)

    result = {
        "Records": ["Number of records", "surgery_and_histological_location_do_not_match_only_one"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 14
def surgery_and_histological_location_do_not_match_multiple(cdf, sdf):
    """
    Warning # 14
    Original warning type: "Surgery and histological location do not match (but multiple surgeries per patient)"

    Args:
        cdf: Condition data frame.
        sdf: Surgery data frame.

    Returns:
        Graph of result.

    """
    cdf_copy = cdf.copy()
    sdf_copy = sdf.copy()
    result = pd.merge(cdf_copy, sdf_copy, how="right", on=["subject"])
    all = result.shape[0]
    result['count'] = result['subject'].map(result['subject'].value_counts())
    result = result[result['count'] > 1]

    result_result = []
    for index, row in result.iterrows():
        result_result.append(match_surgery_location_and_histo_location(row))
    result["result"] = pd.Series(result_result)

    failures = result.result.sum()

    # filter all failures
    failed_rows = result[result["result"] == True]
    failed_rows.to_csv('reports/fhir/extra/surgery_and_histological_location_do_not_match_multiple.csv', index=False)

    result = {
        "Records": ["Number of records", "surgery_and_histological_location_do_not_match_multiple"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# TODO co udělat s tou původní kontrolou s Other?
def get_valid_surgeries(row):
    """
    Maps body site on right surgery

    Args:
        row: Row in data frame.

    Returns:
        Check if surgery and body site are matching.
    """
    surgery_type = row["surgery_display"]
    surgery_loc = row["body_site_display"]
    # C18.0 + (missing C18.1) + C18.2
    if surgery_loc == "Cecum structure" or surgery_loc == "Ascending colon structure":
        if surgery_type == "Right hemicolectomy":
            return "Valid"
        elif surgery_type == "Pan-procto colectomy" or surgery_type == "Total colectomy":
            return "Suspicious"
        else:
            return "Invalid"
    # C18.3
    if surgery_loc == "Structure of right colic flexur":
        if surgery_type == "Right hemicolectomy":
            return "Valid"
        elif surgery_type == "Pan-procto colectomy" or surgery_type == "Total colectomy" or surgery_type == "Transverse colectomy":
            return "Suspicious"
        else:
            return "Invalid"
    # C18.4
    if surgery_loc == "Transverse colon structure":
        if surgery_type == "Right hemicolectomy":
            return "Valid"
        elif surgery_type == "Pan-procto colectomy" or surgery_type == "Left hemicolectomy with anastomosis" or surgery_type == "Right hemicolectomy":
            return "Suspicious"
        else:
            return "Invalid"
    # C18.5
    if surgery_loc == "Structure of left colic flexure":
        if surgery_type == "Left hemicolectomy with anastomosis":
            return "Valid"
        elif (surgery_type == "Abdominoperineal resection of rectum" or surgery_type == "Pan-procto colectomy"
              or surgery_type == "Total colectomy" or surgery_type == "Sigmoid colectomy"
              or surgery_type == "Transverse colectomy"):
            return "Suspicious"
        else:
            return "Invalid"
    # C18.6
    if surgery_loc == "Descending colon structure":
        if surgery_type == "Left hemicolectomy with anastomosis":
            return "Valid"
        elif (surgery_type == "Abdominoperineal resection of rectum" or surgery_type == "Pan-procto colectomy"
              or surgery_type == "Total colectomy" or surgery_type == "Sigmoid colectomy"):
            return "Suspicious"
        else:
            return "Invalid"
    # C18.7
    if surgery_loc == "Sigmoid colon structure":
        if surgery_type == "Sigmoid colectomy":
            return "Valid"
        elif (surgery_type == "Abdominoperineal resection of rectum" or surgery_type == "Pan-procto colectomy"
              or surgery_type == "Total colectomy" or surgery_type == "Low anteroir colon resection"):
            return "Suspicious"
        else:
            return "Invalid"
    # C18.8 + C18.9 are missing
    # C19 (C19.9 is missing)
    if surgery_loc == "Structure of rectosigmoid junction":
        if (surgery_type == "Anterior resection of rectum" or surgery_type == "Endo-rectal tumor resection"
            or surgery_type == "Low anteroir colon resection" or surgery_type == "Sigmoid colectomy"):
            return "Valid"
        elif (surgery_type == "Abdominoperineal resection of rectum" or surgery_type == "Pan-procto colectomy"
              or surgery_type == "Total colectomy" or surgery_type == "Left hemicolectomy with anastomosis"):
            return "Suspicious"
        else:
            return "Invalid"
    # C20 (C20.9 is missing)
    if surgery_loc == "Rectum structure":
        if (surgery_type == "Anterior resection of rectum" or surgery_type == "Endo-rectal tumor resection"
            or surgery_type == "Low anteroir colon resection" or surgery_type == "Abdominoperineal resection of rectum"):
            return "Valid"
        elif (surgery_type == "Left hemicolectomy with anastomosis" or surgery_type == "Pan-procto colectomy"
              or surgery_type == "Total colectomy"):
            return "Suspicious"
        else:
            return "Invalid"
    return "Invalid"


# 15
def mismatch_between_surgery_location_and_surgery_type(sdf):
    """
    Warning # 15
    Original warning type: "Mismatch between surgery location and surgery type"

    Args:
        sdf: Surgery data frame.

    Returns:
        Graph of result.

    """
    result = sdf.copy()
    all = result.shape[0]

    result_result = ["Invalid" for _ in range(all)]
    result["surgery_check"] = pd.Series(result_result).copy()
    result.reset_index(drop=True, inplace=True)
    for index, row in result.iterrows():
        # result.at[index, 'surgery_check'] = get_valid_surgeries(row)
        result.loc[index, "surgery_check"] = get_valid_surgeries(row)
        # TODO opravit potom ostatní iterrows()
        # result_result.append(get_valid_surgeries(row))
    #result["surgery_check"] = pd.Series(result_result)
    result = result[result['surgery_check'] != "Valid"]

    failures = result.shape[0]
    result.to_csv('reports/fhir/extra/mismatch_between_surgery_location_and_surgery_type.csv', index=False)

    result = {
        "Records": ["Number of records", "mismatch_between_surgery_location_and_surgery_type"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 16
# only targeted and radiation
def end_time_is_before_start_time(pdf):
    """
    Warning # 16
    Original warning type: "Negative event (treatment/response) duration: end time is before start time"

    Args:
        pdf: Procedure (Targeted or Radiation Therapy) data frame.

    Returns:
        Graph of result.

    """
    result = pdf.copy()
    all = result.shape[0]
    result = result[result['end'].notnull()]
    result["result"] = result["end"] < result["start"]

    failures = result.result.sum()

    # filter all failures
    failed_rows = result.loc[result.result]
    failed_rows.to_csv('reports/fhir/extra/end_time_is_before_start_time.csv', index=False)

    result = {
        "Records": ["Number of records", "end_time_is_before_start_time"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


def count_adjusted_overall_survival(time_df, procedure_df, condition_df):
    """
    Count adjusted overall survival.

    Args:
        time_df: Time Observation data frame.
        procedure_df: Procedure (Surgery, Targeted Therapy, Radiation Therapy) data frame.
        condition_df: Condition data frame.

    Returns:
        Dataframe with adjusted overall survival.

    """
    time_df_copy = time_df.copy()
    procedure_df_copy = procedure_df.copy()
    condition_df_copy = condition_df.copy()
    result = pd.merge(time_df_copy, condition_df_copy, how="inner", on=["subject"])
    result = pd.merge(result, procedure_df_copy, how="right", on=["subject"])

    result = result.sort_values(by=['subject', 'start'], ascending=[True, True])
    result = result.groupby('subject').first().reset_index()

    result['start'] = pd.to_datetime(result['start'])
    result['recorded_date'] = pd.to_datetime(result['recorded_date'])
    result["start_weeks"] = ((result['start'] - result["recorded_date"]).dt.days) / 7
    result["adjusted_overall_survival"] = result["overall_survival"] + result["start_weeks"]
    return result


# 17
# only for surgery, targeted therapy and radiation therapy
def event_starts_or_ends_after_survival_of_patient_procedure(patient_df, procedure_df, time_df, condition_df):
    """
    Warning # 17
    Original warning type: "Event (treatment/response) starts or ends after survival of patient"

    Args:
        patient_df: Patient data frame.
        procedure_df: Procedure (Targeted or Radiation Therapy) data frame.
        time_df: Time Observation data frame.
        condition_df: Condition data frame.

    Returns:
        Graph of result.

    """
    patient_df_copy = patient_df.copy()
    time_df_copy = time_df.copy()
    procedure_df_copy = procedure_df.copy()
    all = procedure_df_copy.shape[0]
    result = count_adjusted_overall_survival(time_df_copy, procedure_df_copy, condition_df)
    result['end'] = pd.to_datetime(result['end'])
    result['recorded_date'] = pd.to_datetime(result['recorded_date'])
    result["end_weeks"] = ((result['end'] - result["recorded_date"]).dt.days) / 7
    result = pd.merge(patient_df_copy, result, how="right", on=["subject"])

    result["check"] = ((result["start_weeks"] > result["adjusted_overall_survival"])
                       | (result["end_weeks"] > (result["adjusted_overall_survival"] + 1)))

    failures = result.check.sum()

    # filter all failures
    failed_rows = result[result["check"] == True]
    failed_rows.to_csv('reports/fhir/extra/event_starts_or_ends_after_survival_of_patient_procedure.csv', index=False)

    result = {
        "Records": ["Number of records", "event_starts_or_ends_after_survival_of_patient_procedure"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 17
# for response and surgery
def event_starts_or_ends_after_survival_of_patient(patient_df, df, time_df, condition_df):
    """
    Warning # 17
    Original warning type: "Event (treatment/response) starts or ends after survival of patient"

    Args:
        patient_df: Patient data frame.
        df: Response or Surgery data frame.
        time_df: Time Observation data frame.
        condition_df: Condition data frame.

    Returns:
        Graph of result.

    """
    patient_df_copy = patient_df.copy()
    time_df_copy = time_df.copy()
    df_copy = df.copy()
    df_copy.rename(columns={'date': 'start'}, inplace=True)
    all = df_copy.shape[0]
    result = count_adjusted_overall_survival(time_df_copy, df_copy, condition_df)
    result = pd.merge(patient_df_copy, result, how="right", on=["subject"])

    result["check"] = result["start_weeks"] > result["adjusted_overall_survival"]

    failures = result.check.sum()

    # filter all failures
    failed_rows = result[result["check"] == True]
    failed_rows.to_csv('reports/fhir/extra/event_starts_or_ends_after_survival_of_patient.csv', index=False)

    result = {
        "Records": ["Number of records", "event_starts_or_ends_after_survival_of_patient"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 18
# changed, must be compared with date of diagnosis
def start_of_response_to_therapy_is_before_diagnosis(odf, cdf):
    """
    Warning # 18
    Original warning type: "Start of response to therapy is before diagnosis"

    Args:
        odf: Response data frame.
        cdf: Condition data frame.

    Returns:
        Graph of result.

    """
    odf_copy = odf.copy()
    cdf_copy = cdf.copy()
    result = pd.merge(cdf_copy, odf_copy, how="right", on=["subject"])
    all = result.shape[0]

    result = result[result['date'].notnull()]
    result["result"] = result["date"] < result["onset_date_time"]

    failures = result.result.sum()

    # filter all failures
    failed_rows = result.loc[result.result]
    failed_rows.to_csv('reports/fhir/extra/start_of_response_to_therapy_is_before_diagnosis.csv', index=False)

    result = {
        "Records": ["Number of records", "start_of_response_to_therapy_is_before_diagnosis"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 19
def patient_died_but_last_response_is_complete(pdf, odf):
    """
    Warning # 19
    Original warning type: "Suspect incomplete followup: patient died of colon cancer while last response to therapy is Complete response"

    Args:
        pdf: Patient data frame.
        odf: Response data frame.

    Returns:
        Graph of result.

    """
    odf_copy = odf.copy()
    pdf_copy = pdf.copy()
    odf_copy["subject"] = odf_copy["subject"].apply(lambda x: x.split("/")[1])
    result = pd.merge(pdf_copy, odf_copy, how="right", on=["subject"])
    all = result.shape[0]

    result['date'] = pd.to_datetime(result['date'])
    result = result.sort_values(by=['subject', 'date'], ascending=[True, False])
    result = result.groupby('subject').first().reset_index()

    result = result[((result['code'] == "371001000") & (result["deceasedBoolean"] == 1.0))]

    failures = result.shape[0]

    # filter all failures
    failed_rows = result
    failed_rows.to_csv('reports/fhir/extra/patient_died_but_last_response_is_complete.csv', index=False)

    result = {
        "Records": ["Number of records", "patient_died_but_last_response_is_complete"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig

# 20
# changed, diag_date was not needed
def start_of_response_to_therapy_is_in_the_future(odf):
    """
    Warning # 20
    Original warning type: "Start of response to therapy is in the future"

    Args:
        odf: Response data frame.

    Returns:
        Graph of result.

    """
    result = odf.copy()
    all = result.shape[0]

    result = result[result["date"].notnull()]
    result["result"] = result["date"] > datetime.now()

    failures = result.result.sum()

    # filter all failures
    failed_rows = result.loc[result.result]
    failed_rows.to_csv('reports/fhir/extra/start_of_response_to_therapy_is_in_the_future.csv', index=False)

    result = {
        "Records": ["Number of records", "start_of_response_to_therapy_is_in_the_future"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig

# 21
# check only radiation, targeted, surgery
# pharma in OMOP
def start_of_therapy_is_before_diagnosis(pdf, cdf):
    """
    Warning # 21
    Original warning type: "Start of therapy is before diagnosis"

    Args:
        pdf: Procedure (Surgrery, Radiation Therapy, Targeted Therapy) data frame.
        cdf: Condition data frame.

    Returns:
        Graph of result.

    """
    pdf_copy = pdf.copy()
    cdf_copy = cdf.copy()
    result = pd.merge(cdf_copy, pdf_copy, how="right", on=["subject"])
    all = result.shape[0]

    result = result[result['start'].notnull()]
    result["result"] = result["start"] < result["onset_date_time"]

    failures = result.result.sum()

    # filter all failures
    failed_rows = result.loc[result.result]
    failed_rows.to_csv('reports/fhir/extra/start_of_therapy_is_before_diagnosis.csv', index=False)

    result = {
        "Records": ["Number of records", "start_of_therapy_is_before_diagnosis"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 22
# only radiation, surgery and targeted therapy
def start_of_treatment_is_in_the_future(pdf, cdf):
    """
    Warning # 22
    Original warning type: "Start of treatment is in the future"

    Args:
        pdf: Procedure (Surgery, Radiation Therapy, Targeted Therapy) data frame.
        cdf: Condition data frame.

    Returns:
        Graph of result.

    """
    pdf_copy = pdf.copy()
    cdf_copy = cdf.copy()
    result = pd.merge(cdf_copy, pdf_copy, how="right", on=["subject"])
    all = result.shape[0]

    result = result[result['start'].notnull()]
    result["result"] = result["start"] > datetime.now()

    failures = result.result.sum()

    # filter all failures
    failed_rows = result.loc[result.result]
    failed_rows.to_csv('reports/fhir/extra/start_of_treatment_is_in_the_future.csv', index=False)

    result = {
        "Records": ["Number of records", "start_of_treatment_is_in_the_future"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 23
# only radiation and targeted
def end_of_treatment_is_in_the_future(pdf):
    """
    Warning # 23
    Original warning type: "End of treatment is in the future"

    Args:
        pdf: Procedure (Surgery, Radiation Therapy, Targeted Therapy) data frame.

    Returns:
        Graph of result.

    """
    result = pdf.copy()
    all = result.shape[0]

    result = result[result['end'].notnull()]
    result["result"] = result["end"] > datetime.now()

    failures = result.result.sum()

    # filter all failures
    failed_rows = result.loc[result.result]
    failed_rows.to_csv('reports/fhir/extra/end_of_treatment_is_in_the_future.csv', index=False)

    result = {
        "Records": ["Number of records", "end_of_treatment_is_in_the_future"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 24
# only for radiation and targeted therapy
def non_surgery_therapy_starts_and_ends_in_week_0_since_initial_diagnosis(pdf, cdf):
    """
    Warning # 24
    Original warning type: "Non-surgery therapy starts and ends in week 0 since initial diagnosis (maybe false positive)"

    Args:
        pdf: Procedure (Radiation Therapy, Targeted Therapy) data frame.
        cdf: Condition data frame.

    Returns:
        Graph of result.

    """
    result = pd.merge(cdf, pdf, how="right", on="subject")
    count_of_rows = result.shape[0]
    result = result.dropna()

    result["sus_early_therapy"] = ((result["start"]
                                              - result["recorded_date"] == pd.Timedelta(days=0))
                                      & (result["end"]
                                              - result["recorded_date"] == pd.Timedelta(days=0)))
    incorrect_count = result["sus_early_therapy"].sum()

    filter_ddf = result[result['sus_early_therapy'] == True]
    filter_ddf.to_csv('reports/fhir/extra/sus_early_therapy.csv', index=False)

    result = {
        "Records": ["Number of records", "sus_early_therapy"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


def get_stage(row):
    """
    Calculate cancer stage from TNM information and UICC version.

    Args:
        row: Row from data frame.

    Returns:
        Calculated cancer stage.

    """
    method_coding_code = row["method_coding_code"]
    t_coding_code = row["t_coding_code"]
    n_coding_code = row["n_coding_code"]
    m_coding_code = row["m_coding_code"]

    if method_coding_code == "444256004":
        uicc_version = "6th"
    elif method_coding_code == "443830009":
        uicc_version = "7th"
    else:
        uicc_version = None

    if uicc_version == "6th":
        if m_coding_code == "M1":
            return "IV"
        elif m_coding_code == "MX":
            return None
        elif m_coding_code == "M0":
            if t_coding_code == "Tis" and n_coding_code == "N0":
                return None
            elif (t_coding_code == "T1" or t_coding_code == "T2") and n_coding_code == "N0":
                return "I"
            elif t_coding_code == "T3" and n_coding_code == "N0":
                return "IIA"
            elif t_coding_code == "T4" and n_coding_code == "N0":
                return "IIB"
            elif (t_coding_code == "T1" or t_coding_code == "T2") and n_coding_code == "N1":
                return "IIIA"
            elif (t_coding_code == "T3" or t_coding_code == "T4") and n_coding_code == "N1":
                return "IIIB"
            elif n_coding_code == "N2":
                return "IIIC"
            else:
                return "Unknown combination of pTN values in TNM 6th ed: pT = " + t_coding_code + ", pN = " + n_coding_code
        else:
            return "Unknown M value for TNM 6th ed: pM = " + m_coding_code
    elif uicc_version == "7th":
        if m_coding_code == "M1":
            return "IV"
        elif m_coding_code == "M1a":
            return "IVA"
        elif m_coding_code == "M1b":
            return "IVB"
        elif m_coding_code == "M0":
            if t_coding_code == "Tis" and n_coding_code == "N0":
                return "0"
            elif (t_coding_code == "T1" or t_coding_code == "T2") and n_coding_code == "N0":
                return "I"
            elif t_coding_code == "T3" and n_coding_code == "N0":
                return "IIA"
            elif t_coding_code == "T4a" and n_coding_code == "N0":
                return "IIB"
            elif t_coding_code == "T4b" and n_coding_code == "N0":
                return "IIC"
            elif t_coding_code == "T4" and n_coding_code == "N0":
                return "II"
            elif (t_coding_code == "T1" or t_coding_code == "T2") and (n_coding_code == "N1"
            or n_coding_code == "N1a" or n_coding_code == "N1b" or n_coding_code == "N1c"):
                return "IIIA"
            elif t_coding_code == "T1" and n_coding_code == "N2a":
                return "IIIA"
            elif (t_coding_code == "T3" or t_coding_code == "T4a") and (n_coding_code == "N1"
            or n_coding_code == "N1a" or n_coding_code == "N1b" or n_coding_code == "N1c"):
                return "IIIB"
            elif (t_coding_code == "T2" or t_coding_code == "T3") and n_coding_code == "N2a":
                return "IIIB"
            elif (t_coding_code == "T2" or t_coding_code == "T1") and n_coding_code == "N2b":
                return "IIIB"
            elif t_coding_code == "T4a" and n_coding_code == "N2a":
                return "IIIC"
            elif (t_coding_code == "T3" or t_coding_code == "T4a") and n_coding_code == "N2b":
                return "IIIC"
            elif t_coding_code == "T4b" and (n_coding_code == "N1" or n_coding_code == "N1a"
                                            or n_coding_code == "N1b" or n_coding_code == "N1c"
                                            or n_coding_code == "N2" or n_coding_code == "N2a"
                                            or n_coding_code == "N2b"):
                return "IIIC"
            elif (n_coding_code == "N1" or n_coding_code == "N1a" or n_coding_code == "N1b"
                  or n_coding_code == "N1c" or n_coding_code == "N2" or n_coding_code == "N2a"
                  or n_coding_code == "N2b"):
                return "III"
            else:
                return "Unknown combination of pTN values in TNM 7th ed: pT = " + t_coding_code + ", pN = " + n_coding_code
        else:
            return "Unknown M value in TNM 7th ed: " + m_coding_code
    return None


# 26
def mismatch_between_provided_and_computed_stage_value(odf):
    """
    Warning # 26
    Original warning type: "Mismatch between provided and computed stage value"

    Args:
        odf: TNM Observation data frame.

    Returns:
        Graph of result.

    """
    result = odf.copy()
    all = result.shape[0]
    result = result[result['method_coding_code'].notnull()]
    result = result[result['t_coding_code'].notnull()]
    result = result[result['n_coding_code'].notnull()]
    result = result[result['m_coding_code'].notnull()]

    result_result = [None for _ in range(all)]
    result["uicc_stage_computed"] = pd.Series(result_result).copy()
    result.reset_index(drop=True, inplace=True)
    for index, row in result.iterrows():
        result.loc[index, "uicc_stage_computed"] = get_stage(row)

    result = result[result['uicc_stage_computed'].notnull()]

    result["uicc_stage_check"] = result["uicc_stage_computed"] == result["stage_code"]
    result = result[result['uicc_stage_check'] == False]

    failures = result.shape[0]

    # filter all failures
    failed_rows = result
    failed_rows.to_csv('reports/fhir/extra/mismatch_between_provided_and_computed_stage_value.csv', index=False)

    result = {
        "Records": ["Number of records", "mismatch_between_provided_and_computed_stage_value"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 27
def sus_tnm_combo_for_uicc_version_or_uncomputable_stage(odf):
    """
    Warning # 27
    Original warning type: "Suspicious TNM value combination for given UICC version (e.g., N2a for UICC version 6) or uncomputable UICC stage"

    Args:
        odf: TNM Observation data frame.

    Returns:
        Graph of result.

    """
    result = odf.copy()
    all = result.shape[0]
    result = result[result['method_coding_code'].notnull()]
    result = result[result['t_coding_code'].notnull()]
    result = result[result['n_coding_code'].notnull()]
    result = result[result['m_coding_code'].notnull()]
    result = result[result['m_coding_code'] != "MX"]
    result = result[result['n_coding_code'] != "NX"]
    result = result[((result['method_coding_code'] == "444256004") | (result["method_coding_code"] == "443830009"))]

    result_result = []
    for index, row in result.iterrows():
        result_result.append(get_stage(row))
    result["uicc_stage_computed"] = pd.Series(result_result)

    result = result[result['uicc_stage_computed'].isnull()]

    failures = result.shape[0]

    # filter all failures
    failed_rows = result
    failed_rows.to_csv('reports/fhir/extra/sus_tnm_combo_for_uicc_version_or_uncomputable_stage.csv', index=False)

    result = {
        "Records": ["Number of records", "sus_tnm_combo_for_uicc_version_or_uncomputable_stage"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 28
def pnx_and_missing_uicc_stage(odf):
    """
    Warning # 28
    Original warning type: "pNX provided in TNM values, while UICC stage is determined (how?)"

    Args:
        odf: TNM Observation data frame.

    Returns:
        Graph of result.

    """
    result = odf.copy()
    all = result.shape[0]
    result = result[result['method_coding_code'].notnull()]
    result = result[result['t_coding_code'].notnull()]
    result = result[result['n_coding_code'].notnull()]
    result = result[result['m_coding_code'].notnull()]

    result = result[((result['n_coding_code'] == "NX")
                                & (result["stage_code"] is not None)
                                & ~((result["stage_code"] == "IV")
                                | (result["stage_code"] == "IVA")
                                | (result["stage_code"] == "IVB")))]

    failures = result.shape[0]

    # filter all failures
    failed_rows = result
    failed_rows.to_csv('reports/fhir/extra/pnx_and_missing_uicc_stage.csv', index=False)

    result = {
        "Records": ["Number of records", "pnx_and_missing_uicc_stage"],
        "Count": [all, failures]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig