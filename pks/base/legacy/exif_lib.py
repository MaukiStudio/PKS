#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from delorean import Delorean


def get_exif_data(image):
    """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]

                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value

    return exif_data


def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


def _convert_to_degress(value):
    """Helper function to convert the GPS coordinates stored in the EXIF to degress in float format"""
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)


def get_lon_lat(exif_data):
    """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
    lat = None
    lon = None

    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]

        gps_latitude = _get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = _get_if_exist(gps_info, 'GPSLatitudeRef')
        gps_longitude = _get_if_exist(gps_info, 'GPSLongitude')
        gps_longitude_ref = _get_if_exist(gps_info, 'GPSLongitudeRef')

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = _convert_to_degress(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = _convert_to_degress(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon

    return lon, lat


def get_timestamp(exif_data):
    raw_date = _get_if_exist(exif_data, 'DateTimeOriginal')
    if not raw_date:
        raw_date = _get_if_exist(exif_data, 'DateTime')
    if not raw_date:
        raw_date = _get_if_exist(exif_data, 'DateTimeDigitized')
    if not raw_date:
        return None

    dt = datetime.strptime(raw_date, '%Y:%m:%d %H:%M:%S')
    # TODO : VD.timezone 을 참조하여 변환
    d = Delorean(dt, timezone='Asia/Seoul')
    return int(round(d.epoch*1000))


def transpose_image_by_exif(im):
    from PIL.Image import FLIP_LEFT_RIGHT, ROTATE_180, FLIP_TOP_BOTTOM, ROTATE_90, ROTATE_270
    exif_orientation_tag = 0x0112 # contains an integer, 1 through 8
    exif_transpose_sequences = [  # corresponding to the following
        [],
        [FLIP_LEFT_RIGHT],
        [ROTATE_180],
        [FLIP_TOP_BOTTOM],
        [FLIP_LEFT_RIGHT, ROTATE_90],
        [ROTATE_270],
        [FLIP_TOP_BOTTOM, ROTATE_90],
        [ROTATE_90],
    ]

    try:
        seq = exif_transpose_sequences[im._getexif()[exif_orientation_tag] - 1]
    except Exception:
        return im
    else:
        return reduce(lambda im, op: im.transpose(op), seq, im)
