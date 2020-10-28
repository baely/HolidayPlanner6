import os
import psycopg2

from datetime import datetime
from decimal import Decimal
from psycopg2 import sql
from typing import Any, Dict, List, Optional, Tuple
from typing_inspect import get_args, get_origin

from extension import get_all_subclasses


class DB:
    host = os.environ["db_host"]
    port = int(os.environ["db_port"])
    user = os.environ["db_user"]
    password = os.environ["db_pass"]
    database = os.environ["db_database"]

    datatype_mappings: Dict[type, str] = {
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
                    try:
                        child_type = None
                        if get_origin(field_type) is list \
                                and issubclass(child_type := get_args(field_type)[0], DBObject):
                            sql_data[child_type.__name__].append((f"{name}_id", DB.datatype_mappings[int]))
                    except TypeError:
                        pass

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

    @classmethod
    def class_hierarchy(cls):
        return [b for base in cls.__bases__ if issubclass(base, DBObject) for b in base.class_hierarchy()] + [cls]

    @classmethod
    def all_annotations(cls) -> Dict[str, type]:
        return {annotation: a_type for base_class in cls.class_hierarchy() if hasattr(base_class, "__annotations__")
                for annotation, a_type in base_class.__annotations__.items()}

    def __init__(self, *args, object_id: Optional[int] = None, save: Optional[bool] = True, **kwargs):
        self._id = object_id
        self._in_db = kwargs.get("in_db", False)

        if DBObject not in type(self).__bases__:
            self._parent = [t for t in type(self).__bases__ if issubclass(t, DBObject)][0](
                *args, self._id, save, **kwargs)
            self._id = self._parent._id

        if self._id:
            self.id = self._id

        for attr, t in self.__annotations__.items():
            if isinstance(t, type):
                if issubclass(t, DBObject) and not (attr in kwargs and isinstance(kwargs.get(attr), DBObject)):
                    setattr(self, attr, t.get_by_id(kwargs.get(f"{attr}_id", 0)))
                else:
                    setattr(self, attr, kwargs.get(attr))
            elif origin_type := get_origin(t):
                if origin_type is list:
                    # print("ok lets a do some list?")
                    pass

        if save:
            self.save()

    def save(self):
        if self._in_db:
            items = [DBObject.get_id(value, key)
                     for key, value in self.__dict__.items() if not key.startswith("_") and key != "id_row"]
            conditions = ", ".join(["{}=%s".format(item[0]) for item in items])
            values = [item[1] for item in items] + [self._id]
            cursor, db = DB.new_cursor()
            cursor.execute("UPDATE {} SET {} WHERE id_row=%s;".format(type(self).__name__.lower(), conditions), values)
            db.conn.commit()
            db.close()
            pass
        else:
            cursor, db = DB.new_cursor()
            items = [DBObject.get_id(value, key) for key, value in self.__dict__.items() if
                     not key.startswith("_") and key != "id_row"]
            fields = ", ".join([item[0] for item in items])
            value_placeholder = ", ".join(["%s" for _ in items])
            values = [item[1] for item in items]
            cursor.execute("INSERT INTO {} ({}) VALUES ({}) RETURNING id;"
                           .format(type(self).__name__.lower(), fields, value_placeholder), values)
            id_row = cursor.fetchone()
            db.conn.commit()
            db.close()
            self._id = self._id or id_row[0]
            self._in_db = True
