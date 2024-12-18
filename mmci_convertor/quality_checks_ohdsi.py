from _datetime import datetime
import pandas as pd
import plotly.express as px


def create_df_omop(con, table_name, schema):
    """
    Universal function for creation of data frames from OMOP CDM tables.

    :param con: Connection to database.
    :param table_name: Processed table.
    :param schema: Schema in database.
    :return:
        Data frame from OMOP CDM table.
    """
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
                               "drug_exposure_start_date", "drug_exposure_start_datetime",
                               "drug_exposure_end_date", "drug_exposure_end_datetime",
                               "drug_type_concept_id", "drug_source_value"])
    if table_name == "procedure_occurrence":
        return pd.DataFrame(sql_query, columns=["procedure_occurrence_id", "person_id",
                                                "procedure_type_concept_id", "procedure_concept_id", "procedure_date",
                                                "procedure_source_value"])
    return None


def completeness(df):
    """
    Data quality check for completeness.

    :param df: Input data frame
    :return:
        Graph of completeness.
    """
    name = df.columns[0][:-3]
    missing_values = pd.isnull(df).sum()
    fig = px.bar(missing_values)
    fig.update_layout(xaxis_title='count of missing values', yaxis_title='attribute', title="Missing values",
                      showlegend=False)
    df.to_csv("reports/omop/completeness" + name + ".csv", index=False)
    fig.update_layout(title="Completeness" + name)
    return fig


def uniqueness(df):
    """
    Data quality check for uniqueness.

    :param df: Input data frame
    :return:
        Graph of uniqueness.
    """
    df = df.copy()
    id_column = df.columns[0]
    if id_column != "person_id":
        df.drop(columns=['person_id'], inplace=True)
    df.drop(columns=[id_column], inplace=True)

    count_of_rows = df.shape[0]
    count_of_duplicates = df.duplicated().sum()
    result = {
        "Duplicates": ["Unique rows", "Duplicated"],
        "Count": [count_of_rows - count_of_duplicates, count_of_duplicates]
    }

    name = id_column[:-3]
    df.to_csv("reports/omop/uniqueness" + name + ".csv", index=False)

    dff = pd.DataFrame(result)
    fig = px.pie(dff, values='Count', names='Duplicates', title='Duplicated values' + name)
    return fig


