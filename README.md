# CameraHub Tagger

CameraHub Tagger is a companion command-line app for [CameraHub](https://camerahub.info/) to tag JPG
scans of negatives with EXIF metadata from the CameraHub API. This means you can organise your film
scans in a digital photo management app with full metadata.

To use CameraHub Tagger, you must already have entered your cameras, lenses, films and negatives into CameraHub. When you scan your negatives, name them consistently like `{FILM}-{FRAME}-IMG0001.jpg` (for example `45-12-IMG0001.jpg` is frame 12 on film 45).

Run CameraHub Tagger in the same directory. CameraHub Tagger will attempt to match the JPGs with the
negatives by using the filename (it will ask you if it can't figure it out). It will then generate a
unique ID for that scanned JPG to tie it conclusively to the negative. Once the link is made, CameraHub
Tagger will retrieve all data about that negative, film, lens and camera and use it to generate EXIF
metadata, the same as digital cameras do. It is safe to run CameraHub Tagger multiple times on the same
files, as only changed tags are written.

When your images have been tagged, any digital photo app will read and display these tags in the same
way as digital photos.

## Installation

Install from [PyPI](https://pypi.org/project/camerahub-tagger/) with Pip:

```console
pip install camerahub-tagger
```

This installs a `tagger` binary in your `$PATH`.

## Usage

```console
tagger [-h] [-r] [-a] [-y] [-d] [-f FILE] [-p PROFILE]
```

### `-h --help`

Display help message and exit

### `-r --recursive`

Search for scans recursively from current directory

### `-a --auto`

Don't prompt user to identify scans, only guess based on filename

### `-y --yes`

Accept all changes without confirmation

### `-d --dry-run`

Don't write any tags to image files

### `-f --file FILE`

Image file to be tagged. If not supplied, tag everything in the current directory.

### `-p --profile PROFILE`

CameraHub connection profile. Default: `prod`.

## Config

CameraHub Tagger needs some basic connection details to connect to CameraHub.
On first run, it will ask for credentials for CameraHub and save them for future use.

If you need multiple profiles (e.g. if you have multiple users, or you need to connect to
a development instance of CameraHub) you can configure the extra profiles manually by editing
`~/camerahub.ini` and adding more blocks.

The names of each profile are arbitrary, but CameraHub Tagger will automatically use the `prod` profile
unless you override it with the `--profile` option. Here's an example:

```ini
[prod]
server = https://camerahub.info/api
username = anseladams
password = yosemite

[dev]
server = https://dev.camerahub.info/api
username = annieleibovitz
password = johnandyoko

[local]
server = http://127.0.0.1:8000/api
username = admin
password = admin
```