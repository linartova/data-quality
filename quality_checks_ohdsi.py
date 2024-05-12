from _datetime import datetime
import pandas as pd
import plotly.express as px
import psycopg2


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
                               "drug_exposure_start_date", "drug_exposure_start_datetime",
                               "drug_exposure_end_date", "drug_exposure_end_datetime",
                               "drug_type_concept_id", "drug_source_value"])
    if table_name == "procedure_occurrence":
        return pd.DataFrame(sql_query, columns=["procedure_occurrence_id", "person_id",
                                                "procedure_type_concept_id", "procedure_concept_id", "procedure_date",
                                                "procedure_source_value"])
    return None


def completeness(df):
    name = df.columns[0][:-3]
    missing_values = pd.isnull(df).sum()
    fig = px.bar(missing_values)
    fig.update_layout(xaxis_title='count of missing values', yaxis_title='attribute', title="Missing values",
                      showlegend=False)
    df.to_csv("reports/omop/completeness" + name + ".csv", index=False)
    return fig


def uniqueness(df):
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
    fig = px.pie(dff, values='Count', names='Duplicates', title='Duplicated values')
    return fig


# todo original checks:

# todo argumentace u nepoužitých checků
# todo dokumentace, kde bude původní warning a názvy starých a nových hodnot

# místo inner joinu použít left join
# potom spočítat df shape
# odstranit null hodnoty
# name convensions bych udělala do 5 slov, vystihnout myšlenku nového checku, možná inspirace starým
# promyslet ty grafy - už součást vizualizace
# ještě předtím dodělat věci z ccdc_report_generator.R
# otestovat na nových datech
# vizualizace

# todo zkontrolovat, že se dropuje null jen z toho nutného column
# todo zkrátit počítání null values
# todo u těch reports prostě zkontrolovat, jestli jsou vždycky v té tabulce kontrolovány všechny hodnoty
# todo u reports druhou iteraci kontroly
# todo forced values by constrains


# warnings
# 1
def observation_end_precedes_condition_start(cdf, odf):
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
    return fig


# 2
def observation_end_equals_condition_start(cdf, odf):
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
    return fig


