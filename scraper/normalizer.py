"""
normalizer.py

Provides a standard tender structure across all parsers.
"""

from copy import deepcopy


DEFAULT_TENDER = {

    "Source": "",
    "Source URL": "",

    "Unit Name": "",

    "Tender Number": "",

    "Tender Title": "",

    "Publishing Date": None,

    "Closing Date": None,

    "Status": "",

    "Days Left": None,

    "Tender": "",

    "Tender URL": "",

    "Corrigendum": "",

    "Corrigendum URL": "",
}


def normalize_tender(data: dict):

    tender = deepcopy(DEFAULT_TENDER)

    for key, value in data.items():

        if key in tender:

            tender[key] = value

    return tender