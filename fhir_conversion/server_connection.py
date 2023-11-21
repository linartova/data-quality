from fhirclient import client


def server_establishing(url):
    settings = {
        'app_id': 'my_web_app',
        'api_base': url
    }
    smart = client.FHIRClient(settings=settings)
    return smart


def server_connection(smart):
    return smart.prepare()


def testing_server_before_connection(smart):
    assert not smart.ready


def testing_server_after_connection(smart):
    assert smart.ready
    assert smart.authorize_url is None
