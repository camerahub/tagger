"""
Utility functions with few external dependencies
"""

from decimal import Decimal
from deepdiff import DeepDiff
from uuid import UUID
from os.path import basename
import re

def deg_to_dms(degrees):
    """
    Convert from decimal degrees to degrees, minutes, seconds.
    """
    degrees = Decimal(degrees)
    mins, secs = divmod(abs(degrees)*3600, 60)
    degs, mins = divmod(mins, 60)
    degs, mins = int(degs), int(mins)
    return degs, mins, secs


def gps_ref(direction, angle):
    """
    Return the direction of a GPS coordinate
    """
    angle=Decimal(angle)
    if direction == 'latitude':
        hemi = 'N' if angle>=0 else 'S'
    elif direction == 'longitude':
        hemi = 'E' if angle>=0 else 'W'
    else:
        hemi = None
    return hemi


def diff_tags(dicta, dictb):
    """
    Compare two dictionaries of EXIF tags and return a dictionary which contains
    the diff required to apply b's data to a, without destroying data in a.
    """

    # First merge/overwrite b into a copy of a
    merged = dicta | dictb

    # Now diff a with the merged dict
    deepdiff = DeepDiff(dicta, merged)

    return deepdiff


def walk(indict, pre=None):
    """
    Walk a structured, nested dictionary and it return it as a flattened list
    Each item in the stucture is returned as a list consisting of each part of
    the hierarchy and finally the value. For example,
    """
    pre = pre[:] if pre else []
    if isinstance(indict, dict):
        for key, value in indict.items():
            if isinstance(value, dict):
                for d in walk(value, pre + [key]):
                    yield d
            elif isinstance(value, (list, tuple)):
                for v in value:
                    for d in walk(v, pre + [key]):
                        yield d
            else:
                yield pre + [key, value]
    else:
        yield pre + [indict]


def yes_or_no(question):
    """
    Prompt for a yes/no answer
    https://gist.github.com/garrettdreyfus/8153571#gistcomment-2586248
    """
    answer = input(question + "(y/n): ").lower().strip()
    print("")
    while not answer in ('y', 'yes', 'n', 'no'):
        print("Input yes or no")
        answer = input(question + "(y/n):").lower().strip()
        print("")
    return bool(answer[0] == "y")


def is_valid_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.
    """

    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def guess_frame(filepath):
    """
    Guess a negative's film id and frame id based on its filename
    Assumes a format of [film]-[frame]-title.jpg
    for example 123-22-holiday.jpg
    """
    filename = basename(filepath)
    match = re.search(r'^(\d+)-(\d+).*\.jpe?g$', filename.lower())
    if match and match.group(1) and match.group(2):
        returnval = (match.group(1), match.group(2))
    else:
        returnval = None
    return returnval


def prompt_frame(filename):
    """
    Prompt user to enter film id and frame id
    At the moment these questions are asked sequentially
    TODO: be able to parse compact film/frame format
    """
    l_film = input(f"Enter film ID for {filename}: ")
    l_frame = input(f"Enter frame ID for {l_film}: ")
    return (l_film, l_frame)


def apitag2exiftag(apitag):
    """
    When given a CameraHub API tag, flattened and formatted with dots,
    map it to its equivalent EXIF tag, or return None
    https://exif.readthedocs.io/en/latest/api_reference.html#image-attributes
    """

    #'Lens',
    #'FNumber'

    # Static mapping of tags from the short EXIF name
    # to the fully qualified names required by pyexiv2
    mapping = {
        'ImageUniqueID': 'Exif.Photo.ImageUniqueID',
        'Make': 'Exif.Image.Make',
        'LensMake': 'Exif.Photo.LensMake',
        'Model': 'Exif.Image.Model',
        'BodySerialNumber': 'Exif.Photo.BodySerialNumber',
        'ISOSpeed': 'Exif.Photo.ISOSpeed',
        'LensModel': 'Exif.Photo.LensModel',
        'ExposureProgram': 'Exif.Image.ExposureProgram',
        'MeteringMode': 'Exif.Image.MeteringMode',
        'ImageDescription': 'Exif.Photo.UserComment',
        'DateTimeOriginal': 'Exif.Image.DateTimeOriginal',
        'FNumber': 'Exif.Image.FNumber',
        'UserComment': 'Exif.Photo.UserComment',
        'FocalLength': 'Exif.Image.FocalLength',
        'Flash': 'Exif.Photo.Flash',
        'Artist': 'Exif.Image.Artist',
        'LensSerialNumber': 'Exif.Photo.LensSerialNumber',
        'ShutterSpeedValue': 'Exif.Photo.ExposureTime',
        'MaxApertureValue': 'Exif.Image.MaxApertureValue',
        'Copyright': 'Exif.Image.Copyright',
        'FocalLengthIn35mmFilm': 'Exif.Photo.FocalLengthIn35mmFilm',
    }

    exiftag = mapping.get(apitag)
    return exiftag


def api2exif(l_apidata):
    """
    Reformat CameraHub format tags into EXIF format tags.
    CameraHub tags from the API will be JSON-formatted whereas EXIF
    tags are formatted as a simple dictionary. This will also translate
    tags that have different names.
    """
    # Retrieve the flattened walk data as a list of lists
    data = walk(l_apidata)

    # Make a new dictionary of EXIF data to return
    l_exifdata = {}

    # Each item is one member of the nested structure
    for row in data:
        # The value is the last member of the list
        value = row.pop()

        # If the value is not None, build its key by concating the path
        if value is not None:
            key = ('.'.join(row))

            # Check for "special" tags that need computation
            if key == 'negative.latitude':
                l_exifdata['Exif.GPSInfo.GPSLatitude'] = deg_to_dms(value)
                l_exifdata['Exif.GPSInfo.GPSLatitudeRef'] = gps_ref('latitude', value)
            elif key == 'negative.longitude':
                l_exifdata['Exif.GPSInfo.GPSLongitude'] = deg_to_dms(value)
                l_exifdata['Exif.GPSInfo.GPSLongitudeRef'] = gps_ref('longitude', value)
            else:
                # Otherwise do a 1:1 mapping
                exifkey = apitag2exiftag(key)
                if exifkey is not None:
                    # Cast all keys as strings
                    l_exifdata[exifkey] = str(value)

    # Rationals need specialist handling
    if 'Exif.Image.FocalLength' in l_exifdata:
        l_exifdata['Exif.Image.FocalLength'] = str(int(float(l_exifdata['Exif.Image.FocalLength'])))+'/1'

    if 'Exif.Photo.FocalLengthIn35mmFilm' in l_exifdata:
        l_exifdata['Exif.Photo.FocalLengthIn35mmFilm'] = str(int(float(l_exifdata['Exif.Photo.FocalLengthIn35mmFilm'])))+'/1'

    return l_exifdata
