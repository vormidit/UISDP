import uuid

from flask import Flask, render_template, Response, request, url_for, redirect, session, jsonify, json, flash, \
    send_file, make_response, send_from_directory
from flask_pymongo import PyMongo
from pydantic import Field, BaseModel
from pymongo import MongoClient
from mongoengine import connect, StringField, Document, QuerySet
from model.pymongo_model import SimpleModel
from flask_mail import Mail, Message
import bcrypt
import logging
import os
from fpdf import FPDF

# App Setup
app = Flask(__name__)

# Logger Setup
logger = logging.getLogger(__name__)
logger.propagate = False

# Mongo Setup
app.config["MONGO_URI"] = "mongodb://localhost:27017"
app.config["SECRET_KEY"] = 'techuniversity'

connect('flaskDB', host=app.config["MONGO_URI"])

# mongo_client = MongoClient(app.config["MONGO_URI"])
# db = mongo_client['flaskDB']

# mongo = PyMongo(app)
# db = mongo.db

# Mail Password
MAIL_PASSWORD = 'fishing4'

# Salt for Encryption
salt = bcrypt.gensalt()

# Mail Setup
app.config['MAIL_SERVER'] = 'smtp.abv.bg'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'isudp@abv.bg'
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# Paths for Files
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 10
app.config['UPLOAD_EXTENSIONS'] = ['.doc', '.docx', '.pdf']
app.config['UPLOAD_PATH'] = '/home/angel/Desktop/webapp/flask/uploads'
app.config['REF_PATH'] = '/home/angel/Desktop/webapp/flask/references'


class User(Document):
    username = StringField()
    password = StringField()
    role = StringField()
    department = StringField()
    email = StringField()
    meta = {'collection': 'users'}

    def hash_password(self):
        self.password = bcrypt.hashpw(self.password.encode('utf-8'), salt).decode('utf8')

    def check_password(self, password):
        if bcrypt.checkpw(password.encode('utf-8'),
                          self.password.encode('utf-8')
                          ):
            return True
        return False

    def change_profile_data(self, username, password):
        self.username = username
        self.password = password
        self.hash_password()
        if self.update(username=self.username, password=self.password):
            return True
        return False

    def update_password(self, password):
        self.password = password
        self.hash_password()
        if self.update(password=self.password):
            return True
        return False

