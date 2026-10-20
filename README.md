# UniScholarWorks

A web application for managing and reviewing university academic reports. Students can submit their research reports and projects, while teachers can review and approve them.

---

## Demo

[![UniScholarWorks Demo](https://img.youtube.com/vi/IiQgX3hbQHs/0.jpg)](https://youtu.be/IiQgX3hbQHs?vq=hd720)

> Click the thumbnail above to watch the demo video.

---

## Features

### Students
- Register and log in as a student
- Submit academic reports with title, type, description, tags, supervisor, and optional PDF upload
- Track the status of your submitted reports
- Search and browse all approved reports

### Teachers
- Register and log in as a teacher (requires a special registration code)
- Review pending student report submissions
- Approve or reject reports with comments
- Control whether the uploaded PDF is publicly accessible

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | MySQL |
| Frontend | HTML, Jinja2 Templates, CSS |
| Authentication | Argon2 password hashing |
| File Uploads | PDF (max 16 MB) |
| Environment | python-dotenv |

---

## Project Structure

```
UniScholarWorks/
├── app.py                  # Main Flask application & routes
├── database_queries.py     # All database operations
├── my_classes.py           # Data model classes
├── project.sql             # Database schema
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not included)
├── templates/              # HTML templates
│   ├── login.html
│   ├── registration.html
│   ├── register_teacher.html
│   ├── home.html
│   ├── report.html
│   ├── submit_report.html
│   ├── submissions.html
│   ├── reviews.html
│   └── report_review.html
└── static/
    ├── styles/
    ├── scripts/
    ├── images/
    └── uploads/            # Uploaded PDF files (not included)
```

---

## Notes
- The `.env` file and `static/uploads/` folder are excluded from this repository for security and size reasons.
- Maximum PDF upload size is **16 MB**.
- Teacher registration requires a special code set in the `.env` file.
