from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy, inspect

from flask_login import UserMixin, login_user, login_required, logout_user, LoginManager, login_manager, current_user
from sqlalchemy import engine
from werkzeug.security import generate_password_hash, check_password_hash
import contextlib
import MySQLdb
import requests
import django
import enchant
from django import template

local_server = True
app = Flask(__name__)
app.secret_key = 'BAAM'
# for getting unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'log_in'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/database_table_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/cresearch'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
# create db model
class Patients(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(50))
    gender = db.Column(db.String(50))
    # slot = db.Column(db.String(50))
    disease = db.Column(db.String(100))
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    dept = db.Column(db.String(50))
    pno = db.Column(db.Integer, nullable=False)
    # for test
    # id = db.Column(db.Integer, primary_key=True)
    # name = db.Column(db.String(100))

class Doctors(db.Model):
    did = db.Column(db.Integer, primary_key=True)
    doc_name = db.Column(db.String(30))
    email = db.Column(db.String(50))
    dept = db.Column(db.String(100))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))


@app.route('/test')
def hello():
    a = Patients.query.all()
    print(a)
    try:
        Patients.query.all()
        return "Database connected"
    except:
        return "Database not connected"

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/home')
def test():
    return "this home"

@app.route('/access')
def access():
    # flash("Logout Success", "danger")
    return render_template('access.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/patients', methods=['POST', 'GET'])
@login_required
def patients():
    doct = db.engine.execute(f"SELECT distinct `dept` FROM `doctors`")
    # for d in doct:
    #     print(d.did)
    #     print(d.doc_name)
    #     print(d.dept)
    if request.method == "POST":
        # pid = request.form.get('')
        name = request.form.get('name')
        email = request.form.get('email')
        gender = request.form.get('gender')
        # slot = request.form.get('slot')
        disease = request.form.get('disease')
        date = request.form.get('date')
        time = request.form.get('time')
        dept = request.form.get('dept')
        pno = request.form.get('pno')

        query = db.engine.execute(f"INSERT INTO `patients`(`email`, `name`, `gender`, `disease`, `date`,"
                                  f" `time`, `dept`, `pno`) VALUES ('{email}', '{name}', '{gender}', '{disease}', '{date}',"
                                  f" '{time}', '{dept}', '{pno}')")
        flash("Booking Confirmed", "info")

    # if not User.is_authenticated:
        # return render_template('login.html')
    return render_template('patients.html', doct=doct)


@app.route('/bookings', methods=['POST', 'GET'])
@login_required
def bookings():
    em = current_user.email
    qry = db.engine.execute(f"SELECT * FROM `patients` WHERE email = '{em}'")
    return render_template('booking.html', query=qry)


@app.route('/doctors', methods=['POST', 'GET'])
@login_required
def doctors():
    if request.method == "POST":
        # pid = request.form.get('')
        doc_name = request.form.get('doc_name')
        email = request.form.get('email')
        dept = request.form.get('dept')

        query = db.engine.execute(f"INSERT INTO `doctors`(`email`, `doc_name`, `dept`) VALUES ('{email}', '{doc_name}',"
                                  f" '{dept}')")
        flash("Information Stored", "info")

    return render_template("doctors.html")

@app.route("/edit/<string:pid>", methods=['POST', 'GET'])
@login_required
def edit(pid):
    doct = db.engine.execute(f"SELECT distinct `dept` FROM `doctors`")
    posts = Patients.query.filter_by(pid=pid).first()
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        gender = request.form.get('gender')
        # slot = request.form.get('slot')
        disease = request.form.get('disease')
        time = request.form.get('time')
        date = request.form.get('date')
        dept = request.form.get('dept')
        pno = request.form.get('pno')
        db.engine.execute(f"UPDATE `patients` SET `email` = '{email}', `name` = '{name}', `gender` = '{gender}', "
                          f"`disease` = '{disease}', `time` = '{time}', `date` = '{date}', `dept` = '{dept}',"
                          f" `pno` = '{pno}' WHERE `patients`.`pid` = {pid};")
        l = {"name": name, "email": email, "gender": gender, "disease": disease, "Date":date, "phone num":pno}
        file1 = open('myFile.txt', 'w')
        file1.write(str(l))
        flash("Update Successful", "primary")
        return redirect('/bookings')

    return render_template('edit.html', posts=posts, doct=doct)



@app.route('/login', methods=['POST', 'GET'])
def log_in():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Successful", "danger")
            return redirect(url_for('access'))
        else:
            flash("Incorrect username or password", "danger")
            return redirect(url_for('log_in'))
    return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists, please try with a different email", "danger")
            return render_template('signup.html')
        encpass = generate_password_hash(password)

        # method 1-
        new_user = db.engine.execute(f"INSERT INTO `user` (`username`, `email`, `password`) VALUES ('{username}' ,'{email}','{encpass}')")
        return render_template("login.html")

        # method 2-(not working)
        # newuser = User(username=username, email=email, password=encpass)
        # db.session(newuser)
        # db.session.commit()
    return render_template('signup.html')

@app.route('/logout')
@login_required
def log_out():
    logout_user()
    flash("Logout Successful", "danger")
    return redirect(url_for('log_in'))

@app.route("/delete/<string:pid>", methods=['POST', 'GET'])
@login_required
def delete(pid):
    db.engine.execute(f"DELETE FROM `patients` WHERE `pid`={pid}")
    flash("Slot Deleted Successfully", "danger")
    return redirect('/bookings')
@app.route("/download/<string:pid>", methods=['POST','GET'])
def download(pid):

    # file1.close()

    # USE BEAUTIFULSOUP TO COPY THE ROW OF DATA FROM THE HTML CODE (patients.html or booking.html) and write it to file


    # for row in contents:
    #     row_as_dict = dict(row)
    #     file1.write(str(row_as_dict))
    # conn = engine.connect()
    # rows = conn.execute(str(contents))
    # list_of_dicts = [{key: value for (key, value) in row.items()} for row in rows]
    return redirect(url_for('bookings'))


app.run(debug=True)
