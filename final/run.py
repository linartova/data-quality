import argparse
import psycopg2
from load_data_fhir import read_xml_and_create_classes, create_files, create_ids_lists, provide_server_connection
from load_data_ohdsi import load_data
from quality_checks_fhir import (create_df, conformance_patient, conformance_specimen, conformance_condition,
                                 conformance_relational, conformance_computational, completeness, uniqueness)
from quality_checks_ohdsi import (create_df_omop, vital_status_timestamp_precedes_initial_diagnostic_date,
                                  vital_status_timestamp_equals_initial_diagnostic_date, too_young_check,
                                  pharma_start_end)
from create_export_file import create_pdf_ohdsi, create_pdf_fhir


def work_with_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file", help="Mandatory file with data")
    parser.add_argument("--save", "-s", action="store_false", help="Store or delete data")
    parser.add_argument("--fhir", "-f", action="store", help="Fhir server url")
    parser.add_argument("--ohdsi_host", "-host", action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_port", "-port", action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_user", "-user",action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_password", "-pa", action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_database", "-d",action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_schema", "-sch", action="store", help="OHDSI database credentials")
    parser.add_argument("--volume", "-v", action="store_false",
                        help="Expected big data - static visualization.")

    args = parser.parse_args()

    input_file_path = args.input_file

    save = args.save

    fhir = args.fhir

    ohdsi_host = args.ohdsi_host
    ohdsi_port = args.ohdsi_port
    ohdsi_user = args.ohdsi_user
    ohdsi_password = args.ohdsi_password
    ohdsi_database = args.ohdsi_database
    ohdsi_schema = args.ohdsi_schema

    volume = args.volume

    ohdsi = {
        "host": ohdsi_host,
        "port": ohdsi_port,
        "user": ohdsi_user,
        "password": ohdsi_password,
        "database": ohdsi_database,
        "schema": ohdsi_schema
    }

    correct_fhir = False
    if fhir is not None:
        correct_fhir = True

    correct_ohdsi = False
    if (ohdsi_host is not None and ohdsi_port is not None
            and ohdsi_user is not None and ohdsi_password is not None
            and ohdsi_database is not None and ohdsi_schema is not None):
        correct_ohdsi = True

    if not correct_ohdsi:
        print("OHDSI credentials are missing")

    if not correct_fhir:
        print("FHIR url is missing")

    if not correct_fhir and not correct_ohdsi:
        return None

    standard = "both"
    if not correct_fhir:
        standard = "ohdsi"
    if not correct_ohdsi:
        standard = "fhir"

    print(input_file_path, standard, save, fhir, ohdsi, volume)
    return input_file_path, standard, save, fhir, ohdsi, volume


# TODO
def fhir(url, file_name):
    # server
    smart_client = provide_server_connection(url)

    # data
    data = read_xml_and_create_classes(file_name)

    # create id files
    create_files(data, smart_client)

    # todo run checks and create svgs
    server = smart_client.server
    patients_id, specimens_id, conditions_id = create_ids_lists()
    patients_df, specimens_df, conditions_df = create_df(patients_id, specimens_id, conditions_id, server)
    conformance_computational(patients_df, specimens_df, conditions_df)

    # todo create report
    create_pdf_fhir()


# todo
def omop(ohdsi, input_file):
    schema = ohdsi.pop("schema")
    load_data(ohdsi, input_file, schema)

    # todo create dfs
    conn = psycopg2.connect(**ohdsi)
    ddf = create_df_omop(conn, "ohdsi_demo.drug_exposure", schema)
    # person_test_set = create_df_omop(con, "person")
    # observation_period_test_set = create_df_omop(con, "observation_period")
    # condition_occurrence_test_set = create_df_omop(con, "condition_occurrence")

    # todo run checks and create svgs
    pharma_start_end(ddf)

    # todo create report
    create_pdf_ohdsi()


if __name__ == '__main__':
    omop(None, None)
    # todo add mypy
    input_file_path, standard, save, fhir, ohdsi, volume = work_with_arguments()
    print(standard)
    if standard == "fhir":
        fhir(fhir, input_file_path)
    elif standard =="ohdsi":
        omop(ohdsi, input_file_path)
    elif standard == "both":
        fhir(fhir, input_file_path)
        omop(ohdsi, input_file_path)