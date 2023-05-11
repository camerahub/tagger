"""
Functions which interact with the CameraHub API
"""

from datetime import date
from os.path import basename
import json
import requests

def test_credentials(l_server, l_auth):
    """
    Validate a set of credentials
    :param server:
    :param username:
    :param password:
    :return: Bool
    """

    response = requests.get(
            l_server+'/camera',
            auth=l_auth,
            timeout=10
        )

    return bool(response.status_code == 200)


def create_scan(filename, server, auth, negative=None, printid=None):
    """
    Creates a new Scan record in CameraHub, associated with a Negative or Print record
    Returns the uuid of the new Scan record
    {
        "negative": null,
        "print": null,
        "filename": "",
        "date": null
    }
    """

    # Only write the basename of the file
    filename = basename(filename)

    # Create dict
    data = {
        'negative': negative,
        'print': printid,
        'filename': filename,
        'date': date.today()}
    url = server+'/scan/'
    response = requests.post(
        url,
        auth=auth,
        data = data,
        timeout=10
    )
    response.raise_for_status()
    data=json.loads(response.text)
    return data["uuid"]


def get_scan(l_scan, l_server, l_auth):
    """
    Get all details about a scan record in CameraHub
    """
    payload = {'uuid': l_scan}
    url = l_server+'/exif/'
    response = requests.get(
        url,
        auth=l_auth,
        params=payload,
        timeout=10
    )
    response.raise_for_status()

    data=json.loads(response.text)
    if data["count"] == 1:
        scan = data["results"][0]

    return scan


def get_negative(l_film, l_frame, l_server, l_auth):
    """
    Find the negative slug for a negative based on its film slug and frame
    """
    slug = f"{l_film}.{l_frame}"
    payload = {'slug': slug}
    url = l_server+'/negative/'
    response = requests.get(
        url,
        auth=l_auth,
        params=payload,
        timeout=10
    )
    response.raise_for_status()

    data=json.loads(response.text)
    if data["count"] == 1:
        negative = data["results"][0]["slug"]

    return negative


def get_print(l_print, l_server, l_auth):
    """
    Get a print by ID
    """
    payload = {'id_owner': l_print}
    url = l_server+'/print/'+l_print
    response = requests.get(
        url,
        auth=l_auth,
        params=payload,
        timeout=10
    )
    response.raise_for_status()

    data=json.loads(response.text)
    printid = data["id_owner"]
    negative = data["negative"]["slug"]

    return printid, negative