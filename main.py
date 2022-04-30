# # (C)opyright 2021 Edward Francis Westfield Jr. | Standard MIT License
# # v0.1.1-alpha Revised April 2022 


PROJECT_TITLE = "BP Tracker"
YEAR_CREATED = 2021

import requests
from flask import Flask, render_template, redirect, request, url_for, flash, abort, Response
from flask_bootstrap import Bootstrap

from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import Column, Integer, DateTime, Date
from sqlalchemy.orm import relationship
import os
import re
from datetime import date, datetime

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException

from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from functools import wraps

from flask_ckeditor import CKEditor, CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, DateTimeField, DateField
from wtforms.validators import ValidationError, DataRequired, InputRequired, Email, EqualTo, URL
import email_validator

import pandas as pd
import matplotlib.pyplot as plt
import io
import random
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure


# Current time generator function
def current_time():
    now = datetime.now()
    return now


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
bootstrap = Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)

# CONNECT TO DB
# SQLite database for development

uri = os.environ.get("DATABASE_URL")
if uri == None:
    uri = 'sqlite:///tracker.db'
else:
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

print(f"current database url: {uri}")
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# SQLAlchemyMetaClass Fix

# class Mixin:
#     def __init_subclass__(cls, *, default=None, **kwargs):
#         super().__init_subclass__(**kwargs)
#
#         cls.default = default
#
#
# class Model(db.Model, Mixin, default=2):
#     id = Column(Integer, primary_key=True)


# CREATE & CONFIGURE TABLES
class BloodPressureReading(db.Model):
    __tablename__ = "bp_readings"
    id = db.Column(db.Integer, primary_key=True)
    time_of_reading = db.Column(db.DateTime, nullable=False)
    systolic_mmhg = db.Column(db.Integer, nullable=False)
    diastolic_mmhg = db.Column(db.Integer, nullable=False)
    pulse_bpm = db.Column(db.Integer, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="readings")


class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    id_name = db.Column(db.String(250), nullable=False)
    first_name = db.Column(db.Unicode(250), nullable=False)
    middle_name_or_initial = db.Column(db.Unicode(250), unique=False, nullable=True)
    last_name = db.Column(db.Unicode(250), unique=False, nullable=False)
    name_suffix = db.Column(db.Unicode(250), unique=False, nullable=True)
    date_of_birth = db.Column(db.Date, unique=False, nullable=False)
    readings = relationship("BloodPressureReading", back_populates="patient")
    primary_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    primary_user = relationship("User", back_populates="assigned_patients")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    assigned_patients = relationship("Patient", back_populates="primary_user")


db.create_all()


# FORMS


class PatientForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    middle_name_or_initial = StringField("Middle Name/Initial")
    last_name = StringField("Last Name", validators=[DataRequired()])
    name_suffix = StringField("Suffix")
    date_of_birth = DateField("Date of Birth", validators=[DataRequired()])
    submit = SubmitField("Add/Update Patient")


class BloodPressureReadingForm(FlaskForm):
    time_of_reading = DateTimeField("Time of Reading", validators=[DataRequired()])
    systolic_mmhg = IntegerField("Systolic (mmHg)", validators=[DataRequired()])
    diastolic_mmhg = IntegerField("Diastolic (mmHg)", validators=[DataRequired()])
    pulse_bpm = IntegerField("Pulse (bpm)", validators=[DataRequired()])
    submit = SubmitField("Add/Update Reading")


# Custom form validator for 'RegisterUserForm'


def validate_user_email_unique(form, field):
    existing_user = User.query.filter_by(email=field.data).first()
    if existing_user:
        if field.data == existing_user.email:
            raise ValidationError('This user/email address already exists.')


class RegisterUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(message="Please enter a valid email address.",
                                                                   granular_message=False, check_deliverability=False,
                                                                   allow_smtputf8=True, allow_empty_local=False),
                                             validate_user_email_unique])
    password = PasswordField("Password", validators=[DataRequired(), InputRequired(),
                                                     EqualTo('confirm_password', message='Passwords must match')])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Register")


# Custom form validators for 'LoginForm' -- Triggered by 'login' routhe


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


# LoginMananger inits & fn's

login_manager = LoginManager()
login_manager.init_app(app)


# *** ROUTES ***


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# *** ROUTES ***

# Create admin-only decorator

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.is_anonymous or current_user.id != 1:
            return abort(403)
        else:
            return f(*args, **kwargs)

    return decorated_function






# *** ROUTES ***

