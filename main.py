from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    String,
    Text,
    DateTime,
    Date,
    Time,
    Float,
    Numeric,
    SmallInteger,
    Integer,          # 👈 NEW
)
from sqlalchemy.orm import sessionmaker

from sqlalchemy.dialects.mysql import (
    ENUM as MySQLEnum,
    DATETIME as MySQLDateTime,
    TIMESTAMP as MySQLTimestamp,
    DATE as MySQLDate,
    TIME as MySQLTime,
    DOUBLE as MySQLDouble,
    FLOAT as MySQLFloat,
    DECIMAL as MySQLDecimal,
    TINYINT as MySQLTinyInt,
    YEAR as MySQLYear,
    MEDIUMINT as MySQLMediumInt,   # 👈 NEW
)







# ------------- CONFIG: EDIT THESE ------------- #

# MySQL connection information
MYSQL_HOST = "127.0.0.1"      # or your server IP
MYSQL_PORT = 3306             # default
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "property-listing"
MYSQL_CHARSET = "utf8mb4"     # Recommended for Unicode (Khmer ok)

# Build full MySQL SQLAlchemy URL
MYSQL_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:"
    f"{MYSQL_PORT}/{MYSQL_DATABASE}?charset={MYSQL_CHARSET}"
)

# PostgreSQL connection information
PG_HOST = "127.0.0.1"
PG_PORT = 5432
PG_USER = "postgres"
PG_PASSWORD = "ezpass2023"
PG_DATABASE = "property-listing"

# Build full PostgreSQL SQLAlchemy URL
POSTGRES_URL = (
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:"
    f"{PG_PORT}/{PG_DATABASE}"
)

# ------------- MAIN LOGIC ------------- #

def copy_schema(mysql_engine, pg_engine):
    """
    Reflect schema from MySQL and create the same tables in PostgreSQL.
    - ENUM          -> VARCHAR
    - DATETIME/TS   -> DateTime (Postgres TIMESTAMP)
    - DATE          -> Date
    - TIME          -> Time
    - DOUBLE/FLOAT  -> Float
    - DECIMAL       -> Numeric
    - TINYINT       -> SmallInteger
    - YEAR          -> SmallInteger
    - Strip MySQL collations (utf8mb3_general_ci, etc.)
    - No indexes / foreign keys on this first pass
    """
    mysql_meta = MetaData()
    mysql_meta.reflect(bind=mysql_engine)

    pg_meta = MetaData()

    for table_name, table in mysql_meta.tables.items():
        print(f"Creating table schema for: {table_name}")

        new_columns = []

        for col in table.columns:
            col_type = col.type

            # 1️⃣ ENUM -> VARCHAR
            if isinstance(col_type, MySQLEnum):
                max_len = max((len(v) for v in col_type.enums), default=255)
                print(f"  - Column {col.name}: MySQL ENUM -> VARCHAR({max_len})")
                col_type = String(length=max_len)

            # 2️⃣ Date/time types
            elif isinstance(col_type, (MySQLDateTime, MySQLTimestamp)):
                print(f"  - Column {col.name}: MySQL {col_type.__class__.__name__} -> DateTime")
                col_type = DateTime()
            elif isinstance(col_type, MySQLDate):
                print(f"  - Column {col.name}: MySQL DATE -> Date")
                col_type = Date()
            elif isinstance(col_type, MySQLTime):
                print(f"  - Column {col.name}: MySQL TIME -> Time")
                col_type = Time()
            elif isinstance(col_type, MySQLYear):
                print(f"  - Column {col.name}: MySQL YEAR -> SmallInteger")
                col_type = SmallInteger()

            # 3️⃣ Numeric types
            elif isinstance(col_type, (MySQLDouble, MySQLFloat)):
                print(f"  - Column {col.name}: MySQL {col_type.__class__.__name__} -> Float")
                col_type = Float()

            elif isinstance(col_type, MySQLDecimal):
                precision = getattr(col_type, "precision", None)
                scale = getattr(col_type, "scale", None)
                if precision is not None and scale is not None:
                    print(f"  - Column {col.name}: MySQL DECIMAL({precision},{scale}) -> Numeric({precision},{scale})")
                    col_type = Numeric(precision=precision, scale=scale)
                else:
                    print(f"  - Column {col.name}: MySQL DECIMAL -> Numeric")
                    col_type = Numeric()

            elif isinstance(col_type, MySQLTinyInt):
                print(f"  - Column {col.name}: MySQL TINYINT -> SmallInteger")
                col_type = SmallInteger()

            elif isinstance(col_type, MySQLMediumInt):   # 👈 NEW
                print(f"  - Column {col.name}: MySQL MEDIUMINT -> Integer")
                col_type = Integer()

            # 4️⃣ Strip MySQL collation on string-like types
            if getattr(col_type, "collation", None):
                length = getattr(col_type, "length", None)

                if length:
                    print(f"  - Column {col.name}: strip collation -> VARCHAR({length})")
                    col_type = String(length=length)
                else:
                    print(f"  - Column {col.name}: strip collation -> TEXT")
                    col_type = Text()

            # 5️⃣ Rebuild simplified column (safe for Postgres)
            new_col = Column(
                col.name,
                col_type,
                primary_key=col.primary_key,
                autoincrement=col.autoincrement,
                nullable=col.nullable,
            )
            new_columns.append(new_col)

        # Create new PG table
        Table(
            table_name,
            pg_meta,
            *new_columns,
        )

    print("Creating tables in PostgreSQL...")
    pg_meta.create_all(bind=pg_engine)
    print("Schema copy completed (no data copied).")





# Optional: keep this if you ever want to copy data later
def copy_data(mysql_engine, pg_engine):
    """
    Copy all data from MySQL to PostgreSQL table-by-table.
    (NOT USED NOW)
    """
    mysql_meta = MetaData(bind=mysql_engine)
    mysql_meta.reflect()

    SessionMySQL = sessionmaker(bind=mysql_engine)
    SessionPostgres = sessionmaker(bind=pg_engine)

    session_mysql = SessionMySQL()
    session_pg = SessionPostgres()

    try:
        for table_name, table_mysql in mysql_meta.tables.items():
            print(f"Copying data for table: {table_name}")

            table_pg = Table(table_name, MetaData(), autoload_with=pg_engine)

            total_rows = session_mysql.execute(table_mysql.count()).scalar()
            print(f"  Total rows: {total_rows}")

            offset = 0
            while True:
                rows = session_mysql.execute(
                    table_mysql.select().offset(offset).limit(100)
                ).fetchall()

                if not rows:
                    break

                rows_to_insert = [dict(row._mapping) for row in rows]

                session_pg.execute(table_pg.insert(), rows_to_insert)
                session_pg.commit()

                offset += len(rows)
                print(f"  Copied {offset}/{total_rows} rows...", end="\r")

            print(f"\nFinished table: {table_name}")
    finally:
        session_mysql.close()
        session_pg.close()


def main():
    mysql_engine = create_engine(MYSQL_URL)
    pg_engine = create_engine(POSTGRES_URL)

    copy_schema(mysql_engine, pg_engine)
    print("All done!")



if __name__ == "__main__":
    main()
