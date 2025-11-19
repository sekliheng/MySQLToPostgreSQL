
sqlalchemy
pymysql
psycopg2-binary
# MySQL → PostgreSQL Schema Migrator

This project is a small Python tool that **copies table schemas from a MySQL database into PostgreSQL** using SQLAlchemy.

It:

- Connects to an existing MySQL database
- Reflects all table definitions
- Converts MySQL-specific types to PostgreSQL-safe types
- Creates the same tables (schema only, **no data**) in a PostgreSQL database

> ⚠️ This script only creates the schema in PostgreSQL.  
> It does **not** copy data rows (you disabled that part on purpose).

---

## 1. Requirements

Before you start, you need:

- **Python** 3.8+ (3.10 recommended)
- **MySQL** server with an existing database
- **PostgreSQL** server and an empty target database
- `requirements.txt` (already in this project)

The script uses:

- `sqlalchemy`
- `pymysql`
- `psycopg2` or `psycopg2-binary`

---

## 2. Clone / Download the Project

If you’re using Git:

```bash
git clone https://github.com/sekliheng/MySQLToPostgreSQL.git
cd mysql2postgres
