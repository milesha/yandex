from flask import redirect, render_template, Flask, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from flask_sqlalchemy import SQLAlchemy
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    surname = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    is_admin = db.Column(db.Integer)

    def __repr__(self):
        return '<Worker {} {} {} {} {}>'.format(
            self.id, self.username, self.name, self.surname, self.is_admin)


class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tasktext = db.Column(db.String(80), unique=False, nullable=False)
    description = db.Column(db.String(1000), unique=False, nullable=False)
    date = db.Column(db.String(1000), unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=False)
    worker_id = db.Column(db.Integer,
                          db.ForeignKey('worker.id'),
                          nullable=False)
    worker = db.relationship('Worker',
                             backref=db.backref('Tasks',
                                                lazy=True))

    def __repr__(self):
        return 'Tasks {} {} {} {} {}'.format(self.id, self.tasktext, self.description,
                                             self.date, self.status)


db.create_all()
session = {}

if 'Admin' not in [i.username for i in Worker.query.all()]:
    user_admin = Worker(username='Admin',
                        email='Admin@mail.ru',
                        name='Admin',
                        surname='Admin',
                        password='admin',
                        is_admin=1)
    db.session.add(user_admin)
    db.session.commit()

users = []


class AddSolutionsForm(FlaskForm):
    title = StringField('Название задачи', validators=[DataRequired()])
    content = TextAreaField('Описание', validators=[DataRequired()])
    date = StringField('Дата выполнения', validators=[DataRequired()])
    author = StringField('Автор задачи', validators=[DataRequired()])
    submit = SubmitField('Отправить')


@app.route('/create_admin/<s>', methods=['GET', 'POST'])
def create_admin(s):
    user = Worker.query.filter_by(username=s).first()
    user.is_admin = 1
    db.session.commit()
    return redirect('/index')
    #Worker.query.filter_by(username=s).delete()


@app.route('/add_solutions', methods=['GET', 'POST'])
def add_solutions():
    if 'username' not in session:
        return redirect('/login')
    form = AddSolutionsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        date, author = form.date.data, form.author.data
        print(session)
        attempt = Tasks(tasktext=title,
                        description=content,
                        date=date,
                        status=2,
                        worker_id=session['user_id'])
        db.session.add(attempt)
        db.session.commit()
        return redirect("/index")
    return render_template('add_solutions.html', title='Отправка решения',
                           form=form, username=session['username'])


@app.route('/change_solutions', methods=['GET', 'POST'])
def change_solutions():
    if 'username' not in session:
        return redirect('/login')
    form = AddSolutionsForm()
    if form.validate_on_submit():
        title = form.title.data
        u_id = -1
        for i in Tasks.query.all():
            if i.tasktext == title:
                u_id = i.worker_id
        if u_id == -1:
            flash('Такой задачи не существует')
        elif session['user_id'] != u_id:
            flash('Эта задача не ваша')
        else:
            content = form.content.data
            date, author = form.date.data, form.author.data
            print(session)
            attempt = Tasks(tasktext=title,
                            description=content,
                            date=date,
                            status=2,
                            worker_id=session['user_id'])
            Tasks.query.filter_by(tasktext=title).delete()
            db.session.add(attempt)
            db.session.commit()
            return redirect("/index")
    return render_template('add_solutions.html', title='Создание задачи',
                           form=form, username=session['username'])


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        is_admin = 0
        for i in Worker.query.all():
            if i.username == session['username']:
                is_admin = i.is_admin
        if is_admin:
            users_list = []
            print(Worker.query.all())
            for i in Worker.query.all():
                users_list.append(list(str(i).replace('>', '').split()))
            return render_template('admin.html', users=users_list)
        return render_template('index.html', username=session['username'], session=session)
    return render_template('index.html', session='')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    mail = StringField('Почта', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


@app.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegistrationForm()
    if request.method == 'POST':
        user = Worker(username=form.username.data,
                      email=form.mail.data,
                      name=form.name.data,
                      surname=form.surname.data,
                      password=form.password.data,
                      is_admin=0)
        if form.username.data in [i.username for i in Worker.query.all()]:
            flash('Пользователь с таким логином уже существует')
        elif form.password.data != form.password2.data:
            flash('Пароли не совпадают')
        else:
            try:
                db.session.add(user)
                db.session.commit()
                return render_template('successful_reg.html', title='Вы успешно зарегистрировались')
            except:
                flash('Пользователь с таким email существует')
    return render_template('registration.html', title='Регистрация', form=form)


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


d = []


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    global session
    session = {}
    return redirect('/index')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/index')
    print (session)
    form = LoginForm()
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data
        exists = [False, ]
        find_person = Worker.query.filter_by(username=username).first()
        if find_person:
            if find_person.password == password:
                exists = [True, int(find_person.id)]
            else:
                flash('Неправильный пароль')
                return render_template('login.html', title='Авторизация', form=form)
        if exists[0]:
            session['username'] = username
            session['user_id'] = exists[1]
            return redirect("/index")
        flash('Данного пользователя не существует')
    return render_template('login.html', title='Авторизация', form=form)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