class Admin(Document):
    username = StringField()
    email = StringField()
    meta = {'collection': 'admins'}

    @staticmethod
    def add_new_admin(username, password, email):
        new_user = User(username=username, password=password, role='admin', department='administrator', email=email)
        new_admin = Admin(username=username, email=email)
        new_user.hash_password()
        if new_user.save() and new_admin.save():
            return True
        return False

    @staticmethod
    def add_new_student(username, password, fnumber,
                        fname, lname, department, email):
        new_user = User(username=username, password=password, role='student', department=department, email=email)
        new_student = Student(fnumber=fnumber, fname=fname, lname=lname, email=email, department=department,
                              project_manager='None',
                              reviewer='None',
                              thesis_name='None',
                              review_path='None',
                              thesis_path='None',
                              degree_defense='None')
        new_user.hash_password()
        if new_user.save() and new_student.save():
            return True
        return False

    @staticmethod
    def add_new_dean(username, password, fnumber, fname, lname, email):
        new_user = User(username=username, password=password, role='dean', department=department, email=email)
        new_dean = Dean(fnumber=fnumber, fname=fname, lname=lname, email=email)
        new_user.hash_password()
        if new_user.save() and new_dean.save():
            return True
        return False

    @staticmethod
    def add_new_department_head(username, password, fnumber, fname, lname, role, department, email):
        new_user = User(username=username, password=password, role=role, department=department, email=email)
        if role != 'head_of_department2':
            pass
        else:
            new_department_head2 = DepartmentHead2(fnumber=fnumber, fname=fname, lname=lname, email=email,
                                                   department=department,
                                                   role=role)
            new_user.hash_password()
            if new_user.save():
                if new_department_head2.save():
                    pass
                else:
                    return False
            else:
                return False
            return True
        new_department_head = DepartmentHead(fnumber=fnumber, fname=fname, lname=lname, email=email,
                                             department=department,
                                             role=role)
        new_user.hash_password()
        if new_user.save() and new_department_head.save():
            return True
        return False

    @staticmethod
    def add_new_proj_mngr(username, password, fnumber, fname, lname, department, email):
        new_user = User(username=username, password=password, role='project_manager', department=department, email=email)
        new_project_manager = ProjectManager(fnumber=fnumber, fname=fname, lname=lname, email=email,
                                             department=department,
                                             students='None')
        new_user.hash_password()
        if new_user.save() and new_project_manager.save():
            return True
        return False

    @staticmethod
    def add_new_reviewer(username, password, fnumber, fname, lname, department, email):
        new_user = User(username=username, password=password, role='reviewer', department=department, email=email)
        new_reviewer = Reviewer(fnumber=fnumber, fname=fname, lname=lname, email=email,
                                department=department,
                                students='None')
        new_user.hash_password()
        if new_user.save() and new_reviewer.save():
            return True
        return False

    @staticmethod
    def delete_admin(username):
        this_user = User.objects(username=username).first()
        this_admin = Admin.objects(username=username).first()
        if this_user and this_admin:
            if this_user.delete() and this_admin.delete():
                return True
            return False
        return False

    @staticmethod
    def delete_student(fnumber, email):
        this_user = User.objects(email=email).first()
        this_student = Student.objects(fnumber=fnumber).first()
        if this_user and this_student:
            if this_user.delete() and this_student.delete():
                return True
            return False
        return False

    @staticmethod
    def delete_teacher(fnumber, email):
        this_user = User.objects(email=email).first()
        if this_user.role == 'dean':
            this_dean = Dean.objects(fnumber=fnumber).first()
            if this_user.delete() and this_dean.delete():
                return True
            return False
        if this_user.role == 'head_of_department':
            this_department_head = DepartmentHead.objects(fnumber=fnumber).first()
            if this_user.delete() and this_department_head.delete():
                return True
            return False
        if this_user.role == 'head_of_department2':
            this_department_head2 = DepartmentHead2.objects(fnumber=fnumber).first()
            if this_user.delete() and this_department_head2.delete():
                return True
            return False
        if this_user.role == 'project_manager':
            this_project_manager = ProjectManager.objects(fnumber=fnumber).first()
            if this_user.delete() and this_project_manager.delete():
                return True
            return False
        if this_user.role == 'reviewer':
            this_reviewer = Reviewer.objects(fnumber=fnumber).first()
            if this_user.delete() and this_reviewer.delete():
                return True
            return False

    @staticmethod
    def search_admin(username):
        admin = Admin.objects(username=username).first()
        if admin:
            return {'username': admin.username}
        return False
    @staticmethod
    def search_student(fnumber):
        student = Student.objects(fnumber=fnumber).first()
        if student:
            return {'fnumber': student.fnumber, 'fname': student.fname,
                    'lname': student.lname, 'department': student.department,
                    'spec': student.spec}
        return False

    @staticmethod
    def search_teacher(fnumber, email):
        this_user = User.objects(email=email).first()
        if this_user:
            if this_user.role == 'dean':
                this_dean = Dean.objects(fnumber=fnumber).first()
                return {'fname': this_dean.fname, 'lname': this_dean.lname}

            if this_user.role == 'head_of_department':
                this_department_head = DepartmentHead.objects(fnumber=fnumber).first()
                return {'fname': this_department_head.fname, 'lname': this_department_head.lname}

            if this_user.role == 'head_of_department2':
                this_department_head2 = DepartmentHead2.objects(fnumber=fnumber).first()
                return {'fname': this_department_head2.fname, 'lname': this_department_head2.lname}

            if this_user.role == 'project_manager':
                this_project_manager = ProjectManager.objects(fnumber=fnumber).first()
                return {'fname': this_project_manager.fname, 'lname': this_project_manager.lname}

            if this_user.role == 'reviewer':
                this_reviewer = Reviewer.objects(fnumber=fnumber).first()
                return {'fname': this_reviewer.fname, 'lname': this_reviewer.lname}
        return False