# original checks:
# warnings
# 1
def observation_end_precedes_condition_start(cdf, odf):
    """
    Warning # 1
    Original warning type: "Vital check date precedes initial diagnosis date"

    :param cdf: Condition Occurrence data frame.
    :param odf: Observation Period data frame.
    :return:
        Graph of result.
    """
    merged_df = pd.merge(cdf, odf, how="left", on="person_id")
    count_of_rows = merged_df.shape[0]
    merged_df = merged_df.dropna()

    merged_df["fromDiagToVitalCheckWeeks"] = (merged_df["observation_period_end_date"]
                                              - merged_df["condition_start_date"])
    invalid_sum = (merged_df['fromDiagToVitalCheckWeeks']
                                                  < pd.Timedelta(days=0)).sum()


    filter_df = merged_df[merged_df['fromDiagToVitalCheckWeeks'] < pd.Timedelta(days=0)]
    filter_df.to_csv('reports/omop/observation_end_precedes_condition_start.csv', index=False)

    result = {
        "Records": ["Number of records", "observation_end_precedes_condition_start"],
        "Count": [count_of_rows, invalid_sum]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 1: Vital check date precedes initial diagnosis date")
    return fig


# 2
def observation_end_equals_condition_start(cdf, odf):
    """
    Warning # 2
    Original warning type: "Vital check date is equal to initial diagnosis date"

    :param cdf: Condition Occurrence data frame.
    :param odf: Observation Period data frame.
    :return:
        Graph of result.
    """
    merged_df = pd.merge(cdf, odf, how="left", on="person_id")
    count_of_rows = merged_df.shape[0]
    merged_df = merged_df.dropna()

    merged_df["fromDiagToVitalCheckWeeks"] = (merged_df["observation_period_end_date"]
                                              - merged_df["condition_start_date"])
    invalid_sum = (merged_df['fromDiagToVitalCheckWeeks']
                                                  == pd.Timedelta(days=0)).sum()

    filter_df = merged_df[merged_df['fromDiagToVitalCheckWeeks'] == pd.Timedelta(days=0)]
    filter_df.to_csv('reports/omop/observation_end_equals_condition_start.csv', index=False)

    result = {
        "Records": ["Number of records", "observation_end_equals_condition_start"],
        "Count": [count_of_rows, invalid_sum]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 2: Vital check date is equal to initial diagnosis date")
    return fig


# 4
def too_young_person(pdf, cdf):
    """
    Warning # 4
    Original warning type: "Suspiciously young patient"

    :param pdf: Person data frame.
    :param cdf: Condition Occurrence data frame.
    :return:
        Graph of result.
    """
    merged_df = pd.merge(pdf, cdf, how="left", on="person_id")
    count_of_rows = merged_df.shape[0]
    merged_df.dropna()

    merged_df['condition_start_date'] = merged_df["condition_start_date"].apply(lambda x: int(x.strftime('%Y%m%d'))//10000)
    merged_df["age_at_diagnosis"] = merged_df["condition_start_date"] - merged_df["year_of_birth"]
    incorrect_df = merged_df.loc[merged_df['age_at_diagnosis'] < 15]
    incorrect_count = incorrect_df.shape[0]

    incorrect_df.to_csv('reports/omop/too_young_patients.csv', index=False)

    result = {
        "Records": ["Number of records", "too_young_patient"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 4: Suspiciously young patient")
    return fig


# 7
def observation_end_in_the_future(odf):
    """
    Warning # 7
    Original warning type: "Vital status timestamp is in the future"

    :param odf: Observation Period data frame.
    :return:
        Graph of result.
    """
    odf_copy = odf.copy()
    count_of_rows = odf_copy.shape[0]
    odf_copy.dropna()
    odf_copy["missing_timestamp"] = odf_copy['observation_period_end_date'].isnull()
    current_time = datetime.now().date()
    odf_copy["date_in_future"] = odf_copy["observation_period_end_date"] > current_time
    incorrect_count = odf_copy["date_in_future"].sum()

    filter_odf_copy = odf_copy[odf_copy['date_in_future'] == True]
    filter_odf_copy.to_csv('reports/omop/observation_end_in_the_future.csv', index=False)

    result = {
        "Records": ["Number of records", "observation_end_in_the_future"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 7: Vital status timestamp is in the future")
    return fig


# 8
def condition_start_in_the_future(cdf):
    """
    Warning # 8
    Original warning type: "Initial diagnosis date is in the future"

    :param cdf: Condition Occurrence data frame.
    :return:
        Graph of result.
    """
    cdf_copy = cdf.copy()
    count_of_rows = cdf_copy.shape[0]
    now = datetime.now().date()
    cdf_copy.dropna()
    cdf_copy["date_in_future"] = cdf_copy["condition_start_date"] > now
    incorrect_count = cdf_copy["date_in_future"].sum()

    filter_cdf_copy = cdf_copy[cdf_copy['date_in_future'] == True]
    filter_cdf_copy.to_csv('reports/omop/condition_start_in_the_future.csv', index=False)

    result = {
        "Records": ["Number of records", "condition_start_in_the_future"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 8: Initial diagnosis date is in the future")
    return fig


# 9
def missing_drug_exposure_info(ddf):
    """
    Warning # 9
    Original warning type: "Pharmacotherapy scheme description is missing while pharmacotherapy scheme is Other"

    :param ddf: Drug Exposure data frame.
    :return:
        Graph of result.
    """
    ddf_copy = ddf.copy()
    count_of_rows = ddf_copy.shape[0]

    ddf_copy["missing_drug_exposure_info"] = ((ddf_copy["drug_concept_id"] == 0) & (ddf_copy["drug_source_value"].isna()))
    incorrect_count = ddf_copy["missing_drug_exposure_info"].sum()

    filter_ddf_copy = ddf_copy[ddf_copy['missing_drug_exposure_info'] == True]
    filter_ddf_copy.to_csv('reports/omop/missing_drug_exposure_info.csv', index=False)

    result = {
        "Records": ["Number of records", "missing_drug_exposure_info"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 9: Pharmacotherapy scheme description is missing while pharmacotherapy scheme is Other")
    return fig


# 10 + 11
def sus_pharma(ddf):
    """
    Warning # 10 + 11
    Original warning type:
    "Suspicious description of pharmacotherapy"
    "Missing specification of used substances in pharmacotherapy description"

    :param ddf: Drug Exposure data frame.
    :return:
        Graph of result.
    """
    ddf_copy = ddf.copy()
    count_of_rows = ddf_copy.shape[0]
    ddf_copy["sus_pharma"] = (ddf_copy["drug_source_value"].isin(["No pharmacotherapy",
                                                                "other", "unknown", "NULL",
                                                                "neoadjuvante Radiochemo",
                                                                "Substances: unbekannt"]))
    incorrect_count = ddf_copy["sus_pharma"].sum()

    filter_ddf_copy = ddf_copy[ddf_copy['sus_pharma'] == True]
    filter_ddf_copy.to_csv('reports/omop/sus_pharma.csv', index=False)

    result = {
        "Records": ["Number of records", "sus_pharma"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 10 + 11")
    return fig


# 12
def sus_pharma_other(ddf):
    """
    Warning # 12
    Original warning type: "Suspicious characters or words in description of pharmacotherapy"

    :param ddf: Drug Exposure data frame.
    :return:
        Graph of result.
    """
    ddf_copy = ddf.copy()
    count_of_rows = ddf_copy.shape[0]
    ddf_copy["sus_pharma"] = (ddf_copy["drug_source_value"].isin(["%-FU", "andLeucovorin"]))
    incorrect_count = ddf_copy["sus_pharma"].sum()

    filter_ddf_copy = ddf_copy[ddf_copy['sus_pharma'] == True]
    filter_ddf_copy.to_csv('reports/omop/sus_pharma_other.csv', index=False)

    result = {
        "Records": ["Number of records", "sus_pharma"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 12: Suspicious characters or words in description of pharmacotherapy")
    return fig


# 16
def drug_end_before_start(ddf):
    """
    Warning # 16
    Original warning type: "Negative event (treatment/response) duration: end time is before start time"

    :param ddf: Drug Exposure data frame.
    :return:
        Graph of result.
    """
    ddf_copy = ddf.copy()
    count_of_rows = ddf_copy.shape[0]
    ddf_copy = ddf_copy.dropna()
    ddf_copy["date_in_future"] = (ddf_copy["drug_exposure_end_date"]
                                  < ddf_copy["drug_exposure_start_date"])
    incorrect_count = ddf_copy["date_in_future"].sum()

    filter_ddf_copy = ddf_copy[ddf_copy['date_in_future'] == True]
    filter_ddf_copy.to_csv('reports/omop/drug_end_before_start.csv', index=False)

    result = {
        "Records": ["Number of records", "drug_end_before_start"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 16: Negative event (treatment/response) duration: end time is before start time")
    return fig


# 21
def therapy_start_before_diagnosis(cdf, ddf, prdf):
    """
    Warning # 21
    Original warning type: "Start of therapy is before diagnosis"

    :param cdf: Condition Occurrence data frame.
    :param prdf: Procedure Occurrence data frame.
    :param ddf: Drug Exposure data frame.
    :return:
        Two graphs of result.
    """
    merged_ddf = pd.merge(cdf, ddf, how="left", on="person_id")
    count_of_rows = ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

    merged_ddf["therapy_before_diagnosis"] = (merged_ddf['drug_exposure_start_date']
                                             - merged_ddf["condition_start_date"]) < pd.Timedelta(days=0)
    incorrect_count = merged_ddf["therapy_before_diagnosis"].sum()

    filter_ddf = merged_ddf[merged_ddf['therapy_before_diagnosis'] == True]
    filter_ddf.to_csv('reports/omop/therapy_before_diagnosis_ddf.csv', index=False)

    result = {
        "Records": ["Number of records", "therapy_before_diagnosis"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig_dff = px.bar(dff, x='Records', y='Count')
    fig_dff.update_layout(title="Warning # 21: Start of therapy is before diagnosis - drug exposures")

    # prdf
    merged_prdf = pd.merge(cdf, prdf, how="left", on="person_id")
    count_of_rows = ddf.shape[0]
    merged_prdf = merged_prdf.dropna()

    merged_prdf["therapy_before_diagnosis"] = (merged_prdf['procedure_date']
                                              - merged_prdf["condition_start_date"]) < pd.Timedelta(days=0)
    incorrect_count = merged_prdf["therapy_before_diagnosis"].sum()

    filter_prdf = merged_prdf[merged_prdf['therapy_before_diagnosis'] == True]
    filter_prdf.to_csv('reports/omop/therapy_before_diagnosis_prdf.csv', index=False)

    result = {
        "Records": ["Number of records", "therapy_before_diagnosis"],
        "Count": [count_of_rows, incorrect_count]
    }
    prdf = pd.DataFrame(result)
    fig_prdf = px.bar(prdf, x='Records', y='Count')
    fig_prdf.update_layout(title="Warning # 21: Start of therapy is before diagnosis - procedure occurrence")
    return fig_dff, fig_prdf


# 22
def treatment_start_in_the_future(ddf, prdf):
    """
    Warning # 22
    Original warning type: "Start of treatment is in the future"

    :param prdf: Procedure Occurrence data frame.
    :param ddf: Drug Exposure data frame.
    :return:
        Two graphs of result.
    """
    current_date = datetime.now().date()
    ddf_copy = ddf.copy()
    count_of_rows = ddf_copy.shape[0]
    ddf_copy = ddf_copy.dropna()
    ddf_copy["treatment_start_in_the_future"] = ddf_copy["drug_exposure_start_date"] > current_date
    incorrect_count = ddf_copy["treatment_start_in_the_future"].sum()

    filter_ddf = ddf_copy[ddf_copy['treatment_start_in_the_future'] == True]
    filter_ddf.to_csv('reports/omop/treatment_start_in_the_future.csv', index=False)

    result = {
        "Records": ["Number of records", "treatment_start_in_the_future"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff_copy = pd.DataFrame(result)
    fig_dff = px.bar(dff_copy, x='Records', y='Count')
    fig_dff.update_layout(title="Warning # 22: Start of treatment is in the future - drug exposures")

    # prdf
    prdf_copy = prdf.copy()
    count_of_rows = prdf_copy.shape[0]
    prdf_copy = prdf_copy.dropna()
    prdf_copy["treatment_start_in_the_future"] = prdf_copy['procedure_date'] > current_date
    incorrect_count = prdf_copy["treatment_start_in_the_future"].sum()

    filter_prdf = prdf_copy[prdf_copy['treatment_start_in_the_future'] == True]
    filter_prdf.to_csv('reports/omop/start_of_treatment_is_in_the_future_prdf.csv', index=False)

    result = {
        "Records": ["Number of records", "treatment_start_in_the_future"],
        "Count": [count_of_rows, incorrect_count]
    }
    prdf_copy = pd.DataFrame(result)
    fig_prdf = px.bar(prdf_copy, x='Records', y='Count')
    fig_prdf.update_layout(title="Warning # 22: Start of treatment is in the future - procedure occurrence")
    return fig_dff, fig_prdf


# 23
def drug_exposure_end_in_the_future(ddf):
    """
    Warning # 23
    Original warning type: "End of treatment is in the future"

    :param ddf: Drug Exposure data frame.
    :return:
        Graphs of result.
    """
    current_date = datetime.now().date()
    ddf_copy = ddf.copy()
    count_of_rows = ddf_copy.shape[0]
    ddf_copy = ddf_copy.dropna()
    ddf_copy["drug_exposure_end_in_the_future"] = ddf_copy["drug_exposure_end_date"] > current_date
    incorrect_count = ddf_copy["drug_exposure_end_in_the_future"].sum()

    filter_ddf = ddf_copy[ddf_copy['drug_exposure_end_in_the_future'] == True]
    filter_ddf.to_csv('reports/omop/drug_exposure_end_in_the_future.csv', index=False)

    result = {
        "Records": ["Number of records", "drug_exposure_end_in_the_future"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 23: End of treatment is in the future")
    return fig


# 24
def sus_early_pharma(cdf, ddf):
    """
    Warning # 24
    Original warning type:
    "Non-surgery therapy starts and ends in week 0 since initial diagnosis (maybe false positive)"

    :param cdf: Condition Occurrence data frame.
    :param ddf: Drug Exposure data frame.
    :return:
        Graphs of result.
    """
    merged_ddf = pd.merge(cdf, ddf, how="left", on="person_id")
    count_of_rows = ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

    merged_ddf["sus_early_pharma"] = ((merged_ddf["condition_start_date"]
                                              - merged_ddf["drug_exposure_start_date"] == pd.Timedelta(days=0))
                                      & (merged_ddf["condition_start_date"]
                                              - merged_ddf["drug_exposure_end_date"] == pd.Timedelta(days=0)))
    incorrect_count = merged_ddf["sus_early_pharma"].sum()

    filter_ddf = merged_ddf[merged_ddf['sus_early_pharma'] == True]
    filter_ddf.to_csv('reports/omop/sus_early_pharma.csv', index=False)

    result = {
        "Records": ["Number of records", "sus_early_pharma"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 24: Non-surgery therapy starts and ends in week 0 since initial diagnosis (maybe false positive)")
    return fig


# 25
def sus_short_pharma(cdf, ddf):
    """
    Warning # 25
    Original warning type:
    "Suspiciously short pharma therapy - less than 1 week (maybe false positive)"

    :param cdf: Condition Occurrence data frame.
    :param ddf: Drug Exposure data frame.
    :return:
        Graphs of result.
    """
    merged_ddf = pd.merge(cdf, ddf, how="left", on="person_id")
    count_of_rows = ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

    merged_ddf["sus_short_pharma"] = ((merged_ddf["condition_start_date"] - merged_ddf["drug_exposure_start_date"] != pd.Timedelta(days=0))
                                      & (merged_ddf["drug_exposure_end_date"] - merged_ddf["drug_exposure_start_date"] == pd.Timedelta(days=0)))
    incorrect_count = merged_ddf["sus_short_pharma"].sum()

    filter_ddf = merged_ddf[merged_ddf['sus_short_pharma'] == True]
    filter_ddf.to_csv('reports/omop/sus_short_pharma.csv', index=False)

    result = {
        "Records": ["Number of records", "sus_short_pharma"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Warning # 25: Suspiciously short pharma therapy - less than 1 week (may be false positive)")
    return fig


# reports
# 1 + 2
def missing_specimen_date(pdf, sdf):
    """
    Report # 1 + 2

    :param pdf: Person data frame.
    :param sdf: Specimen data frame.
    :return:
        Graphs of result.
    """
    merged_ddf = pd.merge(pdf, sdf, how="left", on="person_id")
    count_of_rows = merged_ddf.shape[0]

    merged_ddf["missing_specimen_date"] = merged_ddf["specimen_date"].isnull()
    incorrect_count = merged_ddf["missing_specimen_date"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_specimen_date'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_specimen_date.csv', index=False)

    filter_ddf = merged_ddf[merged_ddf['missing_specimen_date'] == False]
    filter_ddf.to_csv('reports/omop/patients_with_specimen_date.csv', index=False)

    result = {
        "Records": ["Number of records",
                    "patients_without_specimen_date", "patients_with_specimen_date"],
        "Count": [count_of_rows, incorrect_count, count_of_rows - incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 1 + 2")
    return fig


# 3
def patients_without_specimen_source_id(pdf, sdf):
    """
    Report # 3

    :param pdf: Person data frame.
    :param sdf: Specimen data frame.
    :return:
        Graphs of result.
    """
    merged_ddf = pd.merge(pdf, sdf, how="left", on="person_id")
    count_of_rows = merged_ddf.shape[0]

    merged_ddf["missing_specimen_source_id"] = merged_ddf["specimen_source_id"].isnull()
    incorrect_count_source = merged_ddf["missing_specimen_source_id"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_specimen_source_id'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_specimen_source_id.csv', index=False)

    result = {
        "Records": ["Number of records",
                    "patients_without_specimen_source_id"],
        "Count": [count_of_rows, incorrect_count_source]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 3: createPlotWithoutSampleID")
    return fig


# 4 cannot be done, preservation mode is missing


# 5
def patients_without_specimen_source_value_concept_id(pdf, sdf):
    """
    Report # 5

    :param pdf: Person data frame.
    :param sdf: Specimen data frame.
    :return:
        Graphs of result.
    """
    merged_ddf = pd.merge(pdf, sdf, how="left", on="person_id")
    count_of_rows = merged_ddf.shape[0]

    merged_ddf["missing_specimen_source_value"] = merged_ddf["specimen_source_value"].isnull()
    incorrect_count = merged_ddf["missing_specimen_source_value"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_specimen_source_value'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_specimen_source_value.csv', index=False)

    merged_ddf["missing_specimen_concept_id"] = merged_ddf["specimen_concept_id"].isnull()
    incorrect_count_concept = merged_ddf["missing_specimen_concept_id"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_specimen_concept_id'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_specimen_concept_id.csv', index=False)

    result = {
        "Records": ["Number of records",
                    "patients_without_specimen_source_value", "patients_without_specimen_concept_id"],
        "Count": [count_of_rows, incorrect_count, incorrect_count_concept]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 5: createPlotWithoutMaterialType")
    return fig


# 6
def patients_without_condition_values(pdf, cdf):
    """
    Report # 6

    :param pdf: Person data frame.
    :param cdf: Condition Occurrence data frame.
    :return:
        Graphs of result.
    """
    merged_ddf = pd.merge(pdf, cdf, how="left", on="person_id")
    count_of_rows = merged_ddf.shape[0]

    # condition_source_value
    merged_ddf["missing_condition_source_value"] = merged_ddf["condition_source_value"].isnull()
    incorrect_count = merged_ddf["missing_condition_source_value"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_condition_source_value'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_condition_values.csv', index=False)

    # condition_start_date
    merged_ddf["missing_condition_start_date"] = merged_ddf["condition_start_date"].isnull()
    incorrect_count_date = merged_ddf["missing_condition_start_date"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_condition_start_date'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_condition_start_date.csv', index=False)

    # condition_concept_id
    merged_ddf["missing_condition_concept_id"] = merged_ddf["condition_concept_id"].isnull()
    incorrect_count_concept = merged_ddf["missing_condition_concept_id"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_condition_concept_id'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_condition_concept_id.csv', index=False)

    result = {
        "Records": ["Number of records", "patients_without_condition_values",
                    "patient_without_condition_start_date",
                    "patients_without_condition_concept_id"],
        "Count": [count_of_rows, incorrect_count,
                  incorrect_count_date, incorrect_count_concept]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 6: createPlotsWithoutHistoValues")
    return fig


# 7
def patients_without_surgery_values(pdf, prdf):
    """
    Report # 7

    :param pdf: Person data frame.
    :param prdf: Procedure Occurrence data frame.
    :return:
        Graphs of result.
    """
    patients = pdf.shape[0]
    surgeries = prdf[~prdf['procedure_source_value'].isin(["liver imaging", "CT",
                                                           "colonoscopy", "lung imaging",
                                                           "MRI", "Targeted therapy",
                                                           "Radiation therapy"])]

    merged_ddf = pd.merge(pdf, surgeries, how="right", on="person_id")
    patients_with_surgery_count = merged_ddf.shape[0]

    # procedure_source_value
    merged_ddf["missing_procedure_source_value"] = merged_ddf["procedure_source_value"].isnull()
    incorrect_count_procedure_source_value = merged_ddf["missing_procedure_source_value"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_source_value'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_source_value_surgery.csv', index=False)

    # procedure_concept_id
    merged_ddf["missing_procedure_concept_id"] = merged_ddf["procedure_concept_id"].isnull()
    incorrect_count_procedure_concept_id = merged_ddf["missing_procedure_concept_id"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_concept_id'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_concept_id_surgery.csv', index=False)

    # procedure_date
    merged_ddf["missing_procedure_date"] = merged_ddf["procedure_date"].isnull()
    incorrect_count_procedure_date = merged_ddf["missing_procedure_date"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_date'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_date_surgery.csv', index=False)

    result = {
        "Records": ["Number of patients", "patients_with_surgery_count",
                    "patients_without_procedure_source_value",
                    "patients_without_procedure_concept_id",
                    "patients_without_procedure_date"],
        "Count": [patients, patients_with_surgery_count,
                  incorrect_count_procedure_source_value,
                  incorrect_count_procedure_concept_id,
                  incorrect_count_procedure_date
                  ]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 7: createPlotsWithoutSurgeryValues")
    return fig


# 8
def missing_patient_and_diagnostic_values(pdf, prdf):
    """
    Report # 8

    :param pdf: Person data frame.
    :param prdf: Procedure Occurrence data frame.
    :return:
        Graphs of result.
    """
    patients = pdf.shape[0]

    # "gender_concept_id"
    missing_gender_concept_id = pdf["gender_concept_id"].isnull().sum()

    filter_pdf = pdf[pdf['gender_concept_id'].isnull()]
    filter_pdf.to_csv('reports/omop/missing_gender_concept_id.csv', index=False)

    # "year_of_birth"
    missing_year_of_birth = pdf["year_of_birth"].isnull().sum()
    filter_pdf = pdf[pdf['year_of_birth'].isnull()]
    filter_pdf.to_csv('reports/omop/missing_year_of_birth.csv', index=False)

    # "person_source_value"
    missing_person_source_value = pdf["person_source_value"].isnull().sum()
    filter_pdf = pdf[pdf['person_source_value'].isnull()]
    filter_pdf.to_csv('reports/omop/missing_person_source_value.csv', index=False)

    # "gender_source_value"
    missing_gender_source_value = pdf["gender_source_value"].isnull().sum()
    filter_pdf = pdf[pdf['gender_source_value'].isnull()]
    filter_pdf.to_csv('reports/omop/missing_gender_source_value.csv', index=False)

    # "liver imaging"
    liver_imaging = prdf[prdf['procedure_source_value'] == "liver imaging"]
    liver_imaging_df = pd.merge(pdf, liver_imaging, how="left", on="person_id")
    patients_without_liver_imaging = liver_imaging_df[~liver_imaging_df['procedure_source_value'].isnull()]
    patients_with_liver_imaging_count = liver_imaging_df.shape[0]
    patients_without_liver_imaging.to_csv('reports/omop/patients_without_liver_imaging.csv', index=False)

    # "lung imaging"
    lung_imaging = prdf[prdf['procedure_source_value'] == "lung_imaging"]
    lung_imaging_df = pd.merge(pdf, lung_imaging, how="left", on="person_id")
    patients_without_lung_imaging = lung_imaging_df[~lung_imaging_df['procedure_source_value'].isnull()]
    patients_with_lung_imaging_count = lung_imaging_df.shape[0]
    patients_without_lung_imaging.to_csv('reports/omop/patients_without_lung_imaging.csv', index=False)

    # "colonoscopy"
    colonoscopy = prdf[prdf['procedure_source_value'] == "colonoscopy"]
    colonoscopy_df = pd.merge(pdf, colonoscopy, how="left", on="person_id")
    patients_without_colonoscopy = colonoscopy_df[~colonoscopy_df['procedure_source_value'].isnull()]
    patients_with_colonoscopy_count = colonoscopy_df.shape[0]
    patients_without_colonoscopy.to_csv('reports/omop/patients_without_colonoscopy.csv', index=False)

    # "MRI"
    mri = prdf[prdf['procedure_source_value'] == "MRI"]
    mri_df = pd.merge(pdf, mri, how="left", on="person_id")
    patients_without_mri = mri_df[~mri_df['procedure_source_value'].isnull()]
    patients_with_mri_count = mri_df.shape[0]
    patients_without_mri.to_csv('reports/omop/patients_without_mri.csv', index=False)

    # "CT"
    ct = prdf[prdf['procedure_source_value'] == "CT"]
    ct_df = pd.merge(pdf, ct, how="left", on="person_id")
    patients_without_ct = ct_df[~ct_df['procedure_source_value'].isnull()]
    patients_with_ct_count = ct_df.shape[0]
    patients_without_ct.to_csv('reports/omop/patients_without_ct.csv', index=False)

    result = {
        "Records": ["Number of patients",
                    "missing_gender_concept_id",
                    "missing_year_of_birth",
                    "missing_person_source_value",
                    "missing_gender_source_value",
                    "patients_with_liver_imaging_count",
                    "patients_with_lung_imaging_count",
                    "patients_with_colonoscopy_count",
                    "patients_with_mri_count",
                    "patients_with_ct_count"],
        "Count": [patients,
                  missing_gender_concept_id,
                  missing_year_of_birth,
                  missing_person_source_value,
                  missing_gender_source_value,
                  patients_with_liver_imaging_count,
                  patients_with_lung_imaging_count,
                  patients_with_colonoscopy_count,
                  patients_with_mri_count,
                  patients_with_ct_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 8: createPlotsWithoutPatientValues")
    return fig


# 9
def missing_targeted_therapy_values(pdf, prdf):
    """
    Report # 9

    :param pdf: Person data frame.
    :param prdf: Procedure Occurrence data frame.
    :return:
        Graphs of result.
    """
    patients = pdf.shape[0]
    surgeries = prdf[prdf['procedure_source_value'] == "Targeted therapy"]

    merged_ddf = pd.merge(pdf, surgeries, how="right", on="person_id")
    patients_with_targeted_therapy_count = merged_ddf.shape[0]

    # procedure_source_value
    merged_ddf["missing_procedure_source_value"] = merged_ddf["procedure_source_value"].isnull()
    incorrect_count_procedure_source_value = merged_ddf["missing_procedure_source_value"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_source_value'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_source_value_targeted_therapy.csv', index=False)

    # procedure_concept_id
    merged_ddf["missing_procedure_concept_id"] = merged_ddf["procedure_concept_id"].isnull()
    incorrect_count_procedure_concept_id = merged_ddf["missing_procedure_concept_id"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_concept_id'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_concept_id_targeted_therapy.csv', index=False)

    # procedure_date
    merged_ddf["missing_procedure_date"] = merged_ddf["procedure_date"].isnull()
    incorrect_count_procedure_date = merged_ddf["missing_procedure_date"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_date'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_date_targeted_therapy', index=False)

    result = {
        "Records": ["Number of patients",
                    "patients_with_targeted_therapy_count",
                    "patients_without_procedure_source_value",
                    "patients_without_procedure_concept_id",
                    "patients_without_procedure_date"],
        "Count": [patients,
                  patients_with_targeted_therapy_count,
                  incorrect_count_procedure_source_value,
                  incorrect_count_procedure_concept_id,
                  incorrect_count_procedure_date
                  ]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 9: createPlotsWithoutTargetedTherapy")
    return fig


# 10
def missing_pharmacotherapy_value(pdf, ddf):
    """
    Report # 10

    :param pdf: Person data frame.
    :param ddf: Drug Exposure data frame.
    :return:
        Graphs of result.
    """
    patients = pdf.shape[0]
    merged_ddf = pd.merge(pdf, ddf, how="left", on="person_id")

    # drug_concept_id
    missing_drug_concept_id = merged_ddf["drug_concept_id"].isna().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_concept_id'].isna() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_concept_id.csv', index=False)

    # drug_exposure_start_date
    missing_drug_exposure_start_date = merged_ddf["drug_exposure_start_date"].isna().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_exposure_start_date'].isna() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_exposure_start_date.csv', index=False)

    # drug_exposure_start_datetime
    missing_drug_exposure_start_datetime = merged_ddf["drug_exposure_start_datetime"].isna().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_exposure_start_datetime'].isna() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_exposure_start_datetime.csv', index=False)

    # drug_exposure_end_date
    missing_drug_exposure_end_date = merged_ddf["drug_exposure_end_date"].isna().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_exposure_end_date'].isna() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_exposure_end_date.csv', index=False)

    # drug_exposure_end_datetime
    missing_drug_exposure_end_datetime = merged_ddf["drug_exposure_end_datetime"].isna().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_exposure_end_datetime'].isna() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_exposure_end_datetime.csv', index=False)

    # drug_type_concept_id
    missing_drug_type_concept_id = merged_ddf["drug_type_concept_id"].isna().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_type_concept_id'].isna() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_type_concept_id.csv', index=False)

    # drug_source_value
    missing_drug_source_value = merged_ddf["drug_source_value"].isna().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_source_value'].isna() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_source_value.csv', index=False)

    result = {
        "Records": ["Number of patients",
                    "missing_drug_concept_id",
                    "missing_drug_exposure_start_date",
                    "missing_drug_exposure_start_datetime",
                    "missing_drug_exposure_end_date",
                    "missing_drug_exposure_end_datetime",
                    "missing_drug_type_concept_id",
                    "missing_drug_source_value"
                    ],
        "Count": [patients,
                  missing_drug_concept_id,
                  missing_drug_exposure_start_date,
                  missing_drug_exposure_start_datetime,
                  missing_drug_exposure_end_date,
                  missing_drug_exposure_end_datetime,
                  missing_drug_type_concept_id,
                  missing_drug_source_value
                  ]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 10: createPlotsWithoutPharmacotherapy")
    return fig


# 11
def missing_radiation_therapy_values(pdf, prdf):
    """
    Report # 11

    :param pdf: Person data frame.
    :param prdf: Procedure Occurrence data frame.
    :return:
        Graphs of result.
    """
    patients = pdf.shape[0]
    surgeries = prdf[prdf['procedure_source_value'].isin(["Radiation therapy"])]

    merged_ddf = pd.merge(pdf, surgeries, how="right", on="person_id")
    patients_with_radiation_therapy_count = merged_ddf.shape[0]

    # procedure_source_value
    merged_ddf["missing_procedure_source_value"] = merged_ddf["procedure_source_value"].isnull()
    incorrect_count_procedure_source_value = merged_ddf["missing_procedure_source_value"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_source_value'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_source_value_radiation_therapy.csv', index=False)

    # procedure_concept_id
    merged_ddf["missing_procedure_concept_id"] = merged_ddf["procedure_concept_id"].isnull()
    incorrect_count_procedure_concept_id = merged_ddf["missing_procedure_concept_id"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_concept_id'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_concept_id_radiation_therapy.csv', index=False)

    # procedure_date
    merged_ddf["missing_procedure_date"] = merged_ddf["procedure_date"].isnull()
    incorrect_count_procedure_date = merged_ddf["missing_procedure_date"].sum()

    filter_ddf = merged_ddf[merged_ddf['missing_procedure_date'] == True]
    filter_ddf.to_csv('reports/omop/patients_without_procedure_date_radiation_therapy', index=False)

    result = {
        "Records": ["Number of patients",
                    "patients_with_surgery_count",
                    "patients_without_procedure_source_value",
                    "patients_without_procedure_concept_id",
                    "patients_without_procedure_date"],
        "Count": [patients,
                  patients_with_radiation_therapy_count,
                  incorrect_count_procedure_source_value,
                  incorrect_count_procedure_concept_id,
                  incorrect_count_procedure_date
                  ]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 11: createPlotsWithoutRadiationTherapy")
    return fig

# 12 cannot be done, we do not have Responce to therapy

# 13 done in completeness

# 14 PreservationMode is not converted

# 15 - 22 Takes all form and return tibble of missing values. Something similar done in completeness.

# 23 - 30; get X Record set, return tibble


# 35 histogram with count of records in tables
def counts_of_records(pdf, odf, cdf, sdf, ddf, prdf):
    """
    Report # 35

    :param pdf: Person data frame.
    :param odf: Observation Period data frame.
    :param cdf: Condition Occurrence data frame.
    :param sdf: Specimen data frame.
    :param ddf: Drug Exposure data frame.
    :param prdf: Procedure Occurrence data frame.
    :return:
        Graphs of result.
    """
    patients = pdf.shape[0]
    observations = odf.shape[0]
    conditions = cdf.shape[0]
    specimens = sdf.shape[0]
    drugs = ddf.shape[0]
    procedures = prdf.shape[0]
    result = {
        "Records": ["Patient records",
                    "Observation period records",
                    "Condition occurrence records",
                    "Specimen records",
                    "Drug exposure records",
                    "Procedure occurrence records",
                    ],
        "Count": [patients,
                  observations,
                  conditions,
                  specimens,
                  drugs,
                  procedures
                  ]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 35")
    return fig

# 31 - 34 values have not been mapped

# 36, 37, 38, 39 is done in completeness

# 40, 42 cannot be done, conversion done have Responce and FFPE


# 41
def get_patients_without_surgery(pdf, prdf):
    """
    Report # 41

    :param pdf: Person data frame.
    :param prdf: Procedure Occurrence data frame.
    :return:
        Graphs of result.
    """
    patients = pdf.shape[0]
    surgeries = prdf[~prdf['procedure_source_value'].isin(["liver imaging", "CT",
                                                           "colonoscopy", "lung imaging",
                                                           "MRI", "Targeted therapy",
                                                           "Radiation therapy"])]
    merged_df = pd.merge(pdf, surgeries, how="left", on="person_id")
    patients_without_surgery = merged_df["procedure_source_value"].isnull().sum()

    filter_df = merged_df[merged_df["procedure_source_value"].isnull()]
    filter_df.to_csv('reports/omop/get_patients_without_surgery.csv', index=False)
    result = {
        "Records": ["patients", "patients_without_surgery"],
        "Count": [patients, patients_without_surgery]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    fig.update_layout(title="Report # 41: getPatientsWithoutSurgery")
    return fig


# if __name__ == '__main__':
#     ohdsi = {}
#     con = psycopg2.connect(**ohdsi)
#     pdf = create_df_omop(con, "person", "ohdsi_demo").dropna(axis=1, how='all')
#     odf = create_df_omop(con, "observation_period", "ohdsi_demo").dropna(axis=1, how='all')
#     cdf = create_df_omop(con, "condition_occurrence", "ohdsi_demo").dropna(axis=1, how='all')
#     sdf = create_df_omop(con, "specimen", "ohdsi_demo").dropna(axis=1, how='all')
#     ddf = create_df_omop(con, "drug_exposure", "ohdsi_demo").dropna(axis=1, how='all')
#     prdf = create_df_omop(con, "procedure_occurrence", "ohdsi_demo").dropna(axis=1, how='all')

    # completeness(pdf)
    # completeness(odf)
    # completeness(cdf)
    # completeness(ddf)
    # completeness(sdf)
    # completeness(prdf)

    # tests warnings
    # observation_end_precedes_condition_start(cdf, odf)
    # observation_end_equals_condition_start(cdf, odf)
    # too_young_person(pdf, cdf)
    # observation_end_in_the_future(odf)
    # condition_start_in_the_future(cdf)
    # missing_drug_exposure_info(ddf)
    # sus_pharma(ddf)
    # sus_pharma_other(ddf)
    # drug_end_before_start(ddf)
    # fig_1, fig_2 = therapy_start_before_diagnosis(cdf, ddf, prdf)
    # fig_3, fig_4 = treatment_start_in_the_future(ddf, prdf)
    # drug_exposure_end_in_the_future(ddf)
    # sus_early_pharma(cdf, ddf)
    # sus_short_pharma(cdf, ddf)
    #
    # # test reports
    # missing_specimen_date(pdf, sdf)
    # patients_without_specimen_source_id(pdf, sdf)
    # patients_without_specimen_source_value_concept_id(pdf, sdf)
    # patients_without_condition_values(pdf, cdf)
    # patients_without_surgery_values(pdf, prdf)
    # missing_patient_and_diagnostic_values(pdf, prdf)
    # missing_targeted_therapy_values(pdf, ddf)
    # missing_pharmacotherapy_value(pdf, ddf)
    # missing_radiation_therapy_values(pdf, prdf)
    # counts_of_records(pdf, odf, cdf, sdf, ddf, prdf)
    # get_patients_without_surgery(pdf, prdf)