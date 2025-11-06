from flask import Flask, flash, redirect, render_template, request, url_for

from database import get_connection


app = Flask(__name__)
app.secret_key = "SeCrEtKeY"


def get_departments():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT dept_name FROM faculties ORDER BY dept_name"
            )
            depts = [row["dept_name"] for row in cursor.fetchall()]
            return depts
    finally:
        conn.close()


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search():

    search_type = request.args.get("type", "name")
    query = request.args.get("query", "").strip()

    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for("index"))

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            if search_type == "name":

                sql = """
                    SELECT id, name, dept_name, tot_cred
                    FROM learners
                    WHERE name LIKE %s
                    ORDER BY name
                """
                pattern = f"%{query}%"
                cursor.execute(sql, (pattern,))
            else:

                sql = """
                    SELECT id, name, dept_name, tot_cred
                    FROM learners
                    WHERE CAST(id AS CHAR) LIKE %s
                    ORDER BY id
                """
                pattern = f"%{query}%"
                cursor.execute(sql, (pattern,))

            results = cursor.fetchall()

            return render_template(
                "search_results.html",
                students=results,
                search_type=search_type,
                query=query,
            )
    finally:
        conn.close()


@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        dept_name = request.form.get("dept_name", "").strip()
        is_transfer = request.form.get("is_transfer") == "on"
        tot_cred = request.form.get("tot_cred", "0").strip()

        if not student_id or not name or not dept_name:
            flash("All fields are required.", "error")
            return redirect(url_for("add_student"))

        if is_transfer:
            try:
                tot_cred = int(tot_cred)
            except ValueError:
                flash("Invalid credit value for transfer student.", "error")
                return redirect(url_for("add_student"))
        else:
            tot_cred = 0

        conn = get_connection()
        try:
            with conn.cursor() as cursor:

                try:
                    student_id_int = int(student_id)
                except ValueError:
                    flash("Student ID must be a number.", "error")
                    return redirect(url_for("add_student"))

                cursor.execute(
                    "SELECT id FROM learners WHERE id = %s", (student_id_int,)
                )
                if cursor.fetchone():
                    flash(f"Student ID {student_id} already exists.", "error")
                    return redirect(url_for("add_student"))

                sql = """
                    INSERT INTO learners (id, name, dept_name, tot_cred)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (student_id_int, name, dept_name, tot_cred))
                conn.commit()

                flash(
                    f"Student {name} (ID: {student_id}) added successfully!", "success"
                )
                return redirect(url_for("index"))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding student: {str(e)}", "error")
            return redirect(url_for("add_student"))
        finally:
            conn.close()
    else:

        departments = get_departments()
        return render_template("add_student.html", departments=departments)


@app.route("/add_department", methods=["GET", "POST"])
def add_department():
    if request.method == "POST":
        dept_name = request.form.get("dept_name", "").strip()
        building = request.form.get("building", "").strip()
        budget = request.form.get("budget", "").strip()

        if not dept_name:
            flash("Department name is required.", "error")
            return redirect(url_for("add_department"))

        try:
            budget_float = float(budget) if budget else 0.0
        except ValueError:
            flash("Budget must be a valid number.", "error")
            return redirect(url_for("add_department"))

        conn = get_connection()
        try:
            with conn.cursor() as cursor:

                cursor.execute(
                    "SELECT dept_name FROM faculties WHERE dept_name = %s", (dept_name,)
                )
                if cursor.fetchone():
                    flash(f"Department {dept_name} already exists.", "error")
                    return redirect(url_for("add_department"))

                sql = """
                    INSERT INTO faculties (dept_name, building, budget)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(
                    sql, (dept_name, building if building else None, budget_float)
                )
                conn.commit()

                flash(f"Department {dept_name} added successfully!", "success")
                return redirect(url_for("index"))
        except Exception as e:
            conn.rollback()
            flash(f"Error adding department: {str(e)}", "error")
            return redirect(url_for("add_department"))
        finally:
            conn.close()
    else:

        return render_template("add_department.html")


@app.route("/schedule/<student_id>")
def schedule(student_id):

    year_filter = request.args.get("year", "").strip()

    conn = get_connection()
    try:
        with conn.cursor() as cursor:

            try:
                student_id_int = int(student_id)
            except ValueError:
                flash(f"Invalid student ID: {student_id}", "error")
                return redirect(url_for("index"))

            cursor.execute(
                "SELECT id, name FROM learners WHERE id = %s", (student_id_int,)
            )
            student = cursor.fetchone()

            if not student:
                flash(f"Student with ID {student_id} not found.", "error")
                return redirect(url_for("index"))

            if year_filter:

                try:
                    year_filter_int = int(year_filter)
                except ValueError:
                    flash(f"Invalid year filter: {year_filter}", "error")
                    return redirect(url_for("schedule", student_id=student_id))

                sql = """
                    SELECT l.id, l.name, r.course_id, r.semester, r.year
                    FROM learners l
                    JOIN registrations r ON l.id = r.id
                    WHERE l.id = %s AND r.year = %s
                    ORDER BY r.year DESC, r.semester, r.course_id
                """
                cursor.execute(sql, (student_id_int, year_filter_int))
            else:
                sql = """
                    SELECT l.id, l.name, r.course_id, r.semester, r.year
                    FROM learners l
                    JOIN registrations r ON l.id = r.id
                    WHERE l.id = %s
                    ORDER BY r.year DESC, r.semester, r.course_id
                """
                cursor.execute(sql, (student_id_int,))

            schedule_data = cursor.fetchall()

            sql_years = """
                SELECT DISTINCT year
                FROM registrations
                WHERE id = %s
                ORDER BY year DESC
            """
            cursor.execute(sql_years, (student_id_int,))
            available_years = [row["year"] for row in cursor.fetchall()]

            return render_template(
                "schedule.html",
                student=student,
                schedule=schedule_data,
                available_years=available_years,
                selected_year=year_filter,
            )
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
