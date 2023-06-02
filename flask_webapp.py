from env import *
from datetime import datetime, timedelta
import jwt
from flask_table import Table, Col, create_table


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
    user = User.objects(email=email).first()
    if user:
        token = jwt.encode({'public_id': user.id, 'exp': datetime.utcnow() + timedelta(minutes=10)},
                           app.config['SECRET_KEY'], "HS256")
        msg = Message()
        msg.subject = "Password Reset"
        msg.sender = 'isudp@abv.bg'
        msg.recipients = [email]
        msg.html = render_template('reset_email.html', token=token)
        mail.send(msg)
        print('Email sent')
        error = 'Моля проверете Вашата поща!'
        return redirect(url_for('index', error=error))

    error = "Грешен имейл адрес!"
    return redirect(url_for('psw_reset_view', error=error))


@app.route("/password_reset_verified/<token>", methods=['GET', 'POST'])
def reset_verified(token):
    if request.method == "POST":
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        current_user = User.objects(id=data['public_id']).first()
        if not current_user:
            flash('Невалиден токен!')
            return redirect(url_for('index'))
        data = json.loads(request.data)
        if current_user.update_password(password=data['password']):
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна промяна на парола!<p>'
        return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

    return render_template('reset_psw.html')


@app.route("/login", methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.objects(username=username).first()
    if not user:
        error = "Грешно потребителско име!"
        return redirect(url_for('index', error=error))
    authorized = user.check_password(password)
    if not authorized:
        error = 'Грешна парола!'
        return redirect(url_for('index', error=error))

    session['role'] = user.role
    session['username'] = user.username
    session['email'] = user.email
    logger.info(user.role + ' ' + user.username + ' ' + 'was loged in the system!')
    return redirect(session['role'] + '_main')


@app.route('/admin_main')
def admin_main():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))
    count_usr = User.objects.count()
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
        password = data['password']
        current_user = User.objects(email=session['email']).first()
        if current_user.change_profile_data(username=username, password=password):
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна промяна!</p>'
        return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
    return render_template('admin_prof_change.html')


@app.route('/admin_stu_search', methods=['GET', 'POST'])
def admin_stu_search():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if request.method == "POST":

        data = json.loads(request.data)
        fnumber = data['fnumber']
        student = Admin.search_student(fnumber=fnumber)
        if student:
            return "<table id='stu_info'>" + "<tr><td>Ф.номер:</td><td>" + \
                student['fnumber'] + "</td></tr><tr><td>Име:</td><td>" + \
                student['fname'] + "</td></tr><tr><td>Фамилия:</td><td>" + \
                student['lname'] + "</td></tr><tr><td>Катедра:</td><td>" + \
                student['department'] + "</td></tr><tr><td>Специалност:</td><td>" + \
                student['spec'] + "</td></tr></table>"
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
        email = data['mail']
        username = data['username']
        password = data['password']
        if not Admin.add_new_student(username, password, fnumber, fname, lname, department, email):
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
        return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'
    if request.method == "POST":
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    return render_template('admin_stu_add.html')


# Da se triqt samo po Email user i dr!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@app.route('/admin_stu_del', methods=['GET', 'DELETE'])
def admin_stu_del():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if request.method == "DELETE" and session['role'] == 'admin':
        data = json.loads(request.data)
        fnumber = data['fnumber']
        email = data['email']
        if Admin.delete_student(fnumber, email):
            return "Студентът" + " " + fnumber + " " + "е премахнат успешно!"
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
        email = data['email']
        teacher = Admin.search_teacher(fnumber=fnumber, email=email)
        if teacher:
            return "Записът" + " " + teacher['fname'] + " " + teacher['lname'] + " " + "съществува!"
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
        email = data['mail']
        username = data['username']
        password = data['password']
        if role == 'dean':
            if Admin.add_new_dean(username=username, password=password,
                                  fnumber=fnumber, fname=fname, lname=lname,
                                  email=email):
                return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
        if role == 'head_of_department2' or role == 'head_of_department':
            if Admin.add_new_department_head(username=username, password=password,
                                             fnumber=fnumber, fname=fname, lname=lname, role=role,
                                             department=department, email=email):
                return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
        if role == 'project_manager':
            if Admin.add_new_proj_mngr(username=username, password=password,
                                       fnumber=fnumber, fname=fname, lname=lname,
                                       department=department,
                                       email=email):
                return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
        if role == 'reviewer':
            if Admin.add_new_reviewer(username=username, password=password,
                                      fnumber=fnumber, fname=fname, lname=lname,
                                      department=department,
                                      email=email):
                return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'
            return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
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
        if Admin.delete_teacher(fnumber=data['fnumber'], email=data['email']):
            return "Преподавателят" + " " + data['fnumber'] + " " + "е премахнат успешно!"
        return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
    return render_template('admin_tea_del.html')


