
from flask_restful import reqparse, abort, Api, Resource
import sqlite3
from flask import redirect, render_template, Flask, request, jsonify, make_response, Response, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField
import json
from wtforms.validators import DataRequired
from requests import get, post, delete, put

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


class DB:
    def __init__(self):
        conn = sqlite3.connect('news.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class UsersModel:
    def __init__(self, connection):
        self.connection = connection
        self.init_table()

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128))''')
        cursor.close()
        self.connection.commit()

    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (user_name, password_hash) 
                          VALUES (?,?)''', (user_name, password_hash))
        cursor.close()
        self.connection.commit()

    def delete(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM users WHERE id = ?''', [user_id])
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", [user_id])
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)

    def change(self, user_id, new_username, new_password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''UPDATE users SET user_name = ? WHERE id = ?''', (new_username, str(user_id)))
        cursor.execute('''UPDATE users SET password_hash = ? WHERE id = ?''', (new_password_hash, str(user_id)))
        cursor.close()
        self.connection.commit()


class NewsModel:
    def __init__(self, connection):
        self.connection = connection
        self.init_table()

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS news 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             content VARCHAR(1000),
                             user_id INTEGER
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, content, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO news 
                          (title, content, user_id) 
                          VALUES (?,?,?)''', (title, content, str(user_id),))
        cursor.close()
        self.connection.commit()

    def get(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM news WHERE id = ? ORDER BY title, content, id", (str(news_id),))
        row = cursor.fetchone()
        return row

    def get_all(self, user_id=None):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM news WHERE user_id = ? ORDER BY title, content, id",
                           (str(user_id),))
        else:
            cursor.execute("SELECT * FROM news ORDER BY title, content, id")
        rows = cursor.fetchall()
        return rows

    def delete(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM news WHERE id = ?''', (str(news_id),))
        cursor.close()
        self.connection.commit()

    def change(self, news_id, new_content, new_title):
        cursor = self.connection.cursor()
        cursor.execute('''UPDATE news SET title = ? WHERE id = ?''', (new_title, str(news_id)))
        cursor.execute('''UPDATE news SET content = ? WHERE id = ?''', (new_content, str(news_id)))
        cursor.close()
        self.connection.commit()


session = {}
db = DB()


def abort_if_news_not_found(news_id):
    if not NewsModel(db.get_connection()).get(news_id):
        img = url_for('static', filename='img/404-image.png')
        resp = Response("<img src='{}'>".format(img), mimetype='text/html')
        resp.status_code = 200
        return resp


@app.route('/delete_news/<news_id>', methods=['GET', 'DELETE'])
def delete_news(news_id):
    delete('http://localhost:8080/news/' + news_id)
    return redirect('/news')


class News(Resource):
    def get(self, news_id):
        if 'user_id' in session:
            x = abort_if_news_not_found(news_id)
            if x:
                return x
            news = NewsModel(db.get_connection()).get(news_id)
            resp = Response(render_template('show_chosen_news.html', item=news), mimetype='text/html')
            resp.status_code = 200
            return resp
        return redirect("/")

    def delete(self, news_id):
        x = abort_if_news_not_found(news_id)
        if x:
            return x
        NewsModel(db.get_connection()).delete(news_id)
        return jsonify({'success': 'OK'})


parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)


class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class NewsList(Resource):
    def get(self):
        news = NewsModel(db.get_connection()).get_all()
        print(news)
        form = AddNewsForm()
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            post('http://localhost:8080/news',
                 json={'title': title,
                       'content': content}).json()
            return redirect('/news')
        text = 'Войдите, чтобы добавлять и удалять новости'
        if 'user_id' in session:
            text = 'Привет, ' + session['username'] + '!'
        resp = Response(render_template('show_news_list.html', news=news, form=form, text=text), mimetype='text/html')
        resp.status_code = 200
        return resp

    def post(self):
        args = parser.parse_args()
        news = NewsModel(db.get_connection())
        if 'user_id' in session:
            news.insert(args['title'], args['content'], session['user_id'])
            return redirect('/news')
        return redirect('/')


api.add_resource(NewsList, '/news')  # для списка объектов
api.add_resource(News, '/news/<int:news_id>')  # для одного объекта


def abort_if_user_not_found(user_id):
    if not UsersModel(db.get_connection()).get(user_id):
        img = url_for('static', filename='img/404-image.png')
        resp = Response("<img src='{}'>".format(img), mimetype='text/html')
        resp.status_code = 200
        return resp


class Users(Resource):
    def get(self, user_id):
        x = abort_if_user_not_found(user_id)
        if x:
            return x
        users = UsersModel(db.get_connection()).get(user_id)
        return jsonify({'users': users})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        UsersModel(db.get_connection()).delete(user_id)
        return jsonify({'success': 'OK'})

    def put(self, user_id):
        args = parser_users.parse_args()
        abort_if_user_not_found(user_id)
        users = UsersModel(db.get_connection())
        users.change(user_id, args['user_name'], args['password_hash'])
        return jsonify({'success': 'OK'})


parser_users = reqparse.RequestParser()
parser_users.add_argument('user_name', required=True)
parser_users.add_argument('password_hash', required=True)

parser_users_change = reqparse.RequestParser()
parser_users_change.add_argument('user_id', required=True, type=int)
parser_users_change.add_argument('user_name', required=True)
parser_users_change.add_argument('password_hash', required=True)


class UsersList(Resource):
    def get(self):
        users = UsersModel(db.get_connection()).get_all()
        resp = Response(render_template('show_users_list.html', users=users), mimetype='text/html')
        resp.status_code = 200
        return resp

    def post(self):
        args = parser_users.parse_args()
        users = UsersModel(db.get_connection())
        users.insert(args['user_name'], args['password_hash'])
        return jsonify({'success': 'OK'})


api.add_resource(UsersList, '/users')  # для списка объектов
api.add_resource(Users, '/users/<int:user_id>')  # для одного объекта


@app.route('/logout')
def logout():
    session.pop('username', 0)
    session.pop('user_id', 0)
    return redirect('/')


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


d = []


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        user_name = form.username.data
        password = form.password.data
        user_model = UsersModel(db.get_connection())
        user_model.insert('kirill', 'slezin')
        exists = user_model.exists(user_name, password)
        print(exists, user_name, password, session)
        if exists[0]:
            session['username'] = user_name
            session['user_id'] = exists[1]
        print('username' in session, session)
        return redirect("/news")
    return render_template('login.html', title='Авторизация', form=form)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')