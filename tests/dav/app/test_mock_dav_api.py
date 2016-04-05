import datetime as dt
from decimal import Decimal
from mock import Mock
import unittest
from aqxWeb.dav.app.dav_api import DavAPI
from datetime import datetime


class DavTests(unittest.TestCase):

    # mock method for get_system_measurement

    def test_get_system_measurement(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        result = ((321321,10),(321321,10))
        measurement_info = [(1, u'alkalinity', u'mg/L', u'60', u'140'), (2, u'ammonium', u'mg/L', u'0', u'1'), (3, u'chlorine', u'mg/L', None, None), (4, u'hardness', u'mg/L', u'60', u'140'), (5, u'light', None, None, None), (6, u'nitrate', u'mg/L', u'5', u'150'), (7, u'nitrite', u'mg/L', u'0', u'0.25'), (8, u'o2', u'mg/L', None, None), (9, u'ph', None, u'6.0', u'7.0'), (10, u'temp', u'celsius', u'22', u'30'), (11, u'time', None, None, None)]
        a = tuple(("light",))
        d.mea.get_all_measurement_info.return_value= tuple(measurement_info)
        d.mea.get_latest_value.return_value = tuple(result)
        d.mea.get_measurement_name.return_value = tuple(("light",))
        result = d.get_system_measurement('555d0cfe9ebc11e58153000c29b92d09','9')
        self.assertEquals('{"records": [{"value": "10", "time": "321321"}, {"value": "10", "time": "321321"}], "system_uid": "555d0cfe9ebc11e58153000c29b92d09"}', result)

    # mock method for get_system_measurement_names

    def test_get_all_measurement_names(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        result = (u'o2', u'ph', u'temp', u'alkalinity', u'ammonium', u'chlorine', u'hardness', u'light', u'nitrate', 'time')
        d.mea.get_all_measurement_names.return_value = tuple(result)
        result = d.get_all_measurement_names()
        self.assertEquals('{"types": ["o2", "ph", "temp", "alkalinity", "ammonium", "chlorine", "hardness", "light", "nitrate", "time", "time"]}', result)

    # mock method for get_system_measurements

    def test_get_system_measurements(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        all_measurement_names = ((u'o2',), (u'ph',), (u'temp',), (u'alkalinity',), (u'ammonium',), (u'chlorine',), (u'hardness',), (u'light',), (u'nitrate',), (u'time',))
        d.mea.get_all_measurement_names.return_value = tuple(all_measurement_names)
        latest_value = [(dt.datetime(2016, 1, 14, 20, 0), Decimal('0E-10'))]
        d.mea.get_latest_value.return_value = tuple(latest_value)
        result = d.get_system_measurements('555d0cfe9ebc11e58153000c29b92d09')
        self.assertEquals('{"system_uid": "555d0cfe9ebc11e58153000c29b92d09", "measurements": [{"name": "o2", "value": "0E-10", "time": "2016-01-14 20:00:00"}, {"name": "ph", "value": "0E-10", "time": "2016-01-14 20:00:00"}, {"name": "temp", "value": "0E-10", "time": "2016-01-14 20:00:00"}, {"name": "alkalinity", "value": "0E-10", "time": "2016-01-14 20:00:00"}, {"name": "ammonium", "value": "0E-10", "time": "2016-01-14 20:00:00"}, {"name": "chlorine", "value": "0E-10", "time": "2016-01-14 20:00:00"}, {"name": "hardness", "value": "0E-10", "time": "2016-01-14 20:00:00"}, {"name": "light", "value": "0E-10", "time": "2016-01-14 20:00:00"}, {"name": "nitrate", "value": "0E-10", "time": "2016-01-14 20:00:00"}]}', result)

    # mock test for get_readings_for_plot
    def test_get_readings_for_plot(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        d.sys = Mock()
        result =  {'555d0cfe9ebc11e58153000c29b92d09': {'nitrate': [], 'ph': [], 'o2': []}, '8fb1f712bf1d11e5adcc000c29b92d09': {'nitrate': [], 'ph': [], 'o2': []}}
        d.mea.get_measurement_name_list.return_value = [(u'nitrate',), (u'o2',), (u'ph',)]
        d.mea.get_measurements.return_value = result
        d.sys.get_system_name.return_value = 'xyz'
        result = d.get_readings_for_plot(['555d0cfe9ebc11e58153000c29b92d09'],['9'])
        self.assertEquals('{"response": [{"system_uid": "555d0cfe9ebc11e58153000c29b92d09", "name": "xyz", "measurement": [{"values": [], "type": "nitrate"}, {"values": [], "type": "o2"}, {"values": [], "type": "ph"}]}]}', result)

    # mock test for get_all_measurement_info
    def test_get_all_measurement_info(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        expected_result = [(1, u'alkalinity', u'mg/L', u'60', u'140'), (2, u'ammonium', u'mg/L', u'0', u'1'), (3, u'chlorine', u'mg/L', None, None), (4, u'hardness', u'mg/L', u'60', u'140'), (5, u'light', None, None, None), (6, u'nitrate', u'mg/L', u'5', u'150'), (7, u'nitrite', u'mg/L', u'0', u'0.25'), (8, u'o2', u'mg/L', None, None), (9, u'ph', None, u'6.0', u'7.0'), (10, u'temp', u'celsius', u'22', u'30'), (11, u'time', None, None, None)]
        d.mea.get_all_measurement_info.return_value = tuple(expected_result)
        actual_result = d.get_all_measurement_info()
        self.assertEquals('{"measurement_info": {"temp": {"max": "30", "id": 10, "unit": "celsius", "min": "22"}, "light": {"max": null, "id": 5, "unit": null, "min": null}, "alkalinity": {"max": "140", "id": 1, "unit": "mg/L", "min": "60"}, "ammonium": {"max": "1", "id": 2, "unit": "mg/L", "min": "0"}, "nitrite": {"max": "0.25", "id": 7, "unit": "mg/L", "min": "0"}, "chlorine": {"max": null, "id": 3, "unit": "mg/L", "min": null}, "time": {"max": null, "id": 11, "unit": null, "min": null}, "nitrate": {"max": "150", "id": 6, "unit": "mg/L", "min": "5"}, "ph": {"max": "7.0", "id": 9, "unit": null, "min": "6.0"}, "o2": {"max": null, "id": 8, "unit": "mg/L", "min": null}, "hardness": {"max": "140", "id": 4, "unit": "mg/L", "min": "60"}}}', actual_result)

    # mock method for get_system_measurements (when system with the given system_uid does not exist)

    def test_get_system_measurements_with_nonexistent_system_uid(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        all_measurement_names = ((u'o2',), (u'ph',), (u'temp',), (u'alkalinity',), (u'ammonium',), (u'chlorine',), (u'hardness',), (u'light',), (u'nitrate',), (u'time',))
        d.mea.get_all_measurement_names.return_value = tuple(all_measurement_names)
        latest_value = {'error': u"Table 'projectfeed.aqxs_o2_2' doesn't exist"}
        d.mea.get_latest_value.return_value = latest_value
        # system_uid = 2 does not exist
        result = d.get_system_measurements('2')
        self.assertEquals('{"error": "Table \'projectfeed.aqxs_o2_2\' doesn\'t exist"}', result)

    # mock method for get_system_measurement (when system with the given system_uid does not exist)

    def test_get_system_measurement_with_nonexistent_system_uid(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        measurement_info = [(1, u'alkalinity', u'mg/L', u'60', u'140'), (2, u'ammonium', u'mg/L', u'0', u'1'), (3, u'chlorine', u'mg/L', None, None), (4, u'hardness', u'mg/L', u'60', u'140'), (5, u'light', None, None, None), (6, u'nitrate', u'mg/L', u'5', u'150'), (7, u'nitrite', u'mg/L', u'0', u'0.25'), (8, u'o2', u'mg/L', None, None), (9, u'ph', None, u'6.0', u'7.0'), (10, u'temp', u'celsius', u'22', u'30'), (11, u'time', None, None, None)]
        d.mea.get_all_measurement_info.return_value= tuple(measurement_info)
        d.mea.get_latest_value.return_value = {'error': u"Table 'projectfeed.aqxs_alkalinity_2' doesn't exist"}
        d.mea.get_measurement_name.return_value = tuple(("alkalinity",))
        # system_uid = 2 does not exist
        # measurement_id: 1 = alkalinity
        result = d.get_system_measurement('2','1')
        self.assertEquals('{"error": "Table \'projectfeed.aqxs_alkalinity_2\' doesn\'t exist"}', result)

    # mock method for get_system_measurement (when an invalid measurement_id is given)

    def test_get_system_measurement_with_invalid_measurement_id(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        measurement_info = [(1, u'alkalinity', u'mg/L', u'60', u'140'), (2, u'ammonium', u'mg/L', u'0', u'1'), (3, u'chlorine', u'mg/L', None, None), (4, u'hardness', u'mg/L', u'60', u'140'), (5, u'light', None, None, None), (6, u'nitrate', u'mg/L', u'5', u'150'), (7, u'nitrite', u'mg/L', u'0', u'0.25'), (8, u'o2', u'mg/L', None, None), (9, u'ph', None, u'6.0', u'7.0'), (10, u'temp', u'celsius', u'22', u'30'), (11, u'time', None, None, None)]
        d.mea.get_all_measurement_info.return_value= tuple(measurement_info)
        # measurement_id: 100 = invalid measurement_id
        result = d.get_system_measurement('555d0cfe9ebc11e58153000c29b92d09','100')
        self.assertEquals('{"error": "Invalid measurement id"}', result)

    # mock method for put_system_measurement (when the value at the given time is already recorded)
    def test_put_system_measurement_already_recorded_time(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        data = {'system_uid': '555d0cfe9ebc11e58153000c29b92d09', 'measurement_id': '5', 'time': '2018-03-19 23:28:57',
                'value': '111'}
        d.mea.get_measurement_name.return_value = (u'light',)
        d.mea.put_system_measurement.return_value = 'Value at the given time already recorded'
        result = d.put_system_measurement(data)
        self.assertEquals('{"status": {"message": "Value at the given time already recorded"}}', result)

    # mock method for put_system_measurement (when the value at the given time is current time)
    def test_put_system_measurement_with_current_time(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        time_now = datetime.now()
        data = {'system_uid': '555d0cfe9ebc11e58153000c29b92d09', 'measurement_id': '5', 'time': str(time_now),
                'value': '111'}
        d.mea.get_measurement_name.return_value = (u'light',)
        d.mea.put_system_measurement.return_value = 'Record successfully inserted'
        result = d.put_system_measurement(data)
        self.assertEquals('{"status": {"message": "Record successfully inserted"}}', result)

    # mock method for get_all_measurement_info
    def test_get_all_measurement_info(self):
        d = DavAPI(Mock())
        d.mea = Mock()
        measurement_info = [(1, u'alkalinity', u'mg/L', u'60', u'140'), (2, u'ammonium', u'mg/L', u'0', u'1'), (3, u'chlorine', u'mg/L', None, None), (4, u'hardness', u'mg/L', u'60', u'140'), (5, u'light', None, None, None), (6, u'nitrate', u'mg/L', u'5', u'150'), (7, u'nitrite', u'mg/L', u'0', u'0.25'), (8, u'o2', u'mg/L', None, None), (9, u'ph', None, u'6.0', u'7.0'), (10, u'temp', u'celsius', u'22', u'30'), (11, u'time', None, None, None)]
        d.mea.get_all_measurement_info.return_value= tuple(measurement_info)
        result = d.get_all_measurement_info()
        self.assertEquals('{"measurement_info": {"temp": {"max": "30", "id": 10, "unit": "celsius", "min": "22"}, "light": {"max": null, "id": 5, "unit": null, "min": null}, "alkalinity": {"max": "140", "id": 1, "unit": "mg/L", "min": "60"}, "ammonium": {"max": "1", "id": 2, "unit": "mg/L", "min": "0"}, "nitrite": {"max": "0.25", "id": 7, "unit": "mg/L", "min": "0"}, "chlorine": {"max": null, "id": 3, "unit": "mg/L", "min": null}, "time": {"max": null, "id": 11, "unit": null, "min": null}, "nitrate": {"max": "150", "id": 6, "unit": "mg/L", "min": "5"}, "ph": {"max": "7.0", "id": 9, "unit": null, "min": "6.0"}, "o2": {"max": null, "id": 8, "unit": "mg/L", "min": null}, "hardness": {"max": "140", "id": 4, "unit": "mg/L", "min": "60"}}}', result)