# 4
def too_young_person(pdf, cdf):
    merged_df = pd.merge(pdf, cdf, how="left", on="person_id")
    count_of_rows = merged_df.shape[0]
    merged_df.dropna()

    merged_df['condition_start_date'] = merged_df["condition_start_date"].apply(lambda x: int(x.strftime('%Y%m%d'))//1000)
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
    return fig


# 7
def observation_end_in_the_future(odf):
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
    return fig


# 8
def condition_start_in_the_future(cdf):
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
    return fig


# 9
def missing_drug_exposure_info(ddf):
    ddf_copy = ddf.copy()
    count_of_rows = ddf_copy.shape[0]

    ddf_copy["missing_drug_exposure_info"] = ((ddf_copy["drug_concept_id"] == 0) & (ddf_copy["drug_source_value"].isnull()))
    incorrect_count = ddf_copy["missing_drug_exposure_info"].sum()

    filter_ddf_copy = ddf_copy[ddf_copy['missing_drug_exposure_info'] == True]
    filter_ddf_copy.to_csv('reports/omop/missing_drug_exposure_info.csv', index=False)

    result = {
        "Records": ["Number of records", "missing_drug_exposure_info"],
        "Count": [count_of_rows, incorrect_count]
    }
    dff = pd.DataFrame(result)
    fig = px.bar(dff, x='Records', y='Count')
    return fig


# 10 + 11
def sus_pharma(ddf):
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
    return fig


# 12
def sus_pharma_other(ddf):
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
    return fig


# todo 15
def getValidSurgeries():
    pass


# 16
def drug_end_before_start(ddf):
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
    return fig


# 21
def therapy_start_before_diagnosis(cdf, ddf, prdf):
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
    return fig_dff, fig_prdf


# 22
def treatment_start_in_the_future(ddf, prdf):
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
    return fig_dff, fig_prdf


# 23
def drug_exposure_end_in_the_future(ddf):
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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 24
def sus_early_pharma(cdf, ddf):
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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 25
def sus_short_pharma(cdf, ddf):
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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff

# todo reports

# 1 + 2
def missing_specimen_date(pdf, sdf):
    merged_ddf = pd.merge(pdf, sdf, how="left", on="person_id")
    count_of_rows = merged_ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 3
def patients_without_specimen_source_id(pdf, sdf):
    merged_ddf = pd.merge(pdf, sdf, how="left", on="person_id")
    count_of_rows = merged_ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff

# 4 cannot be done, preservation mode is missing

# 5
def patients_without_specimen_source_value_concept_id(pdf, sdf):
    merged_ddf = pd.merge(pdf, sdf, how="left", on="person_id")
    count_of_rows = merged_ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 6
def patients_without_condition_values(pdf, cdf):
    merged_ddf = pd.merge(pdf, cdf, how="left", on="person_id")
    count_of_rows = merged_ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 7
def patients_without_surgery_values(pdf, prdf):
    patients = pdf.shape[0]
    surgeries = prdf[~prdf['procedure_source_value'].isin(["liver imaging", "CT",
                                                           "colonoscopy", "lung imaging",
                                                           "MRI", "Targeted therapy",
                                                           "Radiation therapy"])]

    merged_ddf = pd.merge(pdf, surgeries, how="right", on="person_id")
    patients_with_surgery_count = merged_ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 8
def missing_patient_and_diagnostic_values(pdf, prdf):
    # check patient values

    # then check if something from Colonoscopy,
    # CT, Liver_imaging, Lung_imaging, MRI is missing for each patient
    # "liver imaging", "CT", "colonoscopy", "lung imaging", "MRI"

    # vyfiltrovat diagnozu z prf
    # left join pdf + prdf
    # u pacientů, kteří budou mít v procedure_source_value None chybí tato diagnóza
    # vyfiltrovat je a dát do csv a spočítat do grafu

    # udělá se jeden velký histogram

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
    liver_imaging_df = liver_imaging_df.dropna()
    patients_with_liver_imaging_count = liver_imaging_df.shape[0]
    patients_without_liver_imaging.to_csv('reports/omop/patients_without_liver_imaging.csv', index=False)

    # "lung imaging"
    lung_imaging = prdf[prdf['procedure_source_value'] == "lung_imaging"]
    lung_imaging_df = pd.merge(pdf, lung_imaging, how="left", on="person_id")
    patients_without_lung_imaging = lung_imaging_df[~lung_imaging_df['procedure_source_value'].isnull()]
    lung_imaging_df = lung_imaging_df.dropna()
    patients_with_lung_imaging_count = lung_imaging_df.shape[0]
    patients_without_lung_imaging.to_csv('reports/omop/patients_without_lung_imaging.csv', index=False)

    # "colonoscopy"
    colonoscopy = prdf[prdf['procedure_source_value'] == "colonoscopy"]
    colonoscopy_df = pd.merge(pdf, colonoscopy, how="left", on="person_id")
    patients_without_colonoscopy = colonoscopy_df[~colonoscopy_df['procedure_source_value'].isnull()]
    colonoscopy_df = colonoscopy_df.dropna()
    patients_with_colonoscopy_count = colonoscopy_df.shape[0]
    patients_without_colonoscopy.to_csv('reports/omop/patients_without_colonoscopy.csv', index=False)

    # "MRI"
    mri = prdf[prdf['procedure_source_value'] == "MRI"]
    mri_df = pd.merge(pdf, mri, how="left", on="person_id")
    patients_without_mri = mri_df[~mri_df['procedure_source_value'].isnull()]
    mri_df = mri_df.dropna()
    patients_with_mri_count = mri_df.shape[0]
    patients_without_mri.to_csv('reports/omop/patients_without_mri.csv', index=False)

    # "CT"
    ct = prdf[prdf['procedure_source_value'] == "CT"]
    ct_df = pd.merge(pdf, ct, how="left", on="person_id")
    patients_without_ct = ct_df[~ct_df['procedure_source_value'].isnull()]
    ct_df = ct_df.dropna()
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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 9
def missing_targeted_therapy_values(pdf, prdf):
    patients = pdf.shape[0]
    surgeries = prdf[prdf['procedure_source_value'].isin(["Targeted therapy"])]

    merged_ddf = pd.merge(pdf, surgeries, how="right", on="person_id")
    patients_with_targeted_therapy_count = merged_ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

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
                    "patients_with_surgery_count",
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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 10
def missing_pharmacotherapy_value(pdf, ddf):
    patients = pdf.shape[0]
    merged_ddf = pd.merge(pdf, ddf, how="left", on="person_id")

    # drug_concept_id
    missing_drug_concept_id = merged_ddf["drug_concept_id"].isnull().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_concept_id'].isnull() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_concept_id.csv', index=False)

    # drug_exposure_start_date
    missing_drug_exposure_start_date = merged_ddf["drug_exposure_start_date"].isnull().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_exposure_start_date'].isnull() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_exposure_start_date.csv', index=False)

    # drug_exposure_start_datetime
    missing_drug_exposure_start_datetime = merged_ddf["drug_exposure_start_datetime"].isnull().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_exposure_start_datetime'].isnull() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_exposure_start_datetime.csv', index=False)

    # drug_exposure_end_date
    missing_drug_exposure_end_date = merged_ddf["drug_exposure_end_date"].isnull().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_exposure_end_date'].isnull() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_exposure_end_date.csv', index=False)

    # drug_exposure_end_datetime
    missing_drug_exposure_end_datetime = merged_ddf["drug_exposure_end_datetime"].isnull().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_exposure_end_datetime'].isnull() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_exposure_end_datetime.csv', index=False)

    # drug_type_concept_id
    missing_drug_type_concept_id = merged_ddf["drug_type_concept_id"].isnull().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_type_concept_id'].isnull() == True]
    filter_ddf.to_csv('reports/omop/patients_without_drug_type_concept_id.csv', index=False)

    # drug_source_value
    missing_drug_source_value = merged_ddf["drug_source_value"].isnull().sum()
    filter_ddf = merged_ddf[merged_ddf['drug_source_value'].isnull() == True]
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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


# 11
def missing_radiation_therapy_values(pdf, prdf):
    patients = pdf.shape[0]
    surgeries = prdf[prdf['procedure_source_value'].isin(["Radiation therapy"])]

    merged_ddf = pd.merge(pdf, surgeries, how="right", on="person_id")
    patients_with_radiation_therapy_count = merged_ddf.shape[0]
    merged_ddf = merged_ddf.dropna()

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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff

# 12 cannot be done, we do not have Responce to therapy

# 13 done in completeness

# 14 PreservationMode is not converted

# 15 - 22 Takes all form and return tibble of missing values. Something similar done in completeness.

# 23 - 30; get X Record set, return tibble


# 35 histogram with count of records in tables
def counts_of_records(pdf, odf, cdf, sdf, ddf, prdf):
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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff

# 31 - 34 values have not been mapped

# 36, 37, 38, 39 is done in completeness

# 40, 42 cannot be done, conversion done have Responce and FFPE

# 41
def get_patients_without_surgery(pdf, prdf):
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
    fig_dff = px.bar(dff, x='Records', y='Count')
    return fig_dff


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