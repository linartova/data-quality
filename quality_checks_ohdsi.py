from _datetime import datetime
import pandas as pd
import plotly.express as px


def create_df_omop(con, table_name, schema):
    table = schema + "." + table_name
    sql_query = pd.read_sql_query("SELECT * FROM " + table, con)
    if table_name == "person":
        return pd.DataFrame(sql_query, columns=["person_id", "gender_concept_id", "year_of_birth",
                                                "race_concept_id", "ethnicity_concept_id",
                                                "person_source_value", "gender_source_value"])
    if table_name == "observation_period":
        return pd.DataFrame(sql_query, columns=["observation_period_id", "person_id",
                                                "observation_period_start_date", "observation_period_end_date",
                                                "period_type_concept_id"])
    if table_name == "condition_occurrence":
        return pd.DataFrame(sql_query, columns=["condition_occurrence_id", "person_id",
                                                "condition_concept_id", "condition_start_date",
                                                "condition_type_concept_id", "condition_source_value"])
    if table_name == "specimen":
        return pd.DataFrame(sql_query, columns=["specimen_id", "person_id", "specimen_concept_id",
                                                "specimen_type_concept_id", "specimen_date",
                                                "specimen_source_id", "specimen_source_value"])
    if table_name == "drug_exposure":
        return pd.DataFrame(sql_query, columns=["drug_exposure_id", "person_id", "drug_concept_id",
                               "drug_exposure_start_date", "drug_exposure_end_date",
                               "drug_type_concept_id"])
    if table_name == "procedure_occurrence":
        return pd.DataFrame(sql_query, columns=["procedure_occurrence_id", "person_id",
                                                "procedure_type_concept_id", "procedure_concept_id, procedure_date",
                                                "procedure_source_value"])
    return None


# todo uniqueness of specific values

def conformance_person(df):
    pass
    # gender_concept_id

    # year_of_birth

    # race_concept_id

    # ethnicity_concept_id

    # gender_source_value


def conformance_observation_period(df):
    pass


def conformance_condition_occurrence(df):
    pass


def conformance_specimen(df):
    pass


def conformance_drug_exposure(df):
    pass


def conformance_procedure_occurrence(df):
    pass


def conformance_computational(df):
    pass


def conformance_relational(df):
    pass


def plausability_atemporal(df):
    pass


def plausability_temporal(df):
    pass


# todo original checks:

