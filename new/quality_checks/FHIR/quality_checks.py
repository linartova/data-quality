from fhirclient import client


def server_establishing():
    settings = {
        'app_id': 'my_web_app',
        'api_base': 'http://localhost:8080/fhir'
    }
    smart = client.FHIRClient(settings=settings)
    return smart


def check_missing_sample_year(server, specimen_url):
    json = server.request_json('http://localhost:8080/fhir/Specimen/' + specimen_url)
    if json.get("collection") is None:
        return False
    if json.get("collection").get("collectedDateTime") is None:
        return False
    return True


def check_missing_sample_material(server, specimen_url):
    json = server.request_json('http://localhost:8080/fhir/Specimen/' + specimen_url)
    if json.get("type") is None:
        return False
    if json.get("type").get("text") is None:
        return False
    return True


def check_missing_histo_values():
    pass
    # 92_1 join left cosi


def check_missing_surgery_values():
    pass
    # nic


def check_missing_patient_values():
    pass
    # 3_1
    # 85_1
    # left join cosi


def check_missing_targeted_therapy():
    pass
    # nic


def check_missing_pharmacotherapy_values():
    pass
    # nic


if __name__ == '__main__':
    smart_client = server_establishing()
    server = smart_client.server
    specimen_urls = ["DDMYJB5JUG3HEKVI", "DDMYJB5MTEZOUHZS", "DDMYJB5OBJMMJ5MX"]
    for specimen_url in specimen_urls:
        check_missing_sample_year(server, specimen_url)
        check_missing_sample_material(server, specimen_url)

