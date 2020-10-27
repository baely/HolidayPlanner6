import os
import psycopg2

from datetime import datetime
from decimal import Decimal
from psycopg2 import sql
from typing import Any, List, Optional, Tuple
from typing_inspect import get_args, get_origin

from extension import get_all_subclasses


class DB:
    host = os.environ["db_host"]
    port = int(os.environ["db_port"])
    user = os.environ["db_user"]
    password = os.environ["db_pass"]
    database = os.environ["db_database"]

    datatype_mappings = {
        datetime: "timestamp with time zone",
        Decimal: "decimal(10,7)",
        str: "text",
        float: "float",
        int: "int",
        (float, float): "point"
    }

    def __init__(self):
        self.conn = None

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn: psycopg2 = None

    def connect(self):
        self.conn = psycopg2.connect(
            host=DB.host,
            port=DB.port,
            database=DB.database,
            user=DB.user,
            password=DB.password)

    @staticmethod
    def new_cursor() -> Tuple[Any, 'DB']:
        db = DB()
        db.connect()
        return db.conn.cursor(), db

    @staticmethod
    def setup():
        sql_data = {name: [("id", "serial")] for name, fields in DBObject.get_all_types()}

        for name, fields in DBObject.get_all_types():
            for field_name, field_type in fields:
                if isinstance(field_type, type):
                    if issubclass(field_type, DBObject):
                        sql_data[name].append((f"{field_name}_id", DB.datatype_mappings[int]))
                    else:
                        sql_data[name].append((field_name, DB.datatype_mappings[field_type]))
                elif get_origin(field_type):
                    if get_origin(field_type) is tuple and get_args(field_type) == (float, float):
                        sql_data[name].append((field_name, DB.datatype_mappings[(float, float)]))
                    else:
                        try:
                            child_type = None
                            if get_origin(field_type) is list \
                                    and issubclass(child_type := get_args(field_type)[0], DBObject):
                                sql_data[child_type.__name__].append((f"{name}_id", DB.datatype_mappings[int]))
                        except TypeError as e:
                            print(e, get_args(field_type))

        query = "\n".join([
            f"DROP TABLE IF EXISTS {name}; "
            f"CREATE TABLE {name} ({', '.join([f'{field_name} {field_type}' for field_name, field_type in items])});"
            for name, items in sql_data.items()
        ])

        cursor, db = DB.new_cursor()
        cursor.execute(query)
        db.conn.commit()
        db.close()


class DBObject:
    @staticmethod
    def get_all_types() -> List[Tuple[str, List[Tuple[str, type]]]]:
        return [(cls.__name__, DBObject.get_types(cls)) for cls in get_all_subclasses(DBObject)]

    @staticmethod
    def get_id(obj, key: str = None):
        if isinstance(obj, DBObject):
            return f"{key}_id", obj._id if key else obj._id
        else:
            return key, obj if key else obj

    @classmethod
    def get_by_id(cls, object_id: int):
        if object_id == 0:
            return None

        cursor, db = DB.new_cursor()
        cursor.execute(
            sql.SQL("SELECT * FROM {} WHERE id = (%s) LIMIT 1;").format(sql.Identifier(cls.__name__.lower())),
            [object_id])
        obj = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))
        db.conn.commit()
        db.close()

        return cls(object_id=object_id, save=True, **obj) if obj else None

    @staticmethod
    def get_types(cls: type) -> List[Tuple[str, type]]:
        return [item for item in cls.__annotations__.items()] if hasattr(cls, "__annotations__") else []

    def __init__(self, *args, object_id: Optional[int] = None, save: Optional[bool] = True, **kwargs):
        self._id = object_id

        for attr, t in self.__annotations__.items():
            if isinstance(t, type):
                if issubclass(t, DBObject) and not (attr in kwargs and isinstance(kwargs.get(attr), DBObject)):
                    setattr(self, attr, t.get_by_id(kwargs.get(f"{attr}_id", 0)))
                else:
                    setattr(self, attr, kwargs.get(attr))
            elif origin_type := get_origin(t):
                if origin_type is list:
                    print("ok lets a do some list?")

        if save:
            self.save()

    def save(self):
        if self._id:
            items = [DBObject.get_id(value, key) for key, value in self.__dict__.items() if not key.startswith("_") and key != "id"]
            conditions = ", ".join(["{}=%s".format(item[0]) for item in items])
            values = [item[1] for item in items] + [self._id]
            cursor, db = DB.new_cursor()
            cursor.execute("UPDATE {} SET {} WHERE id=%s;".format(type(self).__name__.lower(), conditions), values)
            db.conn.commit()
            db.close()
            pass
        else:
            cursor, db = DB.new_cursor()
            items = [DBObject.get_id(value, key) for key, value in self.__dict__.items() if
                     not key.startswith("_") and key != "id"]
            fields = ", ".join([item[0] for item in items])
            value_placeholder = ", ".join(["%s" for item in items])
            values = [item[1] for item in items]
            cursor.execute("INSERT INTO {} ({}) VALUES ({}) RETURNING id;".format(type(self).__name__.lower(), fields, value_placeholder), values)
            id = cursor.fetchone()
            db.conn.commit()
            db.close()
            self._id = id[0]