@app.route('/', methods=['GET'])
def main_page():
    return render_template("index.html", page_title="Home")


@app.route('/user/id/<int:target_user_id>/')
@login_required
def show_user(target_user_id):
    if current_user.id == target_user_id or current_user.id == 1: # only shows patients under user supervision - admin_only wrapper does not work here
        displayed_user = User.query.get(target_user_id)
        users_patients = Patient.query.filter_by(primary_user_id=displayed_user.id).all()
        return render_template("user.html", page_title=f"User Profile: {displayed_user.name}", displayed_user=displayed_user, users_patients=users_patients)
    else:
        return abort(403)


@app.route('/patient/id/<int:target_patient_id>/')
@login_required
def get_patient(target_patient_id):
    patient = Patient.query.get(target_patient_id)
    if current_user.id == patient.primary_user_id or current_user.id == 1: # admin_only wrapper does not work here

        patient_bp_readings = BloodPressureReading.query.filter_by(patient_id=patient.id).all()
        displayed_user = User.query.filter_by(id=patient.primary_user_id).first()

        # # Create pyplot graph... This should be a separate function,
        # # Shut down this functionality for Heroku version for the time being a/o 2021-10-28
        has_image = False # Necessary pass-tru variable
        # if patient_bp_readings:
        #     print(len(patient_bp_readings))
        #     sys_list = list(patient_bp_readings[x].systolic_mmhg for x in range(len(patient_bp_readings)))
        #     dia_list = list(patient_bp_readings[x].diastolic_mmhg for x in range(len(patient_bp_readings)))
        #     bpm_list = list(patient_bp_readings[x].pulse_bpm for x in range(len(patient_bp_readings)))
        #     date_list = list(patient_bp_readings[x].time_of_reading for x in range(len(patient_bp_readings)))
        #     plt.plot(date_list, sys_list, 'b.')
        #     plt.plot(date_list, dia_list, 'r.')
        #     # plt.plot(date_list, bpm_list, 'r.')
        #     plt.ylim([40, 200])
        #     plt.xlim([date_list[0], date_list[-1]])
        #     plt.xticks(rotation=15)
        #     plt.tight_layout()
        #     plt.legend(['Systolic', 'Diastolic'])
        #     # # # plt.plot(date_list, dia_list)
        #     # # # # # ,[patient_bp_readings.systolic_mmhg for reading in patient_bp_readings])
        #     plt.savefig('static/images/new_plot.png', dpi=300)
        #     plt.close()
        #     has_image = True
        # elif os.path.exists('static/images/new_plot.png'):
        #     os.remove('static/images/new_plot.png')
        #     has_image = False
        #     # # Create pyplot graph...


        return render_template("readouts.html", bp_readings=patient_bp_readings, patient=patient, page_title=f"BP Log: {patient.last_name}, {patient.first_name}", pageheading=f"Blood Pressure Reading Log for:",
                                   page_sub_heading=f"Readings taken By: {displayed_user.name}", has_image=has_image, graph_url='/static/images/new_plot.png')

    else:
        return abort(403)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterUserForm()
    if form.validate_on_submit():
        if form.password.data == form.confirm_password.data:
            hash_and_salted_password = generate_password_hash(
                form.password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            new_user = User(
                email=form.email.data,
                name=form.name.data,
                password=hash_and_salted_password,
            )
            db.session.add(new_user)
            db.session.commit()

            # This line will authenticate the user with Flask-Login
            login_user(new_user)
            return redirect(url_for("main_page"))
        else:
            return redirect(url_for("register"))
    else:
        return render_template("form.html", form=form, pageheading="Register User")


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main_page'))
        else:
            logout_user()
            flash("Incorrect Username or Password")
            return redirect(url_for('login'))
    else:
        return render_template("form.html", form=form, pageheading="Login")


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main_page'))


@app.route("/new-patient", methods=["GET", "POST"])
@login_required
def add_new_patient():
    form = PatientForm()
    if form.validate_on_submit():
        new_patient = Patient(
            first_name=form.first_name.data,
            middle_name_or_initial=form.middle_name_or_initial.data,
            last_name=form.last_name.data,
            name_suffix=form.name_suffix.data,
            date_of_birth=form.date_of_birth.data,
            id_name=form.first_name.data.lower() + "_" + form.last_name.data.lower(),
            primary_user_id=current_user.id
        )
        db.session.add(new_patient)
        db.session.commit()
        return redirect(url_for("main_page"))
    else:
        return render_template("form.html", form=form, pageheading="Add New Patient")


@app.route("/new-reading/patient/id/<int:target_patient_id>", methods=["GET", "POST"])
@login_required
def add_new_reading(target_patient_id):
    form = BloodPressureReadingForm(
        time_of_reading=current_time()
    )
    if form.validate_on_submit():
        new_bp_reading = BloodPressureReading(
            time_of_reading=form.time_of_reading.data,
            systolic_mmhg=form.systolic_mmhg.data,
            diastolic_mmhg=form.diastolic_mmhg.data,
            pulse_bpm=form.pulse_bpm.data,
            patient_id=target_patient_id,
        )
        db.session.add(new_bp_reading)
        db.session.commit()
        return redirect(url_for('get_patient', target_patient_id=new_bp_reading.patient_id))
    else:
        return render_template("form.html", form=form, pageheading="Add New BP Reading")


@app.route("/edit-reading/patient/id/<int:target_patient_id>/reading-id/<int:target_reading_id>", methods=["GET", "POST"])
@login_required
def edit_reading(target_reading_id, target_patient_id):
    patient = Patient.query.get(target_patient_id)
    reading_to_edit = BloodPressureReading.query.get(target_reading_id)
    print(f"send: {patient.last_name} {reading_to_edit.time_of_reading}")
    form = BloodPressureReadingForm(
        time_of_reading=reading_to_edit.time_of_reading,
        systolic_mmhg=reading_to_edit.systolic_mmhg,
        diastolic_mmhg=reading_to_edit.diastolic_mmhg,
        pulse_bpm=reading_to_edit.pulse_bpm
    )
    if form.validate_on_submit():
        reading_to_edit.time_of_reading = form.time_of_reading.data
        reading_to_edit.systolic_mmhg = form.systolic_mmhg.data
        reading_to_edit.diastolic_mmhg = form.diastolic_mmhg.data
        reading_to_edit.pulse_bpm = form.pulse_bpm.data
        db.session.commit()
        return redirect(url_for('get_patient', target_patient_id=patient.id))
        # return redirect(url_for("main_page"))
    else:
        return render_template("form.html", form=form, pageheading=f"Edit New BP Reading",
                               page_sub_heading=f"Patient: {patient.last_name}, {patient.first_name}")


@app.route("/delete-reading/patient/id/<int:target_patient_id>/reading-id/<int:target_reading_id>", methods=["GET"])
@login_required
def delete_reading(target_reading_id, target_patient_id):
    patient = Patient.query.get(target_patient_id)
    reading_to_delete = BloodPressureReading.query.get(target_reading_id)
    db.session.delete(reading_to_delete)
    db.session.commit()
    return redirect(url_for('get_patient', target_patient_id=patient.id))
    # , target_patient_id=target_patient_id)


@app.route("/now", methods=['GET'])  # INDEX ROUTE JUST DIAPLAING TIME-NOW ROUTE
def time_now():
    time_stamp = current_time()  # function is called when get request is made
    print(type(time_stamp))
    return f"{time_stamp}"


# CONTEXT PROCESSORS: https://flask.palletsprojects.com/en/2.0.x/templating/#context-processors

@app.context_processor
def inject_into_base():
    if current_user.is_authenticated:
        if current_user.id == 1:
            all_patients = Patient.query.all()
        else:
            all_patients = Patient.query.filter_by(primary_user_id=current_user.id).all()
    else:
        all_patients = 0
    if current_user.is_authenticated and current_user.id == 1:
        all_users = User.query.all()
    else:
        all_users = 0
    return dict(user=current_user, all_users=all_users, patients=all_patients, created_year=YEAR_CREATED,
                current_year=int(current_time().strftime("%Y")), project_title=PROJECT_TITLE)


# ERROR HANDLER

@app.errorhandler(Exception)
def handle_error(e):
    if isinstance(e, HTTPException):
        pass
        code = e.code
    else:
        e = {
            'code': '500',
            'name': "Internal Server Error",
            'description': 'An internal server error occured...'
        }
        code = e['code']
    return render_template('error.html', pageheading="Error:", error_obj=e), code


# @app.errorhandler(error)
# def page_not_found(e):
#     # note that we set the 404 status explicitly
#     return render_template('error.html', error_msg=e), 403
#
# @app.errorhandler(401)
# def page_not_found(e):
#     # note that we set the 404 status explicitly
#     return render_template('error.html', error_msg=e), 401


# Initialize Server

if __name__ == "__main__":
    app.run(debug=True)