def vital_status_timestamp_precedes_initial_diagnostic_date(cdf, odf):
    # diag_date
    # condition_start_date
    # 51_3

    # vital_status_timestamp
    # observation_period_end_date
    # 6_3
    # (vital_status_timestamp - diag_date) / 7
    # indexy 8 a 13
    merged_df = pd.merge(cdf, odf, how="inner", on="person_id")
    merged_df["fromDiagToVitalCheckWeeks"] = (merged_df["observation_period_end_date"]
                                              - merged_df["condition_start_date"]) / pd.Timedelta(weeks=1)
    count_of_rows = merged_df.shape[0]
    invalid_from_diag_to_vital_check_weeks = merged_df.query("fromDiagToVitalCheckWeeks < 0")
    invalid_from_diag_to_vital_check_weeks_sum = invalid_from_diag_to_vital_check_weeks.shape[0]

    result = {
        "Records": ["Number of records", "invalid_from_diag_to_vital_check_weeks_sum"],
        "Count": [count_of_rows, count_of_rows - invalid_from_diag_to_vital_check_weeks_sum]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig
    # todo return table with ids


def vital_status_timestamp_equals_initial_diagnostic_date(cdf, odf):
    merged_df = pd.merge(cdf, odf, how="inner", on="person_id")
    merged_df["fromDiagToVitalCheckWeeks"] = (merged_df["observation_period_end_date"]
                                              - merged_df["condition_start_date"]) / pd.Timedelta(weeks=1)
    count_of_rows = merged_df.shape[0]
    invalid_from_diag_to_vital_check_weeks = merged_df.loc[merged_df['fromDiagToVitalCheckWeeks'] == 0]
    invalid_from_diag_to_vital_check_weeks_sum = invalid_from_diag_to_vital_check_weeks.shape[0]

    result = {
        "Records": ["Number of records", "invalid_from_diag_to_vital_check_weeks_sum"],
        "Count": [count_of_rows, count_of_rows - invalid_from_diag_to_vital_check_weeks_sum]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig
    # todo return table with ids


def too_young_check(pdf):
    count_of_rows = pdf.shape[0]

    current_year = datetime.now().year
    pdf["age"] = current_year - pdf["year_of_birth"]
    incorrect_df = pdf.loc[pdf['age'] < 15]
    incorrect_count = incorrect_df.shape[0]
    result = {
        "Records": ["Number of records", "too_young_patient"],
        "Count": [count_of_rows, count_of_rows - incorrect_count]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


def vital_status_timestamp_is_in_past(odf):
    # observation_period_end_date
    count_of_rows = odf.shape[0]
    current_time = datetime.now()

    odf["date_in_future"] = odf["observation_period_end_date"] > current_time
    incorrect_count = odf["date_in_future"].sum()

    result = {
        "Records": ["Number of records", "too_young_patient"],
        "Count": [count_of_rows, incorrect_count]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 8 todo
def initial_diagnosis_date_is_in_the_future():
    # !is.na(diag_date) & diag_date > Sys.Date()
    pass


def pharma_start_end(ddf):
    # drug_exposure_start_date
    # drug_exposure_end_date
    count_of_rows = ddf.shape[0]

    # ddf_drop_null_end = ddf.loc[ddf['drug_exposure_end_date'] is not None]
    # ddf_drop_null = ddf_drop_null_end.loc[ddf_drop_null_end["drug_exposure_start_date"] is not None]

    ddf["date_in_future"] = ddf["drug_exposure_end_date"] < ddf["drug_exposure_start_date"]
    incorrect_count = ddf["date_in_future"].sum()

    result = {
        "Records": ["Number of records", "too_young_patient"],
        "Count": [count_of_rows, incorrect_count]
    }

    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.write_image("fig1.svg")
    return fig


# 21
def start_of_therapy_is_before_diagnosis(ddf, prdf):
    # 10_2 pharma_start
    # drug_exposure_start_date
    # table drug_exposure

    # 8_3 surgery_start
    # procedure_date
    # table procedure_occurrence

    # 12_4 radiation_start
    # procedure_date
    # table procedure_occurrence

    # 35_3 targeted_start
    # procedure_date
    # table procedure_occurrence

    count_of_rows = ddf.shape[0]

    ddf_drop_null = ddf.loc[ddf['drug_exposure_start_date'] is not None]
    ddf_drop_null["therapy_before_diagnosis"] = ddf_drop_null.loc[ddf_drop_null['drug_exposure_start_date'] < 0]
    incorrect_count = ddf["therapy_before_diagnosis"].sum()

    result = {
        "Records": ["Number of records", "too_young_patient"],
        "Count": [count_of_rows, incorrect_count]
    }

    dff = pd.DataFrame(result)
    fig_dff = px.bar(dff, x='Records', y='Count')

    # prdf
    count_of_rows = prdf.shape[0]

    prdf_drop_null = prdf.loc[prdf['drug_exposure_start_date'] is not None]
    prdf_drop_null["therapy_before_diagnosis"] = prdf_drop_null.loc[prdf_drop_null['drug_exposure_start_date'] < 0]
    incorrect_count = prdf["therapy_before_diagnosis"].sum()

    result = {
        "Records": ["Number of records", "too_young_patient"],
        "Count": [count_of_rows, incorrect_count]
    }

    prdf = pd.DataFrame(result)
    fig_prdf = px.bar(prdf, x='Records', y='Count')
    return fig_dff, fig_prdf


# todo diagnosis checks
# 22
def start_of_treatment_is_in_the_future(cdf, ddf, prdf):
    # diag_date
    # condition_start_date
    # cdf

    # treatment_start
    # drug_exposure_start_date
    # table drug_exposure

    # treatment_start
    # procedure_date
    # table procedure_occurrence

    # !is.na(diag_date) & diag_date + treatment_start*7 > Sys.Date()
    current_date = datetime.now()


# 23, 24, 25 todo

