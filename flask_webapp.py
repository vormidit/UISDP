import time

from flask import Flask, render_template, request, url_for, redirect, session, jsonify, json, flash
from flask.app import setupmethod
from flask_pymongo import PyMongo
from threading import Thread
from flask_mail import Mail, Message
from env import MAIL_PASSWORD
from datetime import datetime, timedelta
import bcrypt
import logging
import os
import jwt

logger = logging.getLogger(__name__)
logger.propagate = False
app = Flask(__name__)


@app.before_request
def before_first_request():
    root = os.path.dirname(os.path.abspath(__file__))
    logdir = os.path.join(root, 'log')
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    log_file = os.path.join(logdir, 'logfile.log')
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s : %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


app.config['MAIL_SERVER'] = 'smtp.abv.bg'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'isudp@abv.bg'
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/flaskDB"
app.config["SECRET_KEY"] = 'techuniversity'
mongo = PyMongo(app)
salt = bcrypt.gensalt()


@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
def index():

    error = request.args.get('error')
    return render_template('index.html', error=error)


@app.route("/psw_reset_view")
def psw_reset_view():
    error = request.args.get('error')
    return render_template('email_ver.html', error=error)


@app.route("/password_reset", methods=['POST'])
def password_reset():

    email = request.form.get('email')
    try:
        user = mongo.db.users.find_one_or_404({"mail": email})
        token = jwt.encode({'public_id': user['id'], 'exp': datetime.utcnow() + timedelta(minutes=10)},
                           app.config['SECRET_KEY'], "HS256")
        msg = Message()
        msg.subject = "Password Reset"
        msg.sender = 'isudp@abv.bg'
        msg.recipients = [email]
        msg.html = render_template('reset_email.html', token=token)
        mail.send(msg)
        print('msg sent')
        error = 'Моля проверете Вашата поща!'
        return redirect(url_for('index', error=error))
    except:
        error = "Грешен имейл адрес!"
        return redirect(url_for('psw_reset_view', error=error))




@app.route("/password_reset_verified/<token>", methods=['GET', 'POST'])
def reset_verified(token):
    if request.method == "POST":
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = mongo.db.users.find_one_or_404({"id": data['public_id']})
        if not current_user:
            flash('Невалиден токен!')
            return redirect(url_for('index'))
        data = json.loads(request.data)
        password = data['password']
        enc_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        try:
            mongo.db.users.update({"id": current_user['id']},
                                    {"$set": {"password": enc_password.decode('utf-8')}})

            return 'OK'
        except:
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

    return render_template('reset_psw.html')


@app.route("/login", methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    try:
        found_username = mongo.db.users.find_one_or_404({"username": username})
    except:
        error = "Грешно потребителско име!"
        return redirect(url_for('index', error=error))
    hashed_password = found_username['password']
    role = found_username['role']
    name = found_username['username']
    session['role'] = role
    session['username'] = name

    if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
        if role == 'admin':
            logger.info('Administrator' + ' ' + username + ' ' + 'was loged in the system!')
            return redirect(url_for(session['role'] + '_main'))
        if role == 'student':
            logger.info('Student' + ' ' + username + ' ' + 'was loged in the system!')
            return redirect(url_for(session['role'] + '_main'))
        if role == 'dean':
            logger.info('Dean' + ' ' + username + ' ' + 'was loged in the system!')
            return redirect(url_for(session['role'] + '_main'))
        if role == 'head_of_department':
            logger.info('Head_of_department' + ' ' + username + ' ' + 'was loged in the system!')
            return redirect(url_for(session['role'] + '_main'))
        if role == 'head_of_department2':
            logger.info('Head_of_department*' + ' ' + username + ' ' + 'was loged in the system!')
            return redirect(url_for(session['role'] + '_main'))
        if role == 'project_manager':
            logger.info('Project_manager' + ' ' + username + ' ' + 'was loged in the system!')
            return redirect(url_for(session['role'] + '_main'))
        if role == 'reviewer':
            logger.info('Reviewer' + ' ' + username + ' ' + 'was loged in the system!')
            return redirect(url_for(session['role'] + '_main'))
    error = 'Грешна парола!'
    return redirect(url_for('index', error=error))


@app.route('/admin_main')
def admin_main():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))
    count_usr = mongo.db.users.estimated_document_count()
    data = dict()
    data['username'] = session['username']
    data['count_usr'] = count_usr

    return render_template('admin_main.html', data=data)


