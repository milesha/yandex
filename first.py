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

    def __repr__(self):
        return '<Worker {} {} {} {}>'.format(
            self.id, self.username, self.name, self.surname)


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
                             backref=db.backref('SolutionAttempts',
                                                lazy=True))

    def __repr__(self):
        return '{}%504);{}%504);{}%504);{}%504);{}'.format(self.worker_id, self.tasktext, self.description, self.status,
                                                           self.id)


db.create_all()
session = {}
users = []


class AddSolutionsForm(FlaskForm):
    title = StringField('Название задачи', validators=[DataRequired()])
    content = TextAreaField('Описание', validators=[DataRequired()])
    date = StringField('Дата выполнения', validators=[DataRequired()])
    author = StringField('Автор задачи', validators=[DataRequired()])
    submit = SubmitField('Отправить')


@app.route('/add_solutions', methods=['GET', 'POST'])
def add_solutions():
    if 'username' not in session:
        return redirect('/login')
    form = AddSolutionsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        print(session)
        user = Worker.query.filter_by(username=session['username']).first()
        attempt = Tasks(task=title,
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
    return render_template('index.html', username=session['username'])


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
                      password=form.password.data)
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
