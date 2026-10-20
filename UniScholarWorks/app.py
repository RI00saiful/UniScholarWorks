from flask import Flask, redirect, url_for, render_template, session, request, flash, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge
import os
from dotenv import load_dotenv
from datetime import timedelta
import database_queries as db_queries
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(days=1)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit


UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash('File is too large. Maximum allowed size is 16 MB.', 'error')
    return redirect(request.referrer or url_for('home'))



# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        user_id = request.form.get("userid")
        password = request.form.get("password")
        user_type = request.form.get("user_type")

        user = db_queries.get_user_by_credentials(user_id, password, user_type)

        if user:
            session["user_id"] = user.get_user_id()
            session["email"] = user.get_email()
            session["name"] = user.get_name()
            session["user_type"] = user_type
            session.permanent = True

            if user_type == "teacher":
                session["pending_reviews"] = db_queries.get_pending_review_count(session["user_id"])

            return redirect(url_for("home"))
        else:
            error = "Invalid username or password"
            return render_template("login.html", error=error, user_type=user_type)

    return render_template("login.html")



# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not student_id or not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("registration.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("registration.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("registration.html")

        status = db_queries.register_student(student_id, name, email, password)

        if status:
            flash("Registration successful! You can now log in.", "success")
        else:
            flash("Registration failed. Student ID or email already exists.", "error")

    return render_template("registration.html")



# REGISTER TEACHER
@app.route("/register_teacher", methods=["GET", "POST"])
def register_teacher():

    if request.method == "POST":
        teacher_id = request.form.get("teacher_id", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        teacher_code = request.form.get("teacher_code", "")

        
        if teacher_code != os.getenv("TEACHER_CODE"):
            flash("Invalid teacher registration code.", "error")
            return render_template("register_teacher.html")

        if not teacher_id or not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register_teacher.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register_teacher.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register_teacher.html")

        status = db_queries.register_teacher(teacher_id, name, email, password)

        if status:
            flash("Teacher registration successful! You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Registration failed. Teacher ID or email already exists.", "error")

    return render_template("register_teacher.html")



# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



# HOME
@app.route("/", methods=["GET"])
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    page = request.args.get('page', 1, type=int)
    per_page = 5
    query = request.args.get('q', '')

    reports = db_queries.search_reports(
        query=query,
        page=page,
        per_page=per_page
    )

    return render_template("home.html",
        reports=reports,
        query=query,
        page=page,
        per_page=per_page
    )



# REPORT DETAIL
@app.route("/report/<int:report_id>")
def report(report_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    report = db_queries.get_report_by_id(report_id)

    if not report:
        flash("Report not found.", "error")
        return redirect(url_for("home"))

    return render_template("report.html", report=report)



# SUBMIT REPORT
@app.route("/submit_report", methods=["GET", "POST"])
def submit_report():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get('title')
        report_type = request.form.get('report_type')
        description = request.form.get('description')
        report_link = request.form.get('report_link')
        supervisor = request.form.get('supervisor_id')
        authors = request.form.getlist('authors[]')
        tags_input = request.form.get('tags')
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []

        
        file_id = None
        if 'pdf_file' in request.files:
            pdf_file = request.files['pdf_file']
            if pdf_file.filename != '':
                
                if not pdf_file.filename.lower().endswith('.pdf'):
                    flash('Only PDF files are allowed.', 'error')
                    supervisors = db_queries.get_all_supervisors()
                    common_tags = db_queries.get_common_tags()
                    return render_template("submit_report.html",
                        supervisors=supervisors,
                        common_tags=common_tags
                    )
                filename = str(uuid.uuid4()) + '.pdf'
                pdf_file.save(os.path.join(UPLOAD_FOLDER, filename))
                file_id = filename

        if not title or not report_type or not authors or not supervisor:
            flash('Please fill in all required fields.', 'error')
            supervisors = db_queries.get_all_supervisors()
            common_tags = db_queries.get_common_tags()
            return render_template("submit_report.html",
                supervisors=supervisors,
                common_tags=common_tags
            )

        submission_status = db_queries.submit_new_report(
            title=title,
            report_type=report_type,
            authors=authors,
            supervisor=supervisor,
            summary=description,
            link=report_link,
            tags=tags,
            submitter_id=session["user_id"],
            file_id=file_id
        )

        if submission_status:
            flash('Report submitted successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Error submitting report. Please try again.', 'error')

    supervisors = db_queries.get_all_supervisors()
    common_tags = db_queries.get_common_tags()

    return render_template("submit_report.html",
        supervisors=supervisors,
        common_tags=common_tags
    )



# MY SUBMISSIONS
@app.route("/submissions")
def submissions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    reports = db_queries.get_submitted_reports_by_user(session["user_id"])
    return render_template("submissions.html", reports=reports)



# TEACHER - REVIEWS LIST
@app.route("/reviews")
def reviews():

    if "user_id" not in session or session["user_type"] != "teacher":
        return redirect(url_for("login"))

    pending_reports, reviewed_reports = db_queries.get_submitted_reports_by_supervisor(session["user_id"])

    if session.get("pending_reviews") and session["pending_reviews"] > 0:
        session["pending_reviews"] = 0

    return render_template("reviews.html",
        pending_reports=pending_reports,
        reviewed_reports=reviewed_reports
    )



# TEACHER - REVIEW A REPORT
@app.route("/report_review/<int:report_id>", methods=["GET", "POST"])
def report_review(report_id):

    if "user_id" not in session or session.get("user_type") != "teacher":
        return redirect(url_for("login"))

    report = db_queries.get_report_by_id(report_id)

    if not report:
        flash("Report not found.", "error")
        return redirect(url_for("reviews"))

    
    if report.get_decision():
        flash("This report has already been reviewed.", "info")
        return redirect(url_for("reviews"))

    if request.method == "POST":
        decision = request.form.get("decision")
        comment = request.form.get("comment", "")
        pdf_allowed = request.form.get("pdf_allowed") == "1"

        if not decision:
            flash("Please select a decision.", "error")
            return render_template("report_review.html", report=report)

        success = db_queries.submit_report_review(
            report_id=report_id,
            reviewer_id=session["user_id"],
            decision=decision,
            comment=comment,
            pdf_allowed=pdf_allowed   # FIX: was not being passed before
        )

        if success:
            flash("Review submitted successfully!", "success")
            return redirect(url_for("reviews"))
        else:
            flash("Error submitting review. Please try again.", "error")

    return render_template("report_review.html", report=report)



# DOWNLOAD PDF
@app.route("/download/<file_id>")
def download_file(file_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    
    try:
        uuid.UUID(file_id.replace('.pdf', ''))
    except ValueError:
        flash("Invalid file requested.", "error")
        return redirect(url_for("home"))

    return send_from_directory(UPLOAD_FOLDER, file_id, as_attachment=True)



if __name__ == "__main__":
    app.run(debug=True)