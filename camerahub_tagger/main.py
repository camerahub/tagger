"""
CameraHub Tagger
"""

import argparse
import os
from fnmatch import filter as fnfilter
import pyexiv2
from requests.models import HTTPError
from camerahub_tagger.config import get_setting
from camerahub_tagger.api import get_negative, get_scan, create_scan, test_credentials
from camerahub_tagger.funcs import is_valid_uuid, guess_frame, prompt_frame, api2exif, diff_tags, yes_or_no

# ----------------------------------------------------------------------
def main():
    print("CameraHub Tagger")

    # Read in args
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--recursive', help="Search for scans recursively", action='store_true')
    parser.add_argument('-a', '--auto', help="Don't prompt user to identify scans, only guess based on filename", action='store_true')
    parser.add_argument('-y', '--yes', help="Accept all changes without confirmation", action='store_true')
    parser.add_argument('-d', '--dry-run', help="Don't write any tags to image files", action='store_true')
    parser.add_argument('-f', '--file', help="Image file to be tagged. If not supplied, tag everything in the current directory.", type=str)
    parser.add_argument('-p', '--profile', help="CameraHub connection profile", default='prod', type=str)
    args = parser.parse_args()

    # Determine path to config file
    home = os.path.expanduser("~")
    configpath = os.path.join(home, "camerahub.ini")

    # Get our initial connection settings
    # Prompt the user to set them if they don't exist
    server = get_setting(configpath, args.profile, 'server')
    username = get_setting(configpath, args.profile, 'username')
    password = get_setting(configpath, args.profile, 'password')

    # Create auth object
    auth = (username, password)

    # Test the credentials we have
    try:
        test_credentials(server, auth)
    except:
        print("Creds not OK")
        raise PermissionError
    print("Creds OK")


    # if no args, scan current folder. consider recursive option
    # elsif load individual frame
    # or quit if none

    files = []
    if args.file:
        files.append(args.file)
    elif args.recursive:
        # recursive search here
        pass
    else:
        files = fnfilter(os.listdir('.'), '*.[Jj][Pp][Gg]')

    if len(files) == 0:
        print("No files found")

    # foreach found photo:
    # read exif data, check for camerahub scan tag
    for file in files:
        print(f"Processing image {file}")

        # Extract exif data from file
        with pyexiv2.Image(file) as img:
            existing = img.read_exif()

        # Example format
        # existing = {'Exif.Image.DateTime': '2019:06:23 19:45:17', 'Exif.Image.Artist': 'TEST', 'Exif.Image.Rating': '4', ...}

        if existing is not None and 'Exif.Photo.ImageUniqueID' in existing and is_valid_uuid(existing['Exif.Photo.ImageUniqueID']):
            # check for presence of custom exif tag for camerahub
            # already has a uuid scan id
            print(f"{file} already has an EXIF scan ID")
            scan = existing['Exif.Photo.ImageUniqueID']
        else:
            # need to match it with a neg/print and generate a scan id
            print(f"{file} does not have an EXIF scan ID")

            # else prompt user to identify the scan
            #	guess film/frame from filename
            guess = guess_frame(file)
            if type(guess) is tuple:
                film, frame = guess
                print(f"Deduced Film ID {film} and Frame {frame}")

            else:
                print(f"{file} does not match FILM-FRAME notation")
                # prompt user for film/frame
                #	either accept film/frame or just film then prompt frame
                film, frame = prompt_frame(file)

            # Lookup Negative from API
            try:
                negative = get_negative(film, frame, server, auth)
            except HTTPError as err:
                print(err)
                continue
            except:
                print(f"Couldn't find Negative ID for {file}")
                continue
            else:
                print(f"{file} corresponds to Negative {negative}")

            # Create Scan record associated with the Negative
            try:
                scan = create_scan(negative, file, server, auth)
            except:
                print(f"Couldn't generate Scan ID for Negative {negative}")
                continue
            else:
                print(f"Created new Scan ID {scan}")

        # Lookup extended Scan details in API
        try:
            apidata = get_scan(scan, server, auth)
        except:
            print(f"Couldn't retrieve data for Scan {scan}")
        else:
            print(f"Got data for Scan {scan}")

        # mangle CameraHub format tags into EXIF format tags
        exifdata = api2exif(apidata)

        # prepare diff of tags
        diff = diff_tags(existing, exifdata)
        prettydiff = diff.pretty()
        diff = diff.to_dict()

        # if non-zero diff, ask user to confirm tag write
        if len(diff) > 0:
            # print diff & confirm write
            print(prettydiff)

            if not args.dry_run:
                if args.yes or yes_or_no("Write this metadata to the file?"):

                    # Apply the diff to the image
                    with pyexiv2.Image(file) as img:
                        img.modify_exif(exifdata)

if __name__ == "__main__":
    main()