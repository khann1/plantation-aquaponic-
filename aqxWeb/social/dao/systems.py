import json
import time

from py2neo import Node, Relationship


def timestamp():
    """copied from models, to break cyclic dependency"""
    return int(round(time.time() * 1000))


class SystemDAO:
    # constructor to get connection
    def __init__(self, graph):
        self.graph = graph

    def create_system(self, jsonObject):
        try:
            sql_id = jsonObject.get('user')
            sql_id = int(sql_id)
            system = jsonObject.get('system')
            system_id = system.get('system_id')
            system_id = int(system_id)
            is_existing_user = self.graph.find_one("User", "sql_id", sql_id)
            is_existing_system = self.graph.find_one("System", "system_id", system_id)
            # Create System node in the Neo4J database, only when there is no system with the provided system_id
            # Also the user node should exists in the Neo4J database
            if is_existing_user is not None and is_existing_system is None:
                system_uid = system.get('system_uid')
                name = system.get('name')
                description = system.get('description')
                location_lat = system.get('location_lat')
                location_lng = system.get('location_lng')
                status = system.get('status')
                systemNode = Node("System", system_id=system_id, system_uid=system_uid, name=name,
                                  description=description, location_lat=location_lat,
                                  location_lng=location_lng, status=status,
                                  creation_time=timestamp(), modified_time=timestamp())
                self.graph.create(systemNode)
                relationship = Relationship(is_existing_user, "SYS_ADMIN", systemNode)
                self.graph.create(relationship)
                return {'success': "System Node Successfully Created in Neo4J Database"}
            else:
                return {'error': 'User Does Not Exists / System Already Exists'}
        except Exception as ex:
            return {'error': 'Exception Occurred At create_system: ' + str(ex.message)}

    ###############################################################################
    # function : update_system_with_system_uid
    # purpose : function used to update System node in the Neo4J Database
    # params : self, system JSON Object
    # returns : None
    # Exceptions : General Exception
    def update_system_with_system_uid(self, jsonObject):
        try:
            system = jsonObject.get('system')
            system_uid = system.get('system_uid')
            is_existing_system = self.graph.find_one("System", "system_uid", system_uid)
            # Create System node in the Neo4J database, only when there is no system with the provided system_id
            if is_existing_system is not None:
                name = system.get('name')
                description = system.get('description')
                status = system.get('status')
                update_system_query = """
                MATCH(s:System)
                WHERE s.system_uid = {system_uid}
                SET s.name = {name}, s.description = {description},
                s.status = {status}, s.modified_time = {modified_time}
                """
                try:
                    # py2neo 2 (current production)
                    self.graph.cypher.execute(update_system_query, system_uid=system_uid, name=name,
                                              description=description, status=status, modified_time=timestamp())
                except:
                    # py2neo 3 (development system)
                    self.graph.run(update_system_query, system_uid=system_uid, name=name,
                                   description=description, status=status, modified_time=timestamp())
                result = json.dumps({'success': "System Node Successfully Updated in Neo4J Database"})
                return result
            else:
                error_msg = json.dumps({'error': 'System Does Not Exists To Update'})
                return error_msg
        except Exception as ex:
            error_msg = json.dumps({'error': 'Exception Occurred At update_system_with_system_uid: ' + str(ex.message)})
            return error_msg

    ###############################################################################
    # function : delete_system_by_system_id
    # purpose : function used to delete the system from Neo4J Database based on system_id
    # params : self, system_id
    # returns : None
    # Exceptions : General Exception
    def delete_system_by_system_id(self, system_id):
        try:
            delete_system_query = """
            MATCH(s:System)
            WHERE s.system_id = {system_id}
            DETACH DELETE s
            """
            try:
                self.graph.cypher.execute(delete_system_query, system_id=system_id)
            except:
                self.graph.run(delete_system_query, system_id=system_id)
            result = json.dumps({'success': "System Node Successfully Deleted in Neo4J Database"})
            return result
        except Exception as ex:
            error_msg = json.dumps({'error': 'Exception Occurred At delete_system_by_system_id: ' + str(ex.message)})
            return error_msg

    ###############################################################################
    # function : get_system_for_user
    # purpose : function to return the systems from Neo4J database where the user is related to
    # params : self, sql_id
    # returns : None
    # Exceptions : Exception
    def get_system_for_user(self, sql_id):
        try:
            query = """
            MATCH (u:User)-[rel]-(s:System)
            WHERE u.sql_id = {sql_id} and
            NOT (type(rel) = "SYS_PENDING_PARTICIPANT")
            RETURN s
            ORDER BY s.name
            """
            try:
                return self.graph.cypher.execute(query, sql_id=sql_id)
            except:
                return self.graph.run(query, sql_id=sql_id)
        except Exception as ex:
            error_msg = json.dumps({'error': 'Exception Occurred At get_system_for_user: ' + str(ex.message)})
            return error_msg
