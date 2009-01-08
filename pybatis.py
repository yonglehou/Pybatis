import psycopg2
import psycopg2.extras
from psycopg2.extensions import (
    ISOLATION_LEVEL_AUTOCOMMIT,
    ISOLATION_LEVEL_READ_COMMITTED,
    ISOLATION_LEVEL_SERIALIZABLE,
    STATUS_BEGIN,
    STATUS_READY)


from jinja2 import Environment, FileSystemLoader
from jinja2.runtime import Undefined

import logging

########### custom Jinja tests needed by pybatis

# detect dict val not being present
def is_present(str):
    return (not isinstance(str, Undefined)) and str != None

# detect dict val not being present or being present but empty string
def is_not_empty(str):
    return (not isinstance(str, Undefined)) and str != None and str != ''

########## custom exceptions

class NullConnectionException(Exception):
    pass

class ConnectionClosedException(Exception):
    pass

class CursorAlreadyExistsException(Exception):
    pass

class CursorAlreadyOpenException(Exception):
    pass

########## utility functions

def row_to_dict (row, keys=None):
    if row == None:
        return None
    if keys == None:
        keys = row.keys()
    dict = {}
    for key in keys:
        dict[key] = row[key]
    return dict

def rows_to_dicts (rows, keys=None):
    if rows == None:
        return None
    if len(rows) < 1:
        return None
    if keys == None:
        keys = row[0].keys()
    list = ()
    for row in rows:
        list.push(row_to_dict(row, keys))
    return list

########## sql map

class SQLMap(object):
    def __init__(self, conn, template_path, default_isolation_level=ISOLATION_LEVEL_READ_COMMITTED):
        self.conn = conn
        self.jinja2env = Environment(trim_blocks = True, loader = FileSystemLoader(template_path))
        self.jinja2env.tests['present'] = is_present
        self.jinja2env.tests['not_empty'] = is_not_empty
        self.default_isolation_level = default_isolation_level
        self.curs = None

    def begin(self, isolation_level=None):
        conn = self.conn
        if conn == None:
            raise NullConnectionExcepton

        if conn.closed == True:
            raise ConnectionClosedException

        if self.curs != None:
            raise CursorAlreadyExistsException

        if isolation_level == None:
            self.isolation_level = self.default_isolation_level
        else:
            self.isolation_level = isolation_level
        self.curs = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        conn.set_isolation_level(self.default_isolation_level)


    def commit(self, isolation_level=None):
        self.conn.commit()


    def rollback(self, isolation_level=None):
        self.conn.rollback()

    def end(self):
        self.curs.close()
        self.curs = None

    def select(self, template_pathname, map=None):
        curs = self.curs
        template = self.jinja2env.get_template(template_pathname)
        sql = template.render(map)
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        if curs.rowcount < 1:
            return None
        else:
            return rows_2_dicts(curs.fetchall())

    def direct_select(self, sql, map=None):
        curs = self.curs
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        if curs.rowcount < 1:
            return None
        else:
            return rows_2_dicts(curs.fetchall())

    def simple_select(self, template_pathname, map=None):
        list_of_dicts = None
        try:
            self.begin()
            list_of_dicts = self.select(template_pathname, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return list_of_dicts

    def simple_direct_select(self, sql, map=None):
        list_of_dicts = None
        try:
            self.begin()
            list_of_dicts = self.direct_select(sql, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return list_of_dicts

    def select_first_row(self, template_pathname, map=None):
        curs = self.curs
        template = self.jinja2env.get_template(template_pathname)
        sql = template.render(map)
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        if curs.rowcount < 1:
            return None
        else:
            return row_to_dict(curs.fetchone())

    def direct_select_first_row(self, sql, map=None):
        curs = self.curs
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        if curs.rowcount < 1:
            return None
        else:
            return row_to_dict(curs.fetchone())

    def simple_select_first_row(self, template_pathname, map=None):
        first_row_dict = None
        try:
            self.begin()
            first_row_dict = self.select_first_row(template_pathname, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return first_row_dict

    def simple_direct_select_first_row(self, template_pathname, map=None):
        first_row_dict = None
        try:
            self.begin()
            first_row_dict = self.direct_select_first_row(template_pathname, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return first_row_dict

    def select_first_datum(self, template_pathname, map=None):
        curs = self.curs
        template = self.jinja2env.get_template(template_pathname)
        sql = template.render(map)
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        if curs.rowcount < 1:
            return None
        else:
            return curs.fetchone()[0]

    def direct_select_first_datum(self, sql, map=None):
        curs = self.curs
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        if curs.rowcount < 1:
            return None
        else:
            return curs.fetchone()[0]

    def simple_select_first_datum(self, template_pathname, map=None):
        first_datum = None
        try:
            self.begin()
            first_datum = self.select_first_datum(template_pathname, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return first_datum

    def simple_direct_select_first_datum(self, template_pathname, map=None):
        first_datum = None
        try:
            self.begin()
            first_datum = self.direct_select_first_datum(template_pathname, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return first_datum

    def insert(self, template_pathname, map=None):
        curs = self.curs
        template = self.jinja2env.get_template(template_pathname)
        sql = template.render(map)
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        return curs.statusmessage

    def direct_insert(self, sql, map=None):
        curs = self.curs
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        return curs.statusmessage

    def simple_insert(self, template_pathname, map=None):
        status_message = None
        try:
            self.begin()
            status_message = self.insert(template_pathname, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return status_message

    def simple_direct_insert(self, sql, map=None):
        status_message = None
        try:
            self.begin()
            status_message = self.direct_insert(sql, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return status_message


    def update(self, template_pathname, map=None):
        curs = self.curs
        template = self.jinja2env.get_template(template_pathname)
        sql = template.render(map)
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        return curs.statusmessage

    def direct_update(self, sql, map=None):
        curs = self.curs
        curs.execute(sql, map);
        logging.debug('Just executed')
        logging.debug(curs.query)
        return curs.statusmessage

    def simple_update(self, template_pathname, map=None):
        status_message = None
        try:
            self.begin()
            status_message = self.update(template_pathname, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return status_message

    def simple_direct_update(self, sql, map=None):
        status_message = None
        try:
            self.begin()
            status_message = self.direct_update(sql, map)
            self.commit()
        except:
            self.rollback()
            raise
        finally:
            self.end()
        return status_message


