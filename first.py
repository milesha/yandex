from flask import redirect, render_template, Flask, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class YandexLyceumStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    surname = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    group = db.Column(db.String(80), unique=False, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)

    def __repr__(self):
        return '<YandexLyceumStudent {} {} {} {}>'.format(
            self.id, self.username, self.name, self.surname)


class SolutionAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(80), unique=False, nullable=False)
    code = db.Column(db.String(1000), unique=False, nullable=False)
    status = db.Column(db.String(50), unique=False, nullable=False)
    student_id = db.Column(db.Integer,
                           db.ForeignKey('yandex_lyceum_student.id'),
                           nullable=False)
    student = db.relationship('YandexLyceumStudent',
                              backref=db.backref('SolutionAttempts',
                                                 lazy=True))

    def __repr__(self):
        return '{}%504);{}%504);{}%504);{}%504);{}'.format(self.student_id, self.task, self.code, self.status, self.id)


db.create_all()
session = {}
users = []


class AddSolutionsForm(FlaskForm):
    title = StringField('Номер или название задачи', validators=[DataRequired()])
    content = TextAreaField('Ваше решение', validators=[DataRequired()])
    submit = SubmitField('Отправить')


@app.route('/change_status_wrong/<n>', methods=['GET', 'POST'])
def change_status_wrong(n):
    print(n)
    q = db.session.query(SolutionAttempt)
    q = q.filter(SolutionAttempt.id == int(n))
    print(q, q.all())
    record = q.first()
    print(record, q.all())
    record.status = 'WA'
    db.session.commit()
    return redirect('/')


@app.route('/change_status_ok/<n>', methods=['GET', 'POST'])
def change_status_ok(n):
    print(n)
    q = db.session.query(SolutionAttempt)
    q = q.filter(SolutionAttempt.id == int(n))
    print(q, q.all())
    record = q.first()
    print(record, q.all())
    record.status = 'OK'
    db.session.commit()
    return redirect('/')


@app.route('/add_solutions', methods=['GET', 'POST'])
def add_solutions():
    if 'username' not in session:
        return redirect('/login')
    form = AddSolutionsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        print(session)
        user = YandexLyceumStudent.query.filter_by(username=session['username']).first()
        attempt = SolutionAttempt(task=title,
                                  code=content,
                                  status='На проверке')
        user.SolutionAttempts.append(attempt)
        db.session.commit()
        return redirect("/index")
    return render_template('add_solutions.html', title='Отправка решения',
                           form=form, username=session['username'])


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect('/login')
    all_solves = SolutionAttempt.query.filter_by(student_id=session['user_id']).all()
    solutions = []
    print(all_solves)
    for i in all_solves:
        solutions.append(list(str(i).split('%504);')))
    print(session, solutions, all_solves)
    if 0 == session['user_id']:
        # return 'admin'
        users_list = []
        print(YandexLyceumStudent.query.all())
        for i in YandexLyceumStudent.query.all():
            users_list.append(list(str(i).replace('>', '').split()))
            # users_list[-1][1] = int(users_list[-1][1])
        print(users_list)
        solutions_list = []
        print(SolutionAttempt.query.all())
        for i in SolutionAttempt.query.all():
            solutions_list.append(list(str(i).split("%504);")))
        print(solutions_list)
        return render_template('admin.html', username=session['username'],
                               users=users_list, news=solutions_list)
    else:
        return render_template('index.html', username=session['username'],
                               solutions=solutions)


@app.route('/logout')
def logout():
    session.pop('username', 0)
    session.pop('user_id', 0)
    return redirect('/login')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    mail = StringField('Почта', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    group = StringField('Город и школа', validators=[DataRequired()])
    year = StringField('Год обучения', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if request.method == 'POST':
        user = YandexLyceumStudent(username=form.username.data,
                                   email=form.mail.data,
                                   name=form.name.data,
                                   surname=form.surname.data,
                                   group=form.group.data,
                                   year=int(form.year.data))
        db.session.add(user)
        db.session.commit()
        return redirect("/index")
    return render_template('registration.html', title='Регистрация', form=form)


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    submit = SubmitField('Войти')


d = []
admin_name, admin_pass, user_id = 'kirill', 'slezin', 0


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = form.username.data
        name = form.name.data
        surname = form.surname.data
        exists = [False, ]
        find_person = YandexLyceumStudent.query.filter_by(username=username, name=name, surname=surname).first()
        if find_person:
            exists = [True, int(str(find_person).split()[1])]
        elif name == 'kirill' and surname == 'slezin' and username == 'kirill':
            exists = [True, 0]

        if exists[0]:
            session['username'] = username
            session['user_id'] = exists[1]
            return redirect("/index")
        return 'Данного пользователя не существует'
    return render_template('login.html', title='Авторизация', form=form)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