@app.route('/admin_adm_search', methods=['POST', 'GET'])
def admin_adm_search():
    if not session.get('role') or session['role'] != 'admin':
        error = "Не сте влезли или не сте администратор!"
        return redirect(url_for('index', error=error))

    if request.method == "POST":
        data = json.loads(request.data)
        admin = Admin.search_admin(username=data['username'])
        if admin:
            return "Записът" + " " + admin["username"] + " " + "съществува!"
        else:
            return "Записът не съществува!"
    return render_template('admin_adm_search.html')


@app.route('/admin_adm_add', methods=['POST', 'GET'])
def admin_adm_add():
    if request.method == "POST" and session['role'] == 'admin':
        data = json.loads(request.data)
        if Admin.add_new_admin(username=data['username'], password=data['password'], email=data['email']):
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна регистрация!</p>'
        return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
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
        if Admin.delete_admin(username=data['username']):
            return "Администратор" + " " + data['username'] + " " + "е премахнат успешно!"
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
    data = Student.diploma_data(session['email'])
    return render_template('student_diplom_project.html', data=data)


@app.route('/student_diplom_project_upload', methods=['POST'])
def student_diplom_project_upload():
    if not session.get('role') or session['role'] != 'student':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))
    file = request.files['file']
    Student.upload_diploma_project(session['email'], file)
    return 'Успешно качен файл!'


@app.route('/student_diplom_project_download')
def student_diplom_project_download():
    if not session.get('role') or session['role'] != 'student':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))
    return Student.download_diploma_project(session['email'])


@app.route('/student_prof_change', methods=['GET', 'POST'])
def student_prof_change():
    if not session.get('role') or session['role'] != 'student':
        error = "Не сте влезли или не сте студент!"
        return redirect(url_for('index', error=error))

    if request.method == "POST" and session['role'] == 'student':
        data = json.loads(request.data)
        username = data['username']
        password = data['password']
        current_user = User.objects(email=session['email']).first()
        if current_user.change_profile_data(username, password):
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна промяна!</p>'
        return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'
    return render_template('student_prof_change.html')


@app.route('/dean_main')
def dean_main():
    if not session.get('role') or session['role'] != 'dean':
        error = "Не сте влезли или не сте декан!"
        return redirect(url_for('index', error=error))
    data = dict()
    data['username'] = session['username']

    return render_template('dean_main.html', data=data)


@app.route('/dean_references')
def dean_references():
    if not session.get('role') or session['role'] != 'dean':
        error = "Не сте влезли или не сте декан!"
        return redirect(url_for('index', error=error))
    return render_template('dean_references.html')


