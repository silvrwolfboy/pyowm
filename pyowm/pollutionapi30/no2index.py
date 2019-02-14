import json
import xml.etree.ElementTree as ET
from pyowm.pollutionapi30.xsd.xmlnsconfig import NO2INDEX_XMLNS_URL, NO2INDEX_XMLNS_PREFIX
from pyowm.weatherapi25 import location
from pyowm.utils import formatting, timestamps, xml
from pyowm.exceptions import parse_response_error


class NO2Index(object):
    """
    A class representing the Nitrogen DiOxide Index observed in a certain location
    in the world. The index is made up of several measurements, each one at a
    different atmospheric levels. The location is represented by the 
    encapsulated *Location* object.

    :param reference_time: GMT UNIXtime telling when the NO2 data has been measured
    :type reference_time: int
    :param location: the *Location* relative to this NO2 observation
    :type location: *Location*
    :param interval: the time granularity of the NO2 observation
    :type interval: str
    :param no2_samples: the NO2 samples
    :type no2_samples: list of dicts
    :param reception_time: GMT UNIXtime telling when the NO2 observation has
        been received from the OWM Weather API
    :type reception_time: int
    :returns: a *NO2Index* instance
    :raises: *ValueError* when negative values are provided as reception time,
      NO2 samples are not provided in a list

    """

    def __init__(self, reference_time, location, interval, no2_samples,
                 reception_time):
        if reference_time < 0:
            raise ValueError("'reference_time' must be greater than 0")
        self._reference_time = reference_time
        self._location = location
        self._interval = interval
        if not isinstance(no2_samples, list):
            raise ValueError("'no2_samples' must be a list")
        self._no2_samples = no2_samples
        if reception_time < 0:
            raise ValueError("'reception_time' must be greater than 0")
        self._reception_time = reception_time

    def get_reference_time(self, timeformat='unix'):
        """
        Returns the GMT time telling when the NO2 samples have been measured

        :param timeformat: the format for the time value. May be:
            '*unix*' (default) for UNIX time
            '*iso*' for ISO8601-formatted string in the format ``YYYY-MM-DD HH:MM:SS+00``
            '*date* for ``datetime.datetime`` object instance
        :type timeformat: str
        :returns: an int or a str
        :raises: ValueError when negative values are provided

        """
        return formatting.timeformat(self._reference_time, timeformat)

    def get_reception_time(self, timeformat='unix'):
        """
        Returns the GMT time telling when the NO2 observation has been received
        from the OWM Weather API

        :param timeformat: the format for the time value. May be:
            '*unix*' (default) for UNIX time
            '*iso*' for ISO8601-formatted string in the format ``YYYY-MM-DD HH:MM:SS+00``
            '*date* for ``datetime.datetime`` object instance
        :type timeformat: str
        :returns: an int or a str
        :raises: ValueError when negative values are provided

        """
        return formatting.timeformat(self._reception_time, timeformat)

    def get_location(self):
        """
        Returns the *Location* object for this NO2 index measurement

        :returns: the *Location* object

        """
        return self._location

    def get_interval(self):
        """
        Returns the time granularity interval for this NO2 index measurement

        :return: str
        """
        return self._interval

    def get_no2_samples(self):
        """
        Returns the NO2 samples for this index

        :returns: list of dicts

        """
        return self._no2_samples

    def get_sample_by_label(self, label):
        """
        Returns the NO2 sample having the specified label or `None` if none 
        is found

        :param label: the label for the seeked NO2 sample 
        :returns: dict or `None`

        """
        for sample in self._no2_samples:
            if sample['label'] == label:
                return sample
        return None

    def is_forecast(self):
        """
        Tells if the current NO2 observation refers to the future with respect
        to the current date
        :return: bool
        """
        return timestamps.now(timeformat='unix') < \
               self.get_reference_time(timeformat='unix')

    def to_JSON(self):
        """Dumps object fields into a JSON formatted string

        :returns:  the JSON string

        """
        return json.dumps({"reference_time": self._reference_time,
                           "location": json.loads(self._location.to_JSON()),
                           "interval": self._interval,
                           "no2_samples": self._no2_samples,
                           "reception_time": self._reception_time,
                           })

    def to_XML(self, xml_declaration=True, xmlns=True):
        """
        Dumps object fields to an XML-formatted string. The 'xml_declaration'
        switch  enables printing of a leading standard XML line containing XML
        version and encoding. The 'xmlns' switch enables printing of qualified
        XMLNS prefixes.

        :param XML_declaration: if ``True`` (default) prints a leading XML
            declaration line
        :type XML_declaration: bool
        :param xmlns: if ``True`` (default) prints full XMLNS prefixes
        :type xmlns: bool
        :returns: an XML-formatted string

        """
        root_node = self._to_DOM()
        if xmlns:
            xml.annotate_with_XMLNS(root_node,
                                    NO2INDEX_XMLNS_PREFIX,
                                    NO2INDEX_XMLNS_URL)
        return xml.DOM_node_to_XML(root_node, xml_declaration)

    def _to_DOM(self):
        """
        Dumps object data to a fully traversable DOM representation of the
        object.

        :returns: a ``xml.etree.Element`` object

        """
        root_node = ET.Element("no2index")
        reference_time_node = ET.SubElement(root_node, "reference_time")
        reference_time_node.text = str(self._reference_time)
        reception_time_node = ET.SubElement(root_node, "reception_time")
        reception_time_node.text = str(self._reception_time)
        interval_node = ET.SubElement(root_node, "interval")
        interval_node.text = str(self._interval)
        no2_samples_node = ET.SubElement(root_node, "no2_samples")
        for smpl in self._no2_samples:
            s = smpl.copy()
            # turn values to 12 decimal digits-formatted strings
            s['label'] = s['label']
            s['value'] = '{:.12e}'.format(s['value'])
            s['precision'] = '{:.12e}'.format(s['precision'])
            xml.create_DOM_node_from_dict(s, "no2_sample",
                                          no2_samples_node)
        root_node.append(self._location._to_DOM())
        return root_node

    @classmethod
    def from_dict(cls, the_dict):
        """
        Parses an *NO2Index* instance out of a data dictionary. Only certain properties of the data dictionary
        are used: if these properties are not found or cannot be parsed, an exception is issued.

        :param the_dict: the input dictionary
        :type the_dict: `dict`
        :returns: a *NO2Index* instance or ``None`` if no data is available
        :raises: *ParseResponseError* if it is impossible to find or parse the data needed to build the result

        """
        if the_dict is None:
            raise parse_response_error.ParseResponseError('Data is None')
        try:
            # -- reference time (strip away Z and T on ISO8601 format)
            t = the_dict['time'].replace('Z', '+00').replace('T', ' ')
            reference_time = formatting.ISO8601_to_UNIXtime(t)

            # -- reception time (now)
            reception_time = timestamps.now('unix')

            # -- location
            lon = float(the_dict['location']['longitude'])
            lat = float(the_dict['location']['latitude'])
            place = location.Location(None, lon, lat, None)

            # -- CO samples
            no2_samples = [dict(label=key,
                                precision=the_dict['data'][key]['precision'],
                                value=the_dict['data'][key]['value']) for key in the_dict['data']]

        except KeyError:
            raise parse_response_error.ParseResponseError(
                      ''.join([__name__, ': impossible to parse NO2Index']))

        return NO2Index(reference_time, place, None, no2_samples, reception_time)

    def to_dict(self):
        """Dumps object to a dictionary

        :returns: a `dict`

        """
        return {"reference_time": self._reference_time,
                "location": self._location.to_dict(),
                "interval": self._interval,
                "no2_samples": self._no2_samples,
                "reception_time": self._reception_time}

    def __repr__(self):
        return "<%s.%s - reference time=%s, reception time=%s, location=%s, " \
               "interval=%s>" % (
                    __name__,
                    self.__class__.__name__,
                    self.get_reference_time('iso'),
                    self.get_reception_time('iso'),
                    str(self._location),
                    self._interval)
