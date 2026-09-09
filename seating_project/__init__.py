try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# Bypass version checks to support XAMPP's MariaDB 10.4
from django.db.backends.base.base import BaseDatabaseWrapper
BaseDatabaseWrapper.check_database_version_supported = lambda self: None

# Disable RETURNING clause for insertions on MariaDB 10.4
from django.db.backends.mysql.features import DatabaseFeatures
DatabaseFeatures.can_return_columns_from_insert = False