@app.route('/dean_references_download/<option>')
def dean_references_download(option):
    if not session.get('role') or session['role'] != 'dean':
        error = "Не сте влезли или не сте декан!"
        return redirect(url_for('index', error=error))

    file, filePath = Dean.download_references(option)
    response = make_response(file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=' + filePath
    return response


@app.route('/dean_prof_change')
def dean_prof_change():
    if not session.get('role') or session['role'] != 'dean':
        error = "Не сте влезли или не сте декан!"
        return redirect(url_for('index', error=error))

    if request.method == "POST" and session['role'] == 'dean':
        data = json.loads(request.data)
        username = data['username']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
        current_user = User.objects(email=session['email']).first()
        if current_user.change_profile_data(username, password):
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна промяна!</p>'
        return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

    return render_template('dean_prof_change.html')


@app.route('/head_of_department_main')
def head_of_department_main():
    if not session.get('role') or session['role'] != 'head_of_department':
        error = "Не сте влезли или не сте ръководител на катедра!"
        return redirect(url_for('index', error=error))
    data = dict()
    data['username'] = session['username']

    return render_template('head_of_department_main.html', data=data)


@app.route('/head_of_department_prof_change')
def head_of_department_prof_change():
    if not session.get('role') or session['role'] != 'head_of_department':
        error = "Не сте влезли или не сте ръководител на катедра!"
        return redirect(url_for('index', error=error))

    if request.method == "POST" and session['role'] == 'head_of_department':
        data = json.loads(request.data)
        username = data['username']
        password = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
        current_user = User.objects(email=session['email']).first()
        if current_user.change_profile_data(username, password):
            return '<p style="size:20px;color:white;margin-left:15px;">Успешна промяна!</p>'
        return '<p style="size:20px;color:white;margin-left:15px;">Възникна проблем с базата данни!<p>'

    return render_template('head_of_department_prof_change.html')


@app.route('/head_of_department_references')
def head_of_department_references():
    if not session.get('role') or session['role'] != 'head_of_department':
        error = "Не сте влезли или не сте ръководител на катедра!"
        return redirect(url_for('index', error=error))
    current_hd = DepartmentHead.objects(email=session['email']).first()
    data = dict()
    data['department'] = current_hd.department

    return render_template('head_of_department_references.html', data=data)


@app.route('/head_of_department_references_download/<option>')
def head_of_department_references_download(option):
    if not session.get('role') or session['role'] != 'head_of_department':
        error = "Не сте влезли или не сте ръководител на катедра!"
        return redirect(url_for('index', error=error))
    file, filePath = DepartmentHead.download_references(option)
    response = make_response(file)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=' + filePath
    return response


@app.route('/head_of_department/set-managers_student')
def head_of_department_set_managers_student():
    if not session.get('role') or session['role'] != 'head_of_department':
        error = "Не сте влезли или не сте ръководител на катедра!"
        return redirect(url_for('index', error=error))

    return render_template('head_of_department_set-managers_student.html')


@app.route('/head_of_department/student_search', methods=['POST'])
def head_of_department_student_search():
    if not session.get('role') or session['role'] != 'head_of_department':
        error = "Не сте влезли или не сте ръководител на катедра!"
        return redirect(url_for('index', error=error))
    self = DepartmentHead.objects(email=session['email']).first()
    data = json.loads(request.data)
    fnumber = data['fnumber']
    student = self.search_student(fnumber)
    if student:
        TableCls = create_table() \
            .add_column('name', Col('')) \
            .add_column('description', Col(''))
        items = [dict(name='Ф.номер', description=student['fnumber']),
                 dict(name='Име', description=student['fname']),
                 dict(name='Фамилия', description=student['lname']),
                 dict(name='Ръководител', description=student['project_manager']),
                 dict(name='Рецензент', description=student['reviewer'])]
        table = TableCls(items)
        return table.__html__()
    return 'Несъществуващ студент!'

@app.route('/head_of_department/teacher_search', methods=['POST'])
def head_of_department_teacher_search():
    if not session.get('role') or session['role'] != 'head_of_department':
        error = "Не сте влезли или не сте ръководител на катедра!"
        return redirect(url_for('index', error=error))
    self = DepartmentHead.objects(email=session['email']).first()
    proj_mngrs, reviewers = self.search_teachers()
    output = []
    for item in proj_mngrs:
        output.append({'fname': item.fname, 'lname': item.lname})
    json_data = json.dumps(output)
    return json_data


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
    elif session['role'] == 'head_of_department2':
        logger.info('Head_of_department*' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    elif session['role'] == 'project_manager':
        logger.info('Project_manager' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    elif session['role'] == 'reviewer':
        logger.info('Reviewer' + ' ' + session['username'] + ' ' + 'was loged out the system!')
    session.pop('role', None)
    session.pop('username', None)
    session.pop('email', None)

    return redirect(url_for('index'))


if __name__ == "__main__":
    context = ('/home/angel/Desktop/webapp/flask/cert/server.crt', '/home/angel/Desktop/webapp/flask/cert/server.key')
    app.run(debug=True, ssl_context=context)
