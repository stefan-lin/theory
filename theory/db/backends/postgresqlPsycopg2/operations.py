from __future__ import unicode_literals

from theory.conf import settings
from theory.db.backends import BaseDatabaseOperations


class DatabaseOperations(BaseDatabaseOperations):
  def __init__(self, connection):
    super(DatabaseOperations, self).__init__(connection)

  def dateExtractSql(self, lookupType, fieldName):
    # http://www.postgresql.org/docs/current/static/functions-datetime.html#FUNCTIONS-DATETIME-EXTRACT
    if lookupType == 'weekDay':
      # For consistency across backends, we return Sunday=1, Saturday=7.
      return "EXTRACT('dow' FROM %s) + 1" % fieldName
    else:
      return "EXTRACT('%s' FROM %s)" % (lookupType, fieldName)

  def dateIntervalSql(self, sql, connector, timedelta):
    """
    implements the interval functionality for expressions
    format for Postgres:
      (datefield + interval '3 days 200 seconds 5 microseconds')
    """
    modifiers = []
    if timedelta.days:
      modifiers.append('%s days' % timedelta.days)
    if timedelta.seconds:
      modifiers.append('%s seconds' % timedelta.seconds)
    if timedelta.microseconds:
      modifiers.append('%s microseconds' % timedelta.microseconds)
    mods = ' '.join(modifiers)
    conn = ' %s ' % connector
    return '(%s)' % conn.join([sql, 'interval \'%s\'' % mods])

  def dateTruncSql(self, lookupType, fieldName):
    # http://www.postgresql.org/docs/current/static/functions-datetime.html#FUNCTIONS-DATETIME-TRUNC
    return "DATE_TRUNC('%s', %s)" % (lookupType, fieldName)

  def datetimeExtractSql(self, lookupType, fieldName, tzname):
    if settings.USE_TZ:
      fieldName = "%s AT TIME ZONE %%s" % fieldName
      params = [tzname]
    else:
      params = []
    # http://www.postgresql.org/docs/current/static/functions-datetime.html#FUNCTIONS-DATETIME-EXTRACT
    if lookupType == 'weekDay':
      # For consistency across backends, we return Sunday=1, Saturday=7.
      sql = "EXTRACT('dow' FROM %s) + 1" % fieldName
    else:
      sql = "EXTRACT('%s' FROM %s)" % (lookupType, fieldName)
    return sql, params

  def datetimeTruncSql(self, lookupType, fieldName, tzname):
    if settings.USE_TZ:
      fieldName = "%s AT TIME ZONE %%s" % fieldName
      params = [tzname]
    else:
      params = []
    # http://www.postgresql.org/docs/current/static/functions-datetime.html#FUNCTIONS-DATETIME-TRUNC
    sql = "DATE_TRUNC('%s', %s)" % (lookupType, fieldName)
    return sql, params

  def deferrableSql(self):
    return " DEFERRABLE INITIALLY DEFERRED"

  def lookupCast(self, lookupType):
    lookup = '%s'

    # Cast text lookups to text to allow things like filter(x__contains=4)
    if lookupType in ('iexact', 'contains', 'icontains', 'startswith',
              'istartswith', 'endswith', 'iendswith', 'regex', 'iregex'):
      lookup = "%s::text"

    # Use UPPER(x) for case-insensitive lookups; it's faster.
    if lookupType in ('iexact', 'icontains', 'istartswith', 'iendswith'):
      lookup = 'UPPER(%s)' % lookup

    return lookup

  def fieldCastSql(self, dbType, internalType):
    if internalType == "GenericIPAddressField" or internalType == "IPAddressField":
      return 'HOST(%s)'
    return '%s'

  def lastInsertId(self, cursor, tableName, pkName):
    # Use pg_get_serial_sequence to get the underlying sequence name
    # from the table name and column name (available since PostgreSQL 8)
    cursor.execute("SELECT CURRVAL(pg_get_serial_sequence('%s','%s'))" % (
      self.quoteName(tableName), pkName))
    return cursor.fetchone()[0]

  def noLimitValue(self):
    return None

  def prepareSqlScript(self, sql, _allowFallback=False):
    return [sql]

  def quoteName(self, name):
    if name.startswith('"') and name.endswith('"'):
      return name  # Quoting once is enough.
    return '"%s"' % name

  def setTimeZoneSql(self):
    return "SET TIME ZONE %s"

  def sqlFlush(self, style, tables, sequences, allowCascade=False):
    if tables:
      # Perform a single SQL 'TRUNCATE x, y, z...;' statement.  It allows
      # us to truncate tables referenced by a foreign key in any other
      # table.
      tablesSql = ', '.join(
        style.SQL_FIELD(self.quoteName(table)) for table in tables)
      if allowCascade:
        sql = ['%s %s %s;' % (
          style.SQL_KEYWORD('TRUNCATE'),
          tablesSql,
          style.SQL_KEYWORD('CASCADE'),
        )]
      else:
        sql = ['%s %s;' % (
          style.SQL_KEYWORD('TRUNCATE'),
          tablesSql,
        )]
      sql.extend(self.sequenceResetByNameSql(style, sequences))
      return sql
    else:
      return []

  def sequenceResetByNameSql(self, style, sequences):
    # 'ALTER SEQUENCE sequenceName RESTART WITH 1;'... style SQL statements
    # to reset sequence indices
    sql = []
    for sequenceInfo in sequences:
      tableName = sequenceInfo['table']
      columnName = sequenceInfo['column']
      if not (columnName and len(columnName) > 0):
        # This will be the case if it's an m2m using an autogenerated
        # intermediate table (see BaseDatabaseIntrospection.sequenceList)
        columnName = 'id'
      sql.append("%s setval(pg_get_serial_sequence('%s','%s'), 1, false);" %
        (style.SQL_KEYWORD('SELECT'),
        style.SQL_TABLE(self.quoteName(tableName)),
        style.SQL_FIELD(columnName))
      )
    return sql

  def tablespaceSql(self, tablespace, inline=False):
    if inline:
      return "USING INDEX TABLESPACE %s" % self.quoteName(tablespace)
    else:
      return "TABLESPACE %s" % self.quoteName(tablespace)

  def sequenceResetSql(self, style, modalList):
    from theory.db import model
    output = []
    qn = self.quoteName
    for modal in modalList:
      # Use `coalesce` to set the sequence for each modal to the max pk value if there are records,
      # or 1 if there are none. Set the `isCalled` property (the third argument to `setval`) to true
      # if there are records (as the max pk value is already in use), otherwise set it to false.
      # Use pg_get_serial_sequence to get the underlying sequence name from the table name
      # and column name (available since PostgreSQL 8)

      for f in modal._meta.localFields:
        if isinstance(f, model.AutoField):
          output.append("%s setval(pg_get_serial_sequence('%s','%s'), coalesce(max(%s), 1), max(%s) %s null) %s %s;" %
            (style.SQL_KEYWORD('SELECT'),
            style.SQL_TABLE(qn(modal._meta.dbTable)),
            style.SQL_FIELD(f.column),
            style.SQL_FIELD(qn(f.column)),
            style.SQL_FIELD(qn(f.column)),
            style.SQL_KEYWORD('IS NOT'),
            style.SQL_KEYWORD('FROM'),
            style.SQL_TABLE(qn(modal._meta.dbTable))))
          break  # Only one AutoField is allowed per modal, so don't bother continuing.
      for f in modal._meta.manyToMany:
        if not f.rel.through:
          output.append("%s setval(pg_get_serial_sequence('%s','%s'), coalesce(max(%s), 1), max(%s) %s null) %s %s;" %
            (style.SQL_KEYWORD('SELECT'),
            style.SQL_TABLE(qn(f.m2mDbTable())),
            style.SQL_FIELD('id'),
            style.SQL_FIELD(qn('id')),
            style.SQL_FIELD(qn('id')),
            style.SQL_KEYWORD('IS NOT'),
            style.SQL_KEYWORD('FROM'),
            style.SQL_TABLE(qn(f.m2mDbTable()))))
    return output

  def prepForIexactQuery(self, x):
    return x

  def maxNameLength(self):
    """
    Returns the maximum length of an identifier.

    Note that the maximum length of an identifier is 63 by default, but can
    be changed by recompiling PostgreSQL after editing the NAMEDATALEN
    macro in src/include/pgConfigManual.h .

    This implementation simply returns 63, but can easily be overridden by a
    custom database backend that inherits most of its behavior from this one.
    """

    return 63

  def distinctSql(self, fields):
    if fields:
      return 'DISTINCT ON (%s)' % ', '.join(fields)
    else:
      return 'DISTINCT'

  def lastExecutedQuery(self, cursor, sql, params):
    # http://initd.org/psycopg/docs/cursor.html#cursor.query
    # The query attribute is a Psycopg extension to the DB API 2.0.
    if cursor.query is not None:
      return cursor.query.decode('utf-8')
    return None

  def returnInsertId(self):
    return "RETURNING %s", ()

  def bulkInsertSql(self, fields, numValues):
    itemsSql = "(%s)" % ", ".join(["%s"] * len(fields))
    return "VALUES " + ", ".join([itemsSql] * numValues)