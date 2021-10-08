# # (C)opyright 2021 Edward Francis Westfield Jr. | Standard MIT License
PROJECT_TITLE = "BP Tracker"
YEAR_CREATED = 2021


import requests
from flask import Flask, render_template, redirect, request, url_for, flash, abort
from flask_bootstrap import Bootstrap

from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import Column, Integer, DateTime, Date
from sqlalchemy.orm import relationship
import os
from datetime import date, datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_gravatar import Gravatar
from functools import wraps

from flask_ckeditor import CKEditor, CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, DateTimeField, DateField
from wtforms.validators import DataRequired, URL

import pandas as pd


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
DB_URI = os.environ.get("DB_URI")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_URI}'
# Switch to PostgreSQL for deployment - this will use sqlite database if run locally
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")
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


if not os.path.isfile(DB_URI):
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
    # time_of_reading = DateTimeField("Time of Reading", validators=[DataRequired()])
    systolic_mmhg = IntegerField("Systolic (mmHg)", validators=[DataRequired()])
    diastolic_mmhg = IntegerField("Diastolic (mmHg)", validators=[DataRequired()])
    pulse_bpm = IntegerField("Pulse (bpm)", validators=[DataRequired()])
    submit = SubmitField("Add Reading")


# # #

# ROUTES

# @app.route("/", methods=['GET'])
# def index():
#     return render_template("index.html", year=current_time().strftime("%Y"))
#
# @app.route("/other", methods=['GET'])
# def other():
#     return render_template("index2.html", year=current_time().strftime("%Y"))

PROJECT_TITLE = "BP Tracker"

@app.route('/', methods=['GET'])
def get_all_patients():
    patients = Patient.query.all()
    bp_readings = BloodPressureReading.query.all()
    return render_template("index.html", patients=patients, bp_readings=bp_readings, created_year=YEAR_CREATED, current_year=current_time().strftime("%Y"), project_title=PROJECT_TITLE)


@app.route("/new-patient", methods=["GET", "POST"])
def add_new_patient():
    form = PatientForm()
    if form.validate_on_submit():
        new_patient = Patient(
            first_name=form.first_name.data,
            middle_name_or_initial=form.middle_name_or_initial.data,
            last_name=form.last_name.data,
            name_suffix=form.name_suffix.data,
            date_of_birth=form.date_of_birth.data,
            id_name=form.first_name.data.lower()+"_"+form.last_name.data.lower()
        )
        db.session.add(new_patient)
        db.session.commit()
        return redirect(url_for("get_all_patients"))
    else:
        return render_template("form.html", form=form, pageheading="Add New Patient", created_year=YEAR_CREATED, current_year=current_time().strftime("%Y"), project_title=PROJECT_TITLE)

@app.route("/new-reading/patient-id-<int:target_patient_id>", methods=["GET", "POST"])
def add_new_reading(target_patient_id):
    form = BloodPressureReadingForm()
    if form.validate_on_submit():
        new_bp_reading = BloodPressureReading(
            time_of_reading=current_time(),
            systolic_mmhg=form.systolic_mmhg.data,
            diastolic_mmhg=form.diastolic_mmhg.data,
            pulse_bpm=form.pulse_bpm.data,
            patient_id=target_patient_id,
        )
        db.session.add(new_bp_reading)
        db.session.commit()
        return redirect(url_for("get_all_patients"))
    else:
        return render_template("form.html", form=form, pageheading="Add New BP Reading", created_year=YEAR_CREATED, current_year=current_time().strftime("%Y"), project_title=PROJECT_TITLE)

@app.route("/now", methods=['GET'])  # INDEX ROUTE JUST DIAPLAING TIME-NOW ROUTE
def time_now():
    time_stamp = current_time()  # fuction is called when get request is made
    print(type(time_stamp))
    return f"{time_stamp}"


if __name__ == "__main__":
    app.run(debug=True)
