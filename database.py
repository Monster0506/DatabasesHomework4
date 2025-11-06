import pymysql

from config import load_config


def get_connection():

    config = load_config()
    return pymysql.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset=config["charset"],
        cursorclass=pymysql.cursors.DictCursor,
    )


def discover_schema():

    conn = get_connection()
    try:
        with conn.cursor() as cursor:

            cursor.execute("SHOW TABLES")
            tables = [
                row[f'Tables_in_{load_config()["database"]}']
                for row in cursor.fetchall()
            ]

            if "student" in tables:
                cursor.execute("DESCRIBE student")
                student_columns = [row["Field"] for row in cursor.fetchall()]

            dept_table = None
            if "department" in tables:
                dept_table = "department"
            elif "departments" in tables:
                dept_table = "departments"

            takes_table = None
            if "takes" in tables:
                takes_table = "takes"
            elif "enrollment" in tables:
                takes_table = "enrollment"
            elif "enrollments" in tables:
                takes_table = "enrollments"

            return {
                "tables": tables,
                "student_columns": student_columns if "student" in tables else [],
                "department_table": dept_table,
                "takes_table": takes_table,
            }
    finally:
        conn.close()
