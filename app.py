from flask import Flask, render_template, redirect, request, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from BD.models import Users, Subscription, db
from datetime import datetime

app = Flask(__name__)


app.secret_key = '12345'
username = "RGZ"
host_ip = "127.0.0.1"
host_port = "5432"
database_name = "rpp2_RGZ"
password = "12345"

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{username}:{password}@{host_ip}:{host_port}/{database_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


#создание таблиц по пользовательским моделям
# with app.app_context():
#     db.create_all() 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' #направление пользователя, если он не авторизован


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

#Переход на страницу с подписками после авторизации
@app.route('/')
@login_required
def index():
    return redirect(url_for('subscriptions')) 


#Страница авторизации
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        user = Users.query.filter_by(name=name).first()
        if not user:
            return render_template('login.html', error="Пользователь не найден!")

        if not check_password_hash(user.password, password):
            return render_template('login.html', error="Пароль введён некорректно!")

        login_user(user)
        return redirect('/') 


#Страница регистрации
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        

        existing_user = Users.query.filter_by(name=name).first()
        if existing_user:
            return render_template('signup.html', error="Пользователь уже существует")

        new_user = Users(name=name, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')


@app.route('/subscriptions', methods=['GET'])
@login_required
def subscriptions():
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
    return render_template('subscriptions.html', subscriptions=subscriptions)


@app.route('/create_subscription', methods=['POST'])
@login_required
def create_subscription():
    name = request.form['name']
    amount = float(request.form['amount'])
    frequency = request.form['frequency']
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    
    # Создание новой подписки
    new_subscription = Subscription(
        name=name,
        amount=amount,
        frequency=frequency,
        start_date=start_date,
        user_id=current_user.id
    )
    db.session.add(new_subscription)
    db.session.commit()
    
    return redirect(url_for('subscriptions'))


@app.route('/edit_subscription/<int:sub_id>', methods=['GET', 'POST'])
@login_required
def edit_subscription(sub_id):
    subscription = Subscription.query.get(sub_id)

    # Проверяем, что подписка принадлежит текущему пользователю
    if subscription is None or subscription.user_id != current_user.id:
        return redirect(url_for('subscriptions'))

    if request.method == 'POST':
        # Обновление полей подписки
        subscription.name = request.form['name']
        subscription.amount = float(request.form['amount'])
        subscription.frequency = request.form['frequency']
        subscription.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()

        db.session.commit()
        return redirect(url_for('subscriptions'))

    # Отправка текущих данных подписки на страницу редактирования
    return render_template('edit_subscription.html', subscription=subscription)


@app.route('/delete_subscription/<int:sub_id>', methods=['POST'])
@login_required
def delete_subscription(sub_id):
    subscription = Subscription.query.get(sub_id)
    if subscription and subscription.user_id == current_user.id:
        db.session.delete(subscription)
        db.session.commit()
    return redirect(url_for('subscriptions'))


#Выход из приложения
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


if __name__ == '__main__':
    app.run()
