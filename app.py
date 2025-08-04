from flask import Flask, render_template, request, jsonify
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import flask_sqlalchemy

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import time

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Case:
    id = db.Column(db.Integer,primary_key=True)
    case_type = db.Column(db.String(), nullable =False)
    case_num=db.Column(db.Integer, nullable = False)
    case_year= db.Column(db.Integer, nullable = False)
    case_status = db.Column(db.String())
    petitioner = db.Column(db.String())
    respondent =db.Column(db.String())
    listing_date =db.Column(db.Date)
    next_date = db.Column(db.Date)
    court_no = db.Column(db.String())

driver = webdriver.Chrome()
driver.get("https://delhihighcourt.nic.in/app/get-case-type-status")
time.sleep(2)

cast_type_dropdown = Select(driver.find_element(By.ID, 'case_type'))
case_type_options = [option.text.strip() for option in case_type_dropdown.options if option.text.strip()]

case_year_dropdown = Select(driver.find_element(By.ID, 'case_year'))
case_year_options = [option.text.strip() for option in case_year_dropdown.options if option.text.strip()]

captcha_element = driver.find_element(By.ID, "captcha-code")
captcha_code = captcha_element.text

@app.route('/',methods = ['POST','GET'])
def index():
    if request.method =='GET': return render_template('index.html')
    else:
        