class User:
    def __init__(self):
        self.user_id = ""
        self.email = ""
        self.name = ""

    def set_user_id(self, user_id):
        self.user_id = user_id

    def set_email(self, email):
        self.email = email

    def set_name(self, name):
        self.name = name

    def get_user_id(self):
        return self.user_id

    def get_email(self):
        return self.email

    def get_name(self):
        return self.name


class Report:
    def __init__(self):
        self.report_id = 0
        self.title = ""
        self.authors = []
        self.tags = []
        self.summary = ""
        self.date = None
        self.link = ""
        self.file_id = ""
        self.supervisor = ""
        self.decision = None
        self.pdf_allowed = False
        self.comment = ""
        self.report_type = ""
        self.report_status = ""
        self.submitter_id = ""

    def set_report_id(self, report_id):
        self.report_id = report_id

    def set_title(self, title):
        self.title = title

    def set_authors(self, authors):
        self.authors = authors if authors is not None else []

    def set_tags(self, tags):
        self.tags = tags if tags is not None else []

    def set_summary(self, summary):
        self.summary = summary

    def set_date(self, date):
        self.date = date

    def set_link(self, link):
        self.link = link

    def set_file_id(self, file_id):
        if file_id is not None:
            self.file_id = file_id

    def set_supervisor(self, supervisor):
        self.supervisor = supervisor

    def set_decision(self, decision):
        self.decision = decision

    def set_pdf_allowed(self, allowed):
        self.pdf_allowed = allowed

    def set_comment(self, comment):
        if comment:
            self.comment = comment

    def set_report_type(self, report_type):
        self.report_type = report_type

    def set_report_status(self, status):
        self.report_status = status

    def set_submitter_id(self, submitter_id):
        self.submitter_id = submitter_id

    def get_report_id(self):
        return self.report_id

    def get_title(self):
        return self.title

    def get_authors(self):
        return self.authors

    def get_tags(self):
        return self.tags

    def get_summary(self):
        return self.summary

    def get_date(self):
        if self.date:
            return self.date.strftime("%d %B %Y")
        return ""

    def get_link(self):
        return self.link

    def get_file_id(self):
        return self.file_id

    def get_supervisor(self):
        return self.supervisor

    def get_decision(self):
        return self.decision

    def get_pdf_allowed(self):
        return self.pdf_allowed

    def get_comment(self):
        if not self.comment:
            return None
        return self.comment

    def get_report_type(self):
        return self.report_type.capitalize()

    def get_report_status(self):
        return self.report_status.capitalize()

    def get_submitter_id(self):
        return self.submitter_id