@app.route('/admin_prof_change', methods=['POST', 'GET'])
def admin_prof_change():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if request.method == "POST" and session['role'] == 'admin':
        data = json.loads(request.data)
        username = data['username']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
        try:
            mongo.db.users.update({"username": session['username']},
                                  {"$set": {"username": username, "password": password.decode('utf-8')}})
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна промяна!</p>'
        except:
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
    return render_template('admin_prof_change.html', data=session['username'])


@app.route('/admin_stu_search', methods=['GET', 'POST'])
def admin_stu_search():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if request.method == "POST":

        data = json.loads(request.data)
        fnumber = data['fnumber']
        student = mongo.db.students.find_one({"fnumber": fnumber})
        if student:
            return "<table id='stu_info'>"+"<tr><td>Ф.номер</td><td>" + \
                   student['fnumber'] + "</td></tr><tr><td>Име</td><td>" + \
                   student['fname'] + "</td></tr><tr><td>Фамилия</td><td>" + \
                   student['lname'] + "</td></tr><tr><td>Катедра</td><td>" + \
                   student['department'] + "</td></tr><tr><td>Специалност</td><td>" + \
                   student['department'] + "</td></tr><tr><td>Имейл</td><td>" + \
                   student['mail'] + "</td></tr><tr><td>Рък.дипл.проект</td><td>" + \
                   student['project_manager'] + "</td></tr><tr><td>Рецензент</td><td>" + \
                   student['reviewer'] + "</td></tr></table>"

        else:
            return "Записът не съществува!"

    return render_template('admin_stu_search.html')


@app.route('/admin_stu_add', methods=['POST', 'GET'])
def admin_stu_add():
    if request.method == "POST" and session['role'] == 'admin':

        data = json.loads(request.data)
        fnumber = data['fnumber']
        fname = data['fname']
        lname = data['lname']
        department = data['department']
        spec = data['spec']
        mail = data['mail']
        username = data['username']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
        try:
            mongo.db.users.insert_one(
                {'_id': time.time_ns(), 'fnumber': fnumber, 'username': username, 'password': password.decode('utf-8'), 'role': 'student'})
            mongo.db.students.insert_one(
                {'_id': time.time_ns(), 'fnumber': fnumber, 'fname': fname, 'lname': lname, 'department': department, 'spec': spec,
                 'mail': mail, 'project_manager': 'None', 'reviewer': 'None'})
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'
        except:
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

    if request.method == "POST":
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    return render_template('admin_stu_add.html')


@app.route('/admin_stu_del', methods=['GET', 'DELETE'])
def admin_stu_del():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if request.method == "DELETE" and session['role'] == 'admin':
        data = json.loads(request.data)
        fnumber = data['fnumber']
        try:
            mongo.db.users.remove({"fnumber": fnumber})
            mongo.db.students.remove({"fnumber": fnumber})
            return "Студентът" + " " + fnumber + " " + "е премахнат успешно!"
        except:
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

    return render_template('admin_stu_del.html')


@app.route('/admin_tea_search', methods=['POST', 'GET'])
def admin_tea_search():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))
    if request.method == "POST":
        data = json.loads(request.data)
        fnumber = data['fnumber']
        teacher = mongo.db.teachers.find_one({"fnumber": fnumber})
        if teacher:
            return "Записът" + " " + teacher["fnumber"] + " " + "съществува!"

        else:
            return "Записът не съществува!"

    return render_template('admin_tea_search.html')


