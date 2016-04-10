# DAO for system annotation table

class SystemAnnotationDAO:
    def __init__(self, conn):
        self.conn = conn

    # add_annotation : adds an annotation to a system
    def add_annotation(self, system_id, annotation):
        old_annotation = self.view_annotation(system_id)
        if len(old_annotation) != 0:
            return "Annotation exists"
        cursor = self.conn.cursor()
        query = ("insert into system_annotations (system_id,water,pH ,"
                 "harvest,plant,fish,bacteria,cleanTank,reproduction,timestamp)    "
                 "values(%s,%s,%s, %s,%s,%s,%s,%s,%s,%s);")
        data = (annotation.get('system_id'), annotation.get('water'), annotation.get('pH')
                , annotation.get('harvest'), annotation.get('plant'), annotation.get('fish'),
                annotation.get('bacteria'), annotation.get('cleanTank'), annotation.get('reproduction'),
                annotation.get('timestamp'))
        try:
            cursor.execute(query, data)
            self.conn.commit()
        except:
            self.conn.rollback()
            cursor.close()
            return "Insert error"
        finally:
            cursor.close()
        return "Annotation inserted"

    # view_annotation : gets an nnotation from a system
    def view_annotation(self, system_id):
        cursor = self.conn.cursor()
        query = ('select * from system_annotations where system_id = %s ')
        try:
            cursor.execute(query, (system_id,))
            system = cursor.fetchall()
        finally:
            cursor.close()
        return system