class Student(Document):
    meta = {'collection': 'students'}
    fnumber = StringField()
    fname = StringField()
    lname = StringField()
    email = StringField()
    department = StringField()
    project_manager = StringField('None')
    reviewer = StringField('None')
    thesis_path = StringField('None')
    review_path = StringField('None')
    thesis_name = StringField('None')
    degree_defense = StringField('None')

    @staticmethod
    def diploma_data(email):
        student = Student.objects(email=email).first()
        if student:
            return {'thesis_name': student.thesis_name,
                    'project_manager': student.project_manager,
                    'reviewer': student.reviewer,
                    'degree_defense': student.degree_defense}
        return False

    @staticmethod
    def upload_diploma_project(email, file):
        current_student = Student.objects(email=email).first()
        if current_student.thesis_path != 'None':
            os.remove(os.path.join(current_student['thesis_path']))
            file_name = current_student.fname + '_' + current_student['lname'] + '_' + current_student.fnumber
            file.save(os.path.join(app.config['UPLOAD_PATH'] + '/diplom_thesis', file_name))
            return
        file_name = current_student.fname+'_'+current_student['lname']+'_'+current_student.fnumber
        file_path = app.config['UPLOAD_PATH']+'/diplom_thesis/'+file_name
        file.save(os.path.join(app.config['UPLOAD_PATH']+'/diplom_thesis', file_name))
        current_student.update(thesis_path=file_path)
        return

    @staticmethod
    def download_diploma_project(email):
        current_student = Student.objects(email=email).first()
        if current_student.thesis_path != 'None':
            return send_file(current_student.thesis_path, as_attachment=True)
        return 'Нямате качен файл!'
class Dean(Document):
    meta = {'collection': 'deans'}
    fnumber = StringField()
    fname = StringField()
    lname = StringField()
    email = StringField()

    @staticmethod
    def download_references(option):
        if option == "swt":
            mdata = list(Student.objects(__raw__={'thesis_name': {'$ne': "None"}}).only('fname', 'lname', 'fnumber', 'department'))
            print(mdata)
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Report for students with Thesis', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 4
            pdf.ln(1)
            th = pdf.font_size

            for student in mdata:
                pdf.cell(col_width, th, student['fname'], border=1)
                pdf.cell(col_width, th, student['lname'], border=1)
                pdf.cell(col_width, th, student['department'], border=1)
                pdf.cell(col_width, th, student['fnumber'], border=1)
                pdf.ln(th)
            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '- end of report -', align='C')
            fileName = '/home/angel/Desktop/webapp/flask/references/' + 'Report_StudentsWithThesis_' + session[
                'username'] + '.pdf'
            filePath = 'Report_StudentsWithThesis_' + session['username'] + '.pdf'
            pdf.output(name=fileName, dest='F').encode('latin-1')
            file = send_from_directory(directory=app.config['REF_PATH'], path=filePath)
            response = make_response(file)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'attachment; filename=' + filePath
            return file, filePath
        if option == "swot":
            mdata = list(Student.objects(__raw__={'thesis_name': "None"}).only('fname', 'lname', 'fnumber', 'department'))
            print(mdata)
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Report for students without Thesis', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 4
            pdf.ln(1)
            th = pdf.font_size

            for student in mdata:
                pdf.cell(col_width, th, student['fname'], border=1)
                pdf.cell(col_width, th, student['lname'], border=1)
                pdf.cell(col_width, th, student['department'], border=1)
                pdf.cell(col_width, th, student['fnumber'], border=1)
                pdf.ln(th)
            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '- end of report -', align='C')
            fileName = '/home/angel/Desktop/webapp/flask/references/' + 'Report_StudentsWithoutThesis_' + session[
                'username'] + '.pdf'
            filePath = 'Report_StudentsWithoutThesis_' + session['username'] + '.pdf'
            pdf.output(name=fileName, dest='F').encode('latin-1')
            file = send_from_directory(directory=app.config['REF_PATH'], path=filePath)
            return file, filePath
        if option == "sup":
            mdata = list(
                Student.objects(__raw__={'thesis_path': {'$ne': "None"}}).only('fname', 'lname', 'fnumber', 'department'))
            print(mdata)
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Report for students with Finished Diplom Project', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 4
            pdf.ln(1)
            th = pdf.font_size

            for student in mdata:
                pdf.cell(col_width, th, student['fname'], border=1)
                pdf.cell(col_width, th, student['lname'], border=1)
                pdf.cell(col_width, th, student['department'], border=1)
                pdf.cell(col_width, th, student['fnumber'], border=1)
                pdf.ln(th)
            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '- end of report -', align='C')
            fileName = '/home/angel/Desktop/webapp/flask/references/' + 'Report_StudentsWithFinishedProject_' + session[
                'username'] + '.pdf'
            filePath = 'Report_StudentsWithFinishedProject_' + session['username'] + '.pdf'
            pdf.output(name=fileName, dest='F').encode('latin-1')
            file = send_from_directory(directory=app.config['REF_PATH'], path=filePath)
            return file, filePath
        if option == "sdd":
            mdata = list(
                Student.objects(__raw__={'degree_defense': {'$ne': "None"}}).only('fname', 'lname', 'fnumber',
                                                                               'department'))
            print(mdata)
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Report for students with Degree defensed', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 4
            pdf.ln(1)
            th = pdf.font_size

            for student in mdata:
                pdf.cell(col_width, th, student['fname'], border=1)
                pdf.cell(col_width, th, student['lname'], border=1)
                pdf.cell(col_width, th, student['department'], border=1)
                pdf.cell(col_width, th, student['fnumber'], border=1)
                pdf.ln(th)
            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '- end of report -', align='C')
            fileName = '/home/angel/Desktop/webapp/flask/references/' + 'Report_StudentsWithDegreeDefensed_' + session[
                'username'] + '.pdf'
            filePath = 'Report_StudentsWithDegreeDefensed_' + session['username'] + '.pdf'
            pdf.output(name=fileName, dest='F').encode('latin-1')
            file = send_from_directory(directory=app.config['REF_PATH'], path=filePath)
            return file, filePath


