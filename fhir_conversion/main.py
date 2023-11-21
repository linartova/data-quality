import sys
import getopt
from server_connection import *
from create_fhir_resources.create_resources import create_resources
from create_fhir_resources.parsing_document import read_xml_and_create_classes


def work_with_arguments(argv):
    input_file = ''
    server_url = ''
    try:
        opts, args = getopt.getopt(argv, "hd:s:", ["data_file_name=", "server_url="])
    except getopt.GetoptError:
        print('main.py -d <data_file_name> -s <server_url>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('main.py -d <data_file_name> -s <server_url>')
            sys.exit()
        elif opt in ("-d", "--data_file_name"):
            input_file = arg
        elif opt in ("-s", "--server_url"):
            server_url = arg
    return input_file, server_url


def main(url, file_name):
    # data
    data = read_xml_and_create_classes(file_name)

    # server
    smart_client = server_establishing(url)
    testing_server_before_connection(smart_client)
    server_connection(smart_client)
    testing_server_after_connection(smart_client)

    # resources
    for record in data:
        create_resources(record[0], record[1], record[2], smart_client)


if __name__ == "__main__":
    arguments = sys.argv[1:]
    file_name, server_url = work_with_arguments(arguments)
    main(server_url, file_name)
    # file_name = 'import_example.xml'
    # url = 'http://localhost:8080/fhir'