@app.route('/admin_tea_add', methods=['POST', 'GET'])
def admin_tea_add():
    if request.method == "POST" and session['role'] == 'admin':
        data = json.loads(request.data)
        fnumber = data['fnumber']
        fname = data['fname']
        lname = data['lname']
        role = data['role']
        department = data['department']
        mail = data['mail']
        username = data['username']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), salt)

        if role != 'dean':
            pass
        else:
            mongo.db.users.insert_one(
                {'fnumber': fnumber, 'username': username, 'password': password.decode('utf-8'), 'role': role})
            mongo.db.dean.insert_one({'fnumber': fnumber, 'fname': fname, 'lname': lname, 'role': role, 'mail': mail})
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'

        if role != 'head_of_department':
            pass
        else:
            mongo.db.users.insert_one(
                {'fnumber': fnumber, 'username': username, 'password': password.decode('utf-8'), 'role': role})
            mongo.db.heads_of_departments.insert_one(
                {'fnumber': fnumber, 'fname': fname, 'lname': lname, 'role': role, 'department': department, 'mail': mail})
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'

        if role != 'head_of_department2':
            pass
        else:
            mongo.db.users.insert_one(
                {'fnumber': fnumber, 'username': username, 'password': password.decode('utf-8'), 'role': role})
            mongo.db.heads_of_departments.insert_one(
                {'fnumber': fnumber, 'fname': fname, 'lname': lname, 'role': role, 'department': department, 'mail': mail})
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'

        if role != 'project_manager':
            pass
        else:
            mongo.db.users.insert_one(
                {'fnumber': fnumber, 'username': username, 'password': password.decode('utf-8'), 'role': role})
            mongo.db.project_managers.insert_one(
                {'fnumber': fnumber, 'fname': fname, 'lname': lname, 'role': role, 'department': department, 'mail': mail, 'students': {}})
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'

        if role != 'reviewer':
            pass
        else:
            mongo.db.users.insert_one(
                {'fnumber': fnumber, 'username': username, 'password': password.decode('utf-8'), 'role': role})
            mongo.db.reviewers.insert_one(
                {'fnumber': fnumber, 'fname': fname, 'lname': lname, 'role': role, 'department': department, 'mail': mail, 'students': {}})
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'

    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))
    return render_template('admin_tea_add.html')


@app.route('/admin_tea_del', methods=['GET', 'DELETE'])
def admin_tea_del():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if request.method == "DELETE" and session['role'] == 'admin':
        data = json.loads(request.data)
        fnumber = data['fnumber']

        try:
            teacher = mongo.db.users.find_one({"fnumber": fnumber})
        except:
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

        if teacher["role"] == 'dean':
            try:
                mongo.db.users.remove({"fnumber": fnumber})
                mongo.db.dean.remove({"fnumber": fnumber})
                return "Преподавателят" + " " + fnumber + " " + "е премахнат успешно!"
            except:
                return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
        if teacher["role"] == 'head_of_department':
            try:
                mongo.db.users.remove({"fnumber": fnumber})
                mongo.db.heads_of_departments.remove({"fnumber": fnumber})
                return "Преподавателят" + " " + fnumber + " " + "е премахнат успешно!"
            except:
                return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

        if teacher["role"] == 'head_of_department*':
            try:
                mongo.db.users.remove({"fnumber": fnumber})
                mongo.db.heads_of_departments.remove({"fnumber": fnumber})
                return "Преподавателят" + " " + fnumber + " " + "е премахнат успешно!"
            except:
                return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

        if teacher["role"] == 'project_manager':
            try:
                mongo.db.users.remove({"fnumber": fnumber})
                mongo.db.project_managers.remove({"fnumber": fnumber})
                return "Преподавателят" + " " + fnumber + " " + "е премахнат успешно!"
            except:
                return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

        if teacher["role"] == 'reviewer':
            try:
                mongo.db.users.remove({"fnumber": fnumber})
                mongo.db.reviewers.remove({"fnumber": fnumber})
                return "Преподавателят" + " " + fnumber + " " + "е премахнат успешно!"
            except:
                return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

    return render_template('admin_tea_del.html')


