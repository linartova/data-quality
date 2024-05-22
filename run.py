import argparse
import psycopg2
from load_data_fhir import read_xml_and_create_resources, provide_server_connection
from load_data_ohdsi import load_data
from visualization_fhir import create_report_fhir
from visualization_ohdsi import create_report_ohdsi


def work_with_arguments():
    """
    This function parses user input.

    :return:
        input_file_path, standard, fhir, ohdsi

	    where
	        input_file_path (string) : The path of input file.
	        standard (string) : The chosen standard(s).
	        fhir (string) : The url of FHIR server.
	        ohdsi (Dict): {
    		    "host": The database host.
    		    "port": The database port.,
    		    "user": The database user.
                "password": The database password.
                "database": The database.
                "schema": The database schema.}
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file", help="Mandatory file with data")
    parser.add_argument("--fhir", "-f", action="store", help="Fhir server url")
    parser.add_argument("--ohdsi_host", "-host", action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_port", "-port", action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_user", "-user",action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_password", "-pa", action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_database", "-d",action="store", help="OHDSI database credentials")
    parser.add_argument("--ohdsi_schema", "-sch", action="store", help="OHDSI database credentials")

    args = parser.parse_args()

    input_file_path = args.input_file

    fhir = args.fhir

    ohdsi_host = args.ohdsi_host
    ohdsi_port = args.ohdsi_port
    ohdsi_user = args.ohdsi_user
    ohdsi_password = args.ohdsi_password
    ohdsi_database = args.ohdsi_database
    ohdsi_schema = args.ohdsi_schema

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

    print(input_file_path, standard, fhir, ohdsi)
    return input_file_path, standard, fhir, ohdsi


def fhir(url, file_name):
    """
    Run FHIR data conversion and data quality control.

    :param url: The url of FHIR server.
    :param file_name: The path of input file.
    :return:
        None
    """
    # server
    smart_client = provide_server_connection(url)

    # store resources
    read_xml_and_create_resources(file_name, smart_client)

    # create report
    create_report_fhir(smart_client.server)
    return None


def omop(ohdsi, input_file):
    """
    Run OMOP CDM data conversion and data quality control.

    :param ohdsi: {
    		    "host": The database host.
    		    "port": The database port.,
    		    "user": The database user.
                "password": The database password.
                "database": The database.
                "schema": The database schema.}
    :param input_file: The path of input file.
    :return:
        None
    """
    schema = ohdsi.pop("schema")
    load_data(ohdsi, input_file, schema)

    # create report
    con = psycopg2.connect(**ohdsi)
    create_report_ohdsi(con, schema)
    return None


if __name__ == '__main__':
    input_file_path, standard, url, ohdsi = work_with_arguments()
    if standard == "fhir":
        fhir(url, input_file_path)
    elif standard =="ohdsi":
         omop(ohdsi, input_file_path)
    elif standard == "both":
         fhir(url, input_file_path)
         omop(ohdsi, input_file_path)