import urllib.parse
import requests
import json
from datetime import date
from datetime import datetime
import logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

DOMAIN = "min_renovasjon"
DATA_MIN_RENOVASJON = "data_min_renovasjon"

CONF_STREET_NAME = "street_name"
CONF_STREET_CODE = "street_code"
CONF_HOUSE_NO = "house_no"
CONF_COUNTY_ID = "county_id"
CONF_DATE_FORMAT = "date_format"
DEFAULT_DATE_FORMAT = "%d/%m/%Y"

CONST_KOMMUNE_NUMMER = "Kommunenr"
CONST_APP_KEY = "RenovasjonAppKey"
CONST_URL_FRAKSJONER = (
    "https://komteksky.norkart.no/komtek.renovasjonwebapi/api/fraksjoner"
)
CONST_URL_TOMMEKALENDER = (
    "https://komteksky.norkart.no/komtek.renovasjonwebapi/api/tommekalender?"
    "gatenavn=[gatenavn]&gatekode=[gatekode]&husnr=[husnr]"
)
CONST_APP_KEY_VALUE = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_STREET_NAME): cv.string,
                vol.Required(CONF_STREET_CODE): cv.string,
                vol.Required(CONF_HOUSE_NO): cv.string,
                vol.Required(CONF_COUNTY_ID): cv.string,
                vol.Optional(CONF_DATE_FORMAT, default=DEFAULT_DATE_FORMAT): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up the MinRenovasjon component."""
    street_name = config[DOMAIN][CONF_STREET_NAME]
    street_code = config[DOMAIN][CONF_STREET_CODE]
    house_no = config[DOMAIN][CONF_HOUSE_NO]
    county_id = config[DOMAIN][CONF_COUNTY_ID]
    date_format = config[DOMAIN][CONF_DATE_FORMAT]

    min_renovasjon = MinRenovasjon(
        street_name, street_code, house_no, county_id, date_format
    )
    hass.data[DATA_MIN_RENOVASJON] = min_renovasjon

    return True


class MinRenovasjon:
    def __init__(self, gatenavn, gatekode, husnr, kommunenr, date_format):
        self.gatenavn = self._url_encode(gatenavn)
        self.gatekode = gatekode
        self.husnr = husnr
        self._kommunenr = kommunenr
        self._date_format = date_format
        self._kalender_list = self._get_calendar_list()

    @staticmethod
    def _url_encode(string):
        string_decoded_encoded = urllib.parse.quote(urllib.parse.unquote(string))
        if string_decoded_encoded != string:
            string = string_decoded_encoded
        return string

    def refresh_calendar(self):
        do_refresh = self._check_for_refresh_of_data(self._kalender_list)
        if do_refresh:
            self._kalender_list = self._get_calendar_list()

    def _get_tommekalender_from_web_api(self):
        header = {
            CONST_KOMMUNE_NUMMER: self._kommunenr,
            CONST_APP_KEY: CONST_APP_KEY_VALUE,
        }

        url = CONST_URL_TOMMEKALENDER
        url = url.replace("[gatenavn]", self.gatenavn)
        url = url.replace("[gatekode]", self.gatekode)
        url = url.replace("[husnr]", self.husnr)

        response = requests.get(url, headers=header)
        if response.status_code == requests.codes.ok:
            data = response.text
            return data
        else:
            _LOGGER.error(response.status_code)
            return None

    def _get_fraksjoner_from_web_api(self):
        header = {
            CONST_KOMMUNE_NUMMER: self._kommunenr,
            CONST_APP_KEY: CONST_APP_KEY_VALUE,
        }
        url = CONST_URL_FRAKSJONER

        response = requests.get(url, headers=header)
        if response.status_code == requests.codes.ok:
            data = response.text
            return data
        else:
            _LOGGER.error(response.status_code)
            return None

    def _get_from_web_api(self):
        tommekalender = self._get_tommekalender_from_web_api()
        fraksjoner = self._get_fraksjoner_from_web_api()

        _LOGGER.debug(f"Tommekalender: {tommekalender}")
        _LOGGER.debug(f"Fraksjoner: {fraksjoner}")

        return tommekalender, fraksjoner

    def _get_calendar_list(self, refresh=False):
        data = None

        if refresh or data is None:
            _LOGGER.info("Refresh or no data. Fetching from API.")
            tommekalender, fraksjoner = self._get_from_web_api()
        else:
            tommekalender, fraksjoner = data

        kalender_list = self._parse_calendar_list(tommekalender, fraksjoner)

        check_for_refresh = False
        if not refresh:
            check_for_refresh = self._check_for_refresh_of_data(kalender_list)

        if check_for_refresh:
            kalender_list = self._get_calendar_list(refresh=True)

        _LOGGER.info("Returning calendar list")
        return kalender_list

    @staticmethod
    def _parse_calendar_list(tommekalender, fraksjoner):
        kalender_list = []

        tommekalender_json = json.loads(tommekalender)
        fraksjoner_json = json.loads(fraksjoner)

        for calender_entry in tommekalender_json:
            fraksjon_id = calender_entry["FraksjonId"]
            tommedato_neste = None

            if len(calender_entry["Tommedatoer"]) == 1:
                tommedato_forste = calender_entry["Tommedatoer"][0]
            else:
                tommedato_forste, tommedato_neste = calender_entry["Tommedatoer"]

            if tommedato_forste is not None:
                tommedato_forste = datetime.strptime(
                    tommedato_forste, "%Y-%m-%dT%H:%M:%S"
                )
            if tommedato_neste is not None:
                tommedato_neste = datetime.strptime(
                    tommedato_neste, "%Y-%m-%dT%H:%M:%S"
                )

            for fraksjon in fraksjoner_json:
                if fraksjon["Id"] == fraksjon_id:
                    fraksjon_navn = fraksjon["Navn"]
                    fraksjon_ikon = fraksjon["Ikon"]

                    kalender_list.append(
                        (
                            fraksjon_id,
                            fraksjon_navn,
                            fraksjon_ikon,
                            tommedato_forste,
                            tommedato_neste,
                        )
                    )
                    continue

        return kalender_list

    @staticmethod
    def _check_for_refresh_of_data(kalender_list):
        for entry in kalender_list:
            _, _, _, tommedato_forste, tommedato_neste = entry

            if tommedato_forste is None or tommedato_neste is None:
                _LOGGER.info("Data needs refresh")
                return True
            if (
                tommedato_forste.date() < date.today()
                or tommedato_neste.date() < date.today()
            ):
                _LOGGER.info("Data needs refresh")
                return True

        return False

    def get_calender_for_fraction(self, fraksjon_id):
        for entry in self._kalender_list:
            entry_fraksjon_id, _, _, _, _ = entry
            if fraksjon_id == entry_fraksjon_id:
                return entry

    @property
    def calender_list(self):
        return self._kalender_list

    def format_date(self, date):
        if self._date_format == "None":
            return date
        return date.strftime(self._date_format)
