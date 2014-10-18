"""
Constants specific to the SQL storage portion of the ORM.
"""

from collections import namedtuple
import re

# Valid query types (a set is used for speedy lookups). These are (currently)
# considered SQL-specific; other storage systems may choose to use different
# lookup types.
QUERY_TERMS = set([
  'exact', 'iexact', 'contains', 'icontains', 'gt', 'gte', 'lt', 'lte', 'in',
  'startswith', 'istartswith', 'endswith', 'iendswith', 'range', 'year',
  'month', 'day', 'weekDay', 'hour', 'minute', 'second', 'isnull', 'search',
  'regex', 'iregex',
])

# Size of each "chunk" for getIterator calls.
# Larger values are slightly faster at the expense of more storage space.
GET_ITERATOR_CHUNK_SIZE = 100

# Namedtuples for sql.* internal use.

# Join lists (indexes into the tuples that are values in the aliasMap
# dictionary in the Query class).
JoinInfo = namedtuple('JoinInfo',
           'tableName rhsAlias joinType lhsAlias '
           'joinCols nullable joinField')

# Pairs of column clauses to select, and (possibly None) field for the clause.
SelectInfo = namedtuple('SelectInfo', 'col field')

# How many results to expect from a cursor.execute call
MULTI = 'multi'
SINGLE = 'single'
CURSOR = 'cursor'
NO_RESULTS = 'no results'

ORDER_PATTERN = re.compile(r'\?|[-+]?[.\w]+$')
ORDER_DIR = {
  'ASC': ('ASC', 'DESC'),
  'DESC': ('DESC', 'ASC'),
}
