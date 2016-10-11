import datetime
import decimal
import json
import random
import re
from collections import defaultdict

from flask import current_app

from aqxWeb.analytics.dao.metadata import MetadataDAO
from aqxWeb.analytics.dao.measurements import MeasurementsDAO
from aqxWeb.analytics.dao.systems import SystemsDAO
from aqxWeb.social.models import social_graph
from aqxWeb.social.dao.users import UserDAO


def to_float(value):
    if value is not None:
        return float(value)
    else:
        return 0.0

class AnalyticsAPI:

    def __init__(self, app):
        self.sys = SystemsDAO(app)
        self.met = MetadataDAO(app)
        self.mea = MeasurementsDAO(app)
        self.user_dao = UserDAO(social_graph())

    def get_all_systems_info(self):
        systems = self.sys.get_all_systems_info()
        if 'error' in systems:
            return json.dumps(systems)
        # Create a list of systems
        systems_list = []
        for system in systems:
            # For each system, create a system
            if system[4] is None and system[5] is None:
                lat = system[13]
                lng = system[14]
            else:
                lat = system[4]
                lng = system[5]

            user = self.user_dao.get_user_by_sql_id(system[1])
            # only display users that have an available user in the graph
            if user is not None:
                info_string = user['displayName']
                if user['organization'] is not None:
                    info_string += ', %s' % user['organization']

                obj = {'system_uid': system[0],
                       'user_id': system[1],
                       'system_name': system[2],
                       'start_date': str(system[3]),
                       'lat': str(lat),
                       'lng': str(lng),
                       'status': str(system[6]),
                       'aqx_technique_name': system[7],
                       'growbed_media': system[8],
                       'crop_name': system[9],
                       'crop_count': system[10],
                       'organism_name': system[11],
                       'organism_count': system[12],
                       'info': info_string
                }
                systems_list.append(obj)

        return json.dumps({'systems': systems_list})

    def get_all_filters_metadata(self):
        results = self.met.get_all_filters()
        if 'error' in results:
            return json.dumps(results)
        values = defaultdict(list)
        for result in results:
            measurement_type = result[0]
            value = result[1]
            values[measurement_type].append(value)
        return json.dumps({'filters': values})

    def get_system_measurements(self, system_uid):
        # Fetch names of all the measurements
        names = self.mea.get_all_measurement_names()
        if 'error' in names:
            return json.dumps(names)
        # Create a list to store the name, latest time and value of all the measurements
        x = []
        # For each measurement
        for name in names:
            # Fetch the name of the measurement using regular expression
            measurement_name = name[0]
            if measurement_name != 'time':
                # As each measurement of a system has a table on it's own,
                # we need to create the name of each table.
                # Each measurement table is: aqxs_measurementName_systemUID
                table_name = self.get_measurement_table_name(measurement_name, system_uid)

                num_of_records = 1
                # Get the latest value stored in the table
                value = self.mea.get_latest_value(table_name, num_of_records)
                if 'error' in value:
                    return json.dumps(value)
                # Append the value to the latest_value[] list
                if len(value) == 1:
                    value_temp = value[0]
                    measurement_value = decimal.Decimal(value_temp[1])
                    if measurement_value.is_normal():
                        normalized_measurement_value = measurement_value
                    else:
                        normalized_measurement_value = measurement_value.normalize()
                    normalized_measurement_value_reduced_decimal = "%.2f" % normalized_measurement_value
                    temp = {
                        'name': measurement_name,
                        'time': str(value_temp[0]),
                        'value': str(normalized_measurement_value_reduced_decimal),
                        'updated_at': value_temp[2].strftime('%Y-%m-%d %H:%M:%S') if value_temp[2] else None
                    }
                else:
                    temp = {
                        'name': measurement_name,
                        'time': None,
                        'value': None,
                        'updated_at': None
                    }

                x.append(temp)

        obj = {
            'system_uid': str(system_uid),
            'measurements': x
        }
        return json.dumps(obj)

    @staticmethod
    def get_measurement_name(name):
            return re.findall(r"\(u'(.*?)',\)", str(name))[0]

    @staticmethod
    def get_measurement_table_name(measurement_name, system_uid):
        table_name = "aqxs_" + measurement_name + "_" + system_uid
        return table_name

    def get_system_measurement(self, system_uid, measurement_id):
        # Encode the measurement_id
        measurement_id_encoded = measurement_id.encode('utf-8')
        # Check if the encoded value is a valid number
        is_given_measurement_id_digit = measurement_id_encoded.isdigit()
        # If the given measurement_id is a valid number, convert it to an integer,
        # Else it is an invalid measurement_id
        if is_given_measurement_id_digit:
            measurement_id_encoded_int = int(measurement_id_encoded)
        else:
            return json.dumps({'error': 'Invalid measurement id'})
        # Fetch the measurement information of all the measurements
        measurement_info = self.mea.get_all_measurement_info()
        # List that stores all the measurement ids
        measurement_id_list = []
        # For each measurement in the measure_info, fetch the measurement id and
        # append to the measurement_id_list
        for each_measurement in measurement_info:
            measurement_id_info = each_measurement[0]
            measurement_id_list.append(measurement_id_info)
        # If the given measurement_id (encoded) in present in the measurement_id_list,
        # then it is a valid id. Else it is an invalid id.
        if measurement_id_encoded_int in measurement_id_list:
            # Fetch the name of the measurement
            measurement = self.mea.get_measurement_name(measurement_id)
        else:
            return json.dumps({'error': 'Invalid measurement id'})
        if 'error' in measurement:
            return json.dumps(measurement)
        # Number of latest recorded to be returned
        # Light: 7
        # All other measurements: 1
        if measurement[0] == 'light':
            num_of_records = 7
        else:
            num_of_records = 1
        # Create the name of the table
        table_name = self.get_measurement_table_name(measurement[0], system_uid)
        # Get the latest value recorded in that table
        result = self.mea.get_latest_value(table_name, num_of_records)
        if 'error' in result:
            return json.dumps(result)
        values = []
        for result_temp in result:
            measurement_value = decimal.Decimal(result_temp[1])
            if measurement_value.is_normal():
                normalized_measurement_value = measurement_value
            else:
                normalized_measurement_value = measurement_value.normalize()
            normalized_measurement_value_reduced_decimal = "%.2f" % normalized_measurement_value
            values_temp = {
                'time': str(result_temp[0]),
                'value': str(normalized_measurement_value_reduced_decimal)
            }
            values.append(values_temp)
        obj = {
            'system_uid': system_uid,
            'records': values
        }
        return json.dumps(obj)

    def put_system_measurement(self, system_uid, measurement_id, time, value):
        measurement = self.mea.get_measurement_name(measurement_id)
        if 'error' in measurement:
            return json.dumps(measurement)
        measurement_name = measurement[0]
        # Create the name of the table
        table_name = self.get_measurement_table_name(measurement_name, system_uid)
        result = self.mea.put_system_measurement(table_name, time, value)
        if 'error' in result:
            return json.dumps(result)
        message = {
            "message": result
        }
        return json.dumps({'status': message})

    def get_readings_for_plot(self, system_uid_list, measurement_id_list,status_id):
        # Form a list of names from the list of ids
        measurement_type_list = self.mea.get_measurement_name_list(measurement_id_list)

        # Return if there is any error in getting the measurement type names
        if 'error' in measurement_type_list:
            error_msg = measurement_type_list
            return json.dumps(error_msg)

        # If there is no type for given id throw an exception
        if not measurement_type_list:
            error_msg = "No data found for " + "measurement_id_list: " + str(measurement_id_list)
            raise ValueError(error_msg)

        # Returned list is list of tuples. Separating measurement type names from tuple
        measurement_name_list = []
        for name in measurement_type_list:
            measurement_name_list.append(str(name[0]))

        # Retrieve the measurements calling DAO
        data_retrieved = self.mea.get_measurements(system_uid_list, measurement_name_list,status_id)

        # Retrieve the annotations
        annotations = self.mea.get_annotations(system_uid_list)

        status = self.mea.get_status_type(status_id)

        if 'error' in data_retrieved:
            return json.dumps(data_retrieved)

        system_measurement_list = []

        for system_uid in system_uid_list:
            readings = data_retrieved[system_uid]

            system_measurement_json = self.form_system_measurement_json(system_uid, readings, annotations[system_uid],
                                                                        measurement_name_list,status)
            system_measurement_list.append(system_measurement_json)

        return json.dumps({"response": system_measurement_list})

    def form_system_measurement_json(self, system_uid, readings,annotations, measurement_type_list,status):
        measurement_list = []

        # For each measurement type, form the list of readings
        for measurement_type in measurement_type_list:

            reading_obj = {
                         "value_list" : [],
                         "annotation_index_list" : []
            }
            if readings:
                if readings[measurement_type]:
                    value_list = self.form_values_list(self, measurement_type, readings[measurement_type])

                    if value_list :
                        reading_obj = self.update_value_list(value_list,annotations)


            measurement = {
                "type": measurement_type,
                "annotation_indices": reading_obj["annotation_index_list"],
                "values": reading_obj["value_list"]
            }
            measurement_list.append(measurement)
        system_name = self.sys.get_system_name(system_uid)
        if 'error' in system_name:
            return system_name
        system_measurement = {
            "system_uid": system_uid,
            "name": system_name,
            "status" : status,
            "measurement": measurement_list
        }

        return system_measurement

    @staticmethod
    def form_values_list(self, measurement_type, all_readings):
        """
        Form the list of values
        Parameters:
          - measurement_type : name of the type of measurement
          - all_readings : readings associated with input measurement_type
        returns the list of readings formed from input readings. ALl the readings that
        fall in 1-hour bucket from time of first reading  are averaged and readings
        is timestamped with latest timestamp in the bucket."""
        value_list = []

        # Initialize the variables
        start_date = all_readings[0][1]
        prev_reading = all_readings[0]
        prev_x = 0
        # Required variable for averaging
        total = 0
        counter = 0

        # Every time  'values' is formed for previous reading if it falls outside the bucket, otherwise averaging is
        # done, over the bucket

        for i in range(1, len(all_readings) + 1):
            try:
                # This condition takes care of the last reading, which gets left out
                if i == len(all_readings):
                    # By incrementing x deliberately, we enforce the 'values' formation for the very last reading
                    reading = prev_reading
                    x = prev_x + 1
                # This condition takes care of all but the last reading
                else:
                    reading = all_readings[i]
                    cur_date = reading[1]
                    # Calculate the difference in hours from previous reading
                    x = self.calc_diff_hours(cur_date, start_date)
                # If x >  prevX, build the values object and append to the values list
                if x > prev_x:

                    # If counter > 0, there were readings from 1-hour bucket and values should be averaged
                    if counter > 0:
                        total = total + prev_reading[2]
                        counter += 1

                        avg = total / counter
                        last_val_date = prev_reading[1]

                        values = self.build_values(prev_x, avg, last_val_date)

                        # Reset Average in a 1-hour bucket params
                        total = 0
                        counter = 0
                    # Otherwise, simply build values from previous reading
                    else:
                        y = prev_reading[2]
                        values = self.build_values(prev_x, y, prev_reading[1])

                    # Append the current values to valuelist
                    value_list.append(values)

                    prev_reading = reading
                    prev_x = x

                else:
                    # if reading falls in same bucket, accumulate the reading value to average later
                    if x == prev_x:
                        total = total + prev_reading[2]
                        counter += 1
                        prev_x = x
                        prev_reading = reading
                    # Skip the reading if the readings are not in order. This is unlikely to occur.
                    else:
                        current_app.logger.info("Skipped Value for %s, %s", str(measurement_type), str(cur_date))

            except ValueError as err:
                raise ValueError('Error in preparing values list', measurement_type, reading)

        return value_list

    @staticmethod
    def build_values(x, y, reading_date):
        values = {
            "x": x,
            "y": round(y, 2),
            #"date": str(reading_date)
            "date": reading_date

        }
        return values

    def update_value_list(self,value_list,annotations):
        """Update value list to add annotations and convert date to string
        Parameters:
          - value_list  : list of all reading values
          - annotations : list of associated annotations
        Returns: updated value list after adding any eligible annotation and converting
        the date to string format. Annotation is added to the closest reading available after
        the annotation timestamp. So there can be multiple annotations associated with one reading."""
        index=0
        updated_value_list = []

        value_index=0
        annotation_index_list = []

        if annotations:
            cur_annotation = annotations[index]
            annotation_date = cur_annotation[2]

            for value in value_list:

                if(value["date"] > annotation_date) and index < len(annotations):
                    annotation_list = []
                    annotation_index_list.append(value_index)

                    while(value["date"] > annotation_date)  :
                        annotation_list.append(cur_annotation)
                        index= index +1

                        if(index < len(annotations)):
                            cur_annotation = annotations[index]
                            annotation_date = cur_annotation[2]
                        else:
                            break

                    updated_value = self.update_values(value,annotation_list)
                    updated_value_list.append(updated_value)
                else:
                     updated_value = self.update_values(value,None)
                     updated_value_list.append(updated_value)

                value_index = value_index + 1
        else:
            for value in value_list:
                updated_value = self.update_values(value,None)
                updated_value_list.append(updated_value)

        obj = {
            "value_list" : updated_value_list,
            "annotation_index_list" : annotation_index_list
        }

        return obj

    @staticmethod
    def update_values(value,annotations):
        """Update the values object
        Parameters:
          - value: value to be updated
          - annotations: annotations associated with the values
        Returns:
        the updated values object. Values are modified to include any associated
        annotations and date in string format"""
        if annotations is None:
            values = {
                "x": value["x"],
                "y": value["y"],
                "date": str(value["date"])
            }
        else:
            annotation_list = []
            for annotation in annotations:
                obj = {
                    "id" : annotation[1],
                    "date" : str(annotation[2])
                }
                annotation_list.append(obj)

            values = {
                "x": value["x"],
                "y": value["y"],
                "date": str(value["date"]),
                "annotations" : annotation_list
            }

        return values

    @staticmethod
    def get_system_name(conn, system_id):
        s = SystemsDAO(conn)
        return s.get_system_name(system_id)

    @staticmethod
    def calc_diff_hours(cur_date, start_date):
        if cur_date < start_date:
            raise ValueError('Current date is lesser than previous date', cur_date, start_date)
        else:
            diff = cur_date - start_date
            return diff.days * 24 + diff.seconds / 3600

    def get_all_measurement_names(self):
        meas = self.mea.get_all_measurement_names()
        if 'error' in meas:
            return json.dumps(meas)
        mlist = []
        for m in meas:
            mlist.append(m)
        mlist.append('time')
        return json.dumps({"types": mlist})

    def generate_data(self, min_range, max_range, systems, meas):
        """generate test data
        Parameters:
          - conn: connection to db
          - min_range: minimum value u want to insert
          - max_range: maximum value u want to insert
          - systems: list of systems
          - meas: list of measurements"""
        for s in systems:
            for i in range(1, 6, 1):
                for j in range(0, 24, 1):
                    for m in meas:
                        d = datetime.datetime(2015, 1, i, j, 0, 0)
                        table_name = self.get_measurement_table_name(m, s)
                        time = d.strftime('%Y-%m-%d %H:%M:%S')
                        val = random.uniform(min_range, max_range)
                        self.mea.put_system_measurement(table_name, time, val)

    def get_all_measurement_info(self):
        meas = self.mea.get_all_measurement_info()
        if 'error' in meas:
            return json.dumps(meas)
        measurement_names = {}
        for m in meas:
            measurement_names[m[1]] = {}
            measurement_names[m[1]]["id"] = (m[0])
            measurement_names[m[1]]["unit"] = (m[2])
            measurement_names[m[1]]["min"] = to_float(m[3])
            measurement_names[m[1]]["max"] = to_float(m[4])
        return json.dumps({"measurement_info": measurement_names})

    def get_all_data_for_system_and_measurement(self, system, measurement, page):
        response = self.mea.get_all_measurements(system, measurement, page)
        if 'error' in response:
            return json.dumps(response)
        return json.dumps(response)

    def get_measurement_by_created_at(self, system, measurement, created_at):
        response = self.mea.get_measurement(system, measurement, created_at)
        if 'error' in response:
            return json.dumps(response)
        return json.dumps(response)

    def edit_measurement(self, system_uid, measurement, data):
        response = self.mea.update_existing_measurement(system_uid, measurement, data)
        if 'error' in response:
            return json.dumps(response)
        return json.dumps(response)
