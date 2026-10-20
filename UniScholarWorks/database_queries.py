import mysql.connector
import os
from dotenv import load_dotenv
from my_classes import Report, User
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

load_dotenv()

ph = PasswordHasher()

db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}


def get_user_by_credentials(user_id, password, user_type):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        if user_type == "teacher":
            query = "SELECT * FROM teachers WHERE (teacher_id = %s OR email = %s)"
        else:
            query = "SELECT * FROM students WHERE (student_id = %s OR email = %s)"

        cursor.execute(query, (user_id, user_id))
        user_data = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    if user_data:
        try:
            ph.verify(user_data['password'], password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return None

        user = User()
        user.set_user_id(user_data['teacher_id'] if user_type == 'teacher' else user_data['student_id'])
        user.set_email(user_data['email'])
        user.set_name(user_data['name'])
        return user

    return None


def register_student(student_id, name, email, password):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        hashed_password = ph.hash(password)

        cursor.execute("""
            INSERT INTO students (student_id, name, email, password)
            VALUES (%s, %s, %s, %s)
        """, (student_id, name, email, hashed_password))

        conn.commit()
        return True

    except mysql.connector.IntegrityError:
        return False

    finally:
        cursor.close()
        conn.close()


def register_teacher(teacher_id, name, email, password):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        hashed_password = ph.hash(password)

        cursor.execute("""
            INSERT INTO teachers (teacher_id, name, email, password)
            VALUES (%s, %s, %s, %s)
        """, (teacher_id, name, email, hashed_password))

        conn.commit()
        return True

    except mysql.connector.IntegrityError:
        return False

    finally:
        cursor.close()
        conn.close()


def search_reports(query, page, per_page):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        offset = (page - 1) * per_page

        sql = """
            SELECT DISTINCT reports.report_id, title, summary, review_date
            FROM reports
            INNER JOIN reviews ON reports.report_id = reviews.report_id
            WHERE reviews.decision = 'accepted'
        """

        params = []

        if query and query.strip():
            sql += " AND (reports.title LIKE %s OR reports.summary LIKE %s)"
            search_term = f"%{query}%"
            params.extend([search_term, search_term])

        sql += " ORDER BY review_date DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        reports_list = []

        for row in rows:
            report = Report()
            report.set_report_id(row['report_id'])
            report.set_title(row['title'])
            report.set_summary(row['summary'])
            report.set_date(row['review_date'])

            cursor.execute("""
                SELECT name FROM students
                WHERE student_id IN (
                    SELECT student_id FROM report_authors WHERE report_id = %s
                )
            """, (row['report_id'],))
            authors = cursor.fetchall()
            report.set_authors([a['name'] for a in authors])

            cursor.execute("SELECT tag FROM report_tag WHERE report_id = %s", (row['report_id'],))
            tags = cursor.fetchall()
            report.set_tags([t['tag'] for t in tags])

            cursor.execute("SELECT type FROM reports WHERE report_id = %s", (row['report_id'],))
            report_type = cursor.fetchone()
            if report_type:
                report.set_report_type(report_type['type'])

            reports_list.append(report)

    finally:
        cursor.close()
        conn.close()

    return reports_list


def get_report_by_id(report_id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM reports WHERE report_id = %s", (report_id,))
        row = cursor.fetchone()

        if not row:
            return None

        report = Report()
        report.set_report_id(row['report_id'])
        report.set_title(row['title'])
        report.set_summary(row['summary'])
        report.set_link(row['link'])
        report.set_supervisor(row['supervisor'])
        report.set_report_type(row['type'])
        report.set_file_id(row['file_id'])

        cursor.execute("""
            SELECT name FROM students
            WHERE student_id IN (
                SELECT student_id FROM report_authors WHERE report_id = %s
            )
        """, (report_id,))
        authors = cursor.fetchall()
        report.set_authors([a['name'] for a in authors])

        cursor.execute("SELECT tag FROM report_tag WHERE report_id = %s", (report_id,))
        tags = cursor.fetchall()
        report.set_tags([t['tag'] for t in tags])

        cursor.execute("""
            SELECT review_date, pdf_allowed, decision, comment
            FROM reviews WHERE report_id = %s
        """, (report_id,))
        review = cursor.fetchone()
        if review:
            report.set_date(review['review_date'])
            report.set_pdf_allowed(review['pdf_allowed'])
            report.set_decision(review['decision'])
            report.set_comment(review['comment'])

    finally:
        cursor.close()
        conn.close()

    return report


def get_all_supervisors():

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT teacher_id, name FROM teachers")
        supervisors = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return supervisors


def get_common_tags():

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT tag, COUNT(*) as count
            FROM report_tag
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 10
        """)
        tags = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return [t['tag'] for t in tags]


def submit_new_report(title, report_type, authors, supervisor,
                      summary, link, tags, submitter_id, file_id=None):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        conn.start_transaction()

        cursor.execute("""
            INSERT INTO reports (title, summary, type, supervisor, link, file_id, submitter_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, summary, report_type, supervisor, link, file_id, submitter_id))

        report_id = cursor.lastrowid

        for author_id in authors:
            cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (author_id,))
            result = cursor.fetchone()
            if result:
                cursor.execute("""
                    INSERT INTO report_authors (report_id, student_id)
                    VALUES (%s, %s)
                """, (report_id, result[0]))
            else:
                conn.rollback()
                return False

        if tags:
            for tag in tags:
                cursor.execute("""
                    INSERT INTO report_tag (report_id, tag)
                    VALUES (%s, %s)
                """, (report_id, tag))

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def get_submitted_reports_by_user(user_id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT reports.report_id, title, summary, submitter_id,
                   submission_date, comment
            FROM reports
            LEFT JOIN reviews ON reports.report_id = reviews.report_id
            WHERE submitter_id = %s
            ORDER BY reports.report_id DESC
        """, (user_id,))

        rows = cursor.fetchall()
        reports_list = []

        for row in rows:
            report = Report()
            report.set_report_id(row['report_id'])
            report.set_title(row['title'])
            report.set_summary(row['summary'])
            report.set_date(row['submission_date'])
            report.set_submitter_id(row['submitter_id'])
            report.set_comment(row['comment'])

            cursor.execute("""
                SELECT name FROM students
                WHERE student_id IN (
                    SELECT student_id FROM report_authors WHERE report_id = %s
                )
            """, (row['report_id'],))
            authors = cursor.fetchall()
            report.set_authors([a['name'] for a in authors])

            cursor.execute("SELECT tag FROM report_tag WHERE report_id = %s", (row['report_id'],))
            tags = cursor.fetchall()
            report.set_tags([t['tag'] for t in tags])

            cursor.execute("SELECT decision FROM reviews WHERE report_id = %s", (row['report_id'],))
            review = cursor.fetchone()
            report.set_report_status(review['decision'] if review else "pending")

            reports_list.append(report)

    finally:
        cursor.close()
        conn.close()

    return reports_list


def get_submitted_reports_by_supervisor(supervisor_id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT reports.report_id, title, summary, submitter_id,
                   submission_date, comment
            FROM reports
            LEFT JOIN reviews ON reports.report_id = reviews.report_id
            WHERE supervisor = %s
            ORDER BY reports.report_id DESC
        """, (supervisor_id,))

        rows = cursor.fetchall()
        pending_list = []
        reviewed_list = []

        for row in rows:
            report = Report()
            report.set_report_id(row['report_id'])
            report.set_title(row['title'])
            report.set_summary(row['summary'])
            report.set_date(row['submission_date'])
            report.set_submitter_id(row['submitter_id'])
            report.set_comment(row['comment'])

            cursor.execute("""
                SELECT name FROM students
                WHERE student_id IN (
                    SELECT student_id FROM report_authors WHERE report_id = %s
                )
            """, (row['report_id'],))
            authors = cursor.fetchall()
            report.set_authors([a['name'] for a in authors])

            cursor.execute("SELECT tag FROM report_tag WHERE report_id = %s", (row['report_id'],))
            tags = cursor.fetchall()
            report.set_tags([t['tag'] for t in tags])

            cursor.execute("SELECT decision FROM reviews WHERE report_id = %s", (row['report_id'],))
            review = cursor.fetchone()

            if review:
                report.set_report_status(review['decision'])
                reviewed_list.append(report)
            else:
                report.set_report_status("pending")
                pending_list.append(report)

    finally:
        cursor.close()
        conn.close()

    return pending_list, reviewed_list


def submit_report_review(report_id, reviewer_id, decision, comment, pdf_allowed=False):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO reviews (report_id, teacher_id, decision, comment, pdf_allowed)
            VALUES (%s, %s, %s, %s, %s)
        """, (report_id, reviewer_id, decision, comment, pdf_allowed))

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def get_pending_review_count(teacher_id):

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM reports
            WHERE supervisor = %s
            AND report_id NOT IN (
                SELECT report_id FROM reviews
                WHERE report_id IS NOT NULL
            )
        """, (teacher_id,))

        result = cursor.fetchone()

    finally:
        cursor.close()
        conn.close()

    return result['count'] if result else 0