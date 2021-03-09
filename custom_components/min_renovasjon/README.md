# Min renovasjon


Modified component for using Min renovasjon in Home Assistant.
Based on (https://github.com/eyesoft/home-assistant-custom-components/tree/master/min_renovasjon)

## Install
Copy the files to the custom_components folder in Home Assistant config.

In configuration.yaml:

```
min_renovasjon:
  street_name: "Min gate"
  house_no: "12"
  street_code: "12345"
  county_id: "1234"
  date_format: "None"

sensor:
  - platform: min_renovasjon
    fraction_id:
      - 1
      - 2
      - 3
      - 19
  ```

**street_name:**\
The name of the street without house number, e.g. "Slottsplassen".

**house_no:** \
The number of the house, e.g. "1".

**street_code:** \
**county_id:** \
Can be found with this REST-API call.
```
https://ws.geonorge.no/adresser/v1/#/default/get_sok
https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012
```
"street_code" equals to "adressekode" and "county_id" equals to "kommunenummer".

**date_format:** \
Defaults to "%d/%m/%Y" if not specified. If set to "None" no formatting of the date is performed.

**fraction_id:**\
One or more fractions for which a sensor is to be set up. ID's might be different depending on county. Turn on debug logging in Home Asstistant to log the list of fractions
(https://www.home-assistant.io/components/logger/).
```
1: Restavfall
2: Papir
3: Matavfall
4: Glass/Metallemballasje
5: Drikkekartonger
6: Spesialavfall
8: Trevirke
9: Tekstiler
10: Hageavfall
11: Metaller
12: Hvitevarer/EE-avfall
13: Papp
14: Møbler
19: Plastemballasje
23: Nedgravd løsning
24: GlassIGLO
25: Farlig avfall
26: Matavfall hytter
27: Restavfall hytter
28: Papir hytter
```


[Buy me a coffee :)](http://paypal.me/dahoiv)
