import requests
import os
from urllib.parse import urljoin
import json


BASE_URL = 'https://api.cloudflare.com/client/v4/'


def get_env_var(var: str):
    try:
        return os.environ[var]
    except KeyError:
        raise RuntimeError(f'environment variable not found: {var}')


def get_public_ip() -> str | None:
    try:
        response = requests.get('https://api.ipify.org')
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        return None
    

def get_cloudfare_api_header():
    api_token = get_env_var('CLOUDFARE_TOKEN')

    return {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }


def cloudfare_api_call(endpoint: str, method: str = 'GET', data: dict = None, raise_error: bool = True) -> dict:
    def is_error_status(status: int):
        return not (200 <= status <= 229)

    request_fun = getattr(requests, method.lower())
    url = urljoin(BASE_URL, endpoint)
    print('sending', method, 'request to', url)
    response = request_fun(
        url,
        headers=get_cloudfare_api_header(),
        json=data,
    )
    response_data = response.json()
    if raise_error and is_error_status(response.status_code):
        raise requests.HTTPError(
            f'{response_data["errors"]}',
            response=response
        )

    return response_data


def get_cloudfare_zone_id() -> str:
    return get_env_var('CLOUDFARE_ZONE_ID')

    res = cloudfare_api_call('zones', 'GET')
    for zone in res['result']:
        if zone['name'] == domain:
            return zone['id']

    raise RuntimeError(f'domain {domain} does not exist')


def get_cloudfare_record_id(zone_id: str) -> str:
    """
    Only update the root A record.
    """
    root_domain = get_env_var('CLOUDFARE_ROOT_DOMAIN')
    res = cloudfare_api_call(f'zones/{zone_id}/dns_records')
    for record in res['result']:
        if record['name'] == root_domain:
            return record['id']
        
    raise RuntimeError(f'record_id not found for root domain {root_domain}')


def overwrite_cloudfare_dns_record(zone_id: str, record_id: str, ip: str, name: str, type: str, proxied: bool):
    return cloudfare_api_call(
        f'zones/{zone_id}/dns_records/{record_id}',
        'PUT',
        data={
            'content': ip,
            'name': name,
            'proxied': proxied,
            'type': type
        }
    )


if __name__ == '__main__':
    ip = get_public_ip()
    zone_id = get_cloudfare_zone_id()
    record_id = get_cloudfare_record_id(zone_id)
    
    res = overwrite_cloudfare_dns_record(
        zone_id,
        record_id,
        ip,
        get_env_var('CLOUDFARE_ROOT_DOMAIN'),
        type='A',
        proxied=True
    )
    print(json.dumps(res, indent=2))