@app.route('/admin_adm_search', methods=['POST', 'GET'])
def admin_adm_search():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if request.method == "POST":
        data = json.loads(request.data)
        username = data['username']
        admin = mongo.db.users.find_one({"username": username})
        if admin:
            return "Записът" + " " + admin["username"] + " " + "съществува!"
        else:
            return "Записът не съществува!"

    return render_template('admin_adm_search.html')


@app.route('/admin_adm_add', methods=['POST', 'GET'])
def admin_adm_add():
    if request.method == "POST" and session['role'] == 'admin':
        data = json.loads(request.data)
        username = data['username']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), salt)

        try:
            mongo.db.users.insert_one(
                {'username': username, 'password': password.decode('utf-8'), 'role': 'admin', 'lastlogin': ''})
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'
        except NameError:
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>' + str(
                NameError)

    if request.method == "POST":
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        redirect(url_for('index', error=error))
    return render_template('admin_adm_add.html')


@app.route('/admin_adm_del', methods=['GET', 'DELETE'])
def admin_adm_del():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))
    if request.method == "DELETE" and session['role'] == 'admin':
        data = json.loads(request.data)
        username = data['username']
        try:
            mongo.db.users.remove({"username": username})
            return "Администратор" + " " + username + " " + "е премахнат успешно!"
        except:
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

    return render_template('admin_adm_del.html')

@app.route('/student_main')
def student_main():
    if not session.get('role') or session['role'] != 'student':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))
    data = dict()
    data['username'] = session['username']


    return render_template('student_main.html', data=data)


@app.route('/student_diplom_project')
def student_diplom_project():
    if not session.get('role') or session['role'] != 'student':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))


    return render_template('student_diplom_project.html')

@app.route('/student_prof_change')
def student_prof_change():
    if not session.get('role') or session['role'] != 'student':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))


    return render_template('student_prof_change.html')


@app.route('/dean_main')
def dean_main():
    if not session.get('role') or session['role'] != 'dean':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))
    data = dict()
    data['username'] = session['username']


    return render_template('dean_main.html', data=data)

@app.route('/head_of_department_main')
def head_of_department_main():
    if not session.get('role') or session['role'] != 'head_of_department':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))
    data = dict()
    data['username'] = session['username']


    return render_template('head_of_department_main.html', data=data)

@app.route('/head_of_department2_main')
def head_of_department2_main():
    if not session.get('role') or session['role'] != 'head_of_department2':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))
    data = dict()
    data['username'] = session['username']


    return render_template('head_of_department2_main.html', data=data)

@app.route('/project_manager_main')
def project_manager_main():
    if not session.get('role') or session['role'] != 'project_manager':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))
    data = dict()
    data['username'] = session['username']


    return render_template('project_manager_main.html', data=data)

@app.route('/reviewer_main')
def reviewer_main():
    if not session.get('role') or session['role'] != 'reviewer':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))
    data = dict()
    data['username'] = session['username']


    return render_template('reviewer_main.html', data=data)

@app.route('/logout')
def logout():
    if session['role'] == 'admin':
        logger.info('Administrator' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    elif session['role'] == 'student':
        logger.info('Student' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    elif session['role'] == 'dean':
        logger.info('Dean' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    elif session['role'] == 'head_of_department':
        logger.info('Head_of_department' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    elif session['role'] == 'head_of_departmen2':
        logger.info('Head_of_department2' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    elif session['role'] == 'project_manager':
        logger.info('Project_manager' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    elif session['role'] == 'reviewer':
        logger.info('Reviewer' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    session.pop('role', None)
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    context = ('/home/angel/Desktop/webapp/flask/cert/server.crt', '/home/angel/Desktop/webapp/flask/cert/server.key')
    app.run(debug=True, ssl_context=context)