class DepartmentHead(Document):
    meta = {'collection': 'heads_of_departments',
            'allow_inheritance': True}
    fnumber = StringField()
    fname = StringField()
    lname = StringField()
    email = StringField()
    department = StringField()
    role = StringField()

    @staticmethod
    def download_references(option):
        current_user = DepartmentHead.objects(email=session['email'])
        department = current_user.department
        if option == "swt":
            mdata = list(Student.objects(__raw__={'department': department, 'thesis_name': {'$ne': "None"}}).only('fname', 'lname', 'fnumber', 'department'))
            print(mdata)
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Report for students with Thesis in ' + department + ' Department', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 4
            pdf.ln(1)
            th = pdf.font_size

            for student in mdata:
                pdf.cell(col_width, th, student['fname'], border=1)
                pdf.cell(col_width, th, student['lname'], border=1)
                pdf.cell(col_width, th, student['department'], border=1)
                pdf.cell(col_width, th, student['fnumber'], border=1)
                pdf.ln(th)
            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '- end of report -', align='C')
            fileName = '/home/angel/Desktop/webapp/flask/references/' + 'Report_StudentsWithThesis_' + department + '_' + \
                       session[
                           'username'] + '.pdf'
            filePath = 'Report_StudentsWithThesis_' + department + '_' + session['username'] + '.pdf'
            pdf.output(name=fileName, dest='F').encode('latin-1')
            file = send_from_directory(directory=app.config['REF_PATH'], path=filePath)
            return file, filePath
        if option == "swot":
            mdata = list(Student.objects(__raw__={'department': department, 'thesis_name': "None"}).only('fname', 'lname', 'fnumber', 'department'))
            print(mdata)
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Report for students without Thesis in ' + department + ' Department', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 4
            pdf.ln(1)
            th = pdf.font_size

            for student in mdata:
                pdf.cell(col_width, th, student['fname'], border=1)
                pdf.cell(col_width, th, student['lname'], border=1)
                pdf.cell(col_width, th, student['department'], border=1)
                pdf.cell(col_width, th, student['fnumber'], border=1)
                pdf.ln(th)
            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '- end of report -', align='C')
            fileName = '/home/angel/Desktop/webapp/flask/references/' + 'Report_StudentsWithoutThesis_' + department + '_' + \
                       session[
                           'username'] + '.pdf'
            filePath = 'Report_StudentsWithoutThesis_' + session['username'] + '.pdf'
            pdf.output(name=fileName, dest='F').encode('latin-1')
            file = send_from_directory(directory=app.config['REF_PATH'], path=filePath)
            return file, filePath

        if option == "sup":
            mdata = list(Student.objects(__raw__={'department': department, 'thesis_path': {'$ne': "None"}}).only('fname', 'lname', 'fnumber', 'department'))
            print(mdata)
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Report for students with Finished Diplom Project', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 4
            pdf.ln(1)
            th = pdf.font_size

            for student in mdata:
                pdf.cell(col_width, th, student['fname'], border=1)
                pdf.cell(col_width, th, student['lname'], border=1)
                pdf.cell(col_width, th, student['department'], border=1)
                pdf.cell(col_width, th, student['fnumber'], border=1)
                pdf.ln(th)
            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '- end of report -', align='C')
            fileName = '/home/angel/Desktop/webapp/flask/references/' + 'Report_StudentsWithFinishedProject_' + department + '_' + \
                       session[
                           'username'] + '.pdf'
            filePath = 'Report_StudentsWithFinishedProject_' + session['username'] + '.pdf'
            pdf.output(name=fileName, dest='F').encode('latin-1')
            file = send_from_directory(directory=app.config['REF_PATH'], path=filePath)
            return file, filePath
        if option == "sdd":
            mdata = list(Student.objects(__raw__={'department': department, 'degree_defense': {'$ne': "None"}}).only('fname', 'lname', 'fnumber', 'department'))
            print(mdata)
            pdf = FPDF()
            pdf.add_page()
            page_width = pdf.w - 2 * pdf.l_margin
            pdf.set_font('Times', 'B', 14.0)
            pdf.cell(page_width, 0.0, 'Report for students with Degree defensed', align='C')
            pdf.ln(10)
            pdf.set_font('Courier', '', 12)
            col_width = page_width / 4
            pdf.ln(1)
            th = pdf.font_size

            for student in mdata:
                pdf.cell(col_width, th, student['fname'], border=1)
                pdf.cell(col_width, th, student['lname'], border=1)
                pdf.cell(col_width, th, student['department'], border=1)
                pdf.cell(col_width, th, student['fnumber'], border=1)
                pdf.ln(th)
            pdf.ln(10)
            pdf.set_font('Times', '', 10.0)
            pdf.cell(page_width, 0.0, '- end of report -', align='C')
            fileName = '/home/angel/Desktop/webapp/flask/references/' + 'Report_StudentsWithDegreeDefensed_' + department + '_' + \
                       session[
                           'username'] + '.pdf'
            filePath = 'Report_StudentsWithDegreeDefensed_' + session['username'] + '.pdf'
            pdf.output(name=fileName, dest='F').encode('latin-1')
            file = send_from_directory(directory=app.config['REF_PATH'], path=filePath)
            return file, filePath


    def search_student(self, fnumber):
        student = Student.objects(fnumber=fnumber, department=self.department).first()
        if student:
            return {'fnumber': student.fnumber, 'fname': student.fname,
                    'lname': student.lname, 'project_manager': student.project_manager,
                    'reviewer': student.reviewer}
        return False

    def search_teachers(self):
        proj_mngrs = ProjectManager.objects(department=self.department).only('fname', 'lname')
        reviewers = Reviewer.objects(department=self.department).only('fname', 'lname')
        return proj_mngrs, reviewers


class DepartmentHead2(DepartmentHead):
    pass


class ProjectManager(Document):
    meta = {'collection': 'project_managers'}
    fnumber = StringField()
    fname = StringField()
    lname = StringField()
    email = StringField()
    department = StringField()
    students = StringField()


class Reviewer(Document):
    meta = {'collection': 'reviewers'}
    fnumber = StringField()
    fname = StringField()
    lname = StringField()
    email = StringField()
    department = StringField()
    students = StringField()
