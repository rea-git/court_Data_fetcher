from flask import Flask, render_template, request, jsonify
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup

import time

app = Flask(__name__)
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
def driver_load():
    driver.get("https://delhihighcourt.nic.in/app/get-case-type-status")
    time.sleep(1)

    case_type_dropdown = Select(driver.find_element(By.ID, 'case_type'))
    case_type_options = [option.text.strip() for option in case_type_dropdown.options if option.text.strip()]

    case_year_dropdown = Select(driver.find_element(By.ID, 'case_year'))
    case_year_options = [option.text.strip() for option in case_year_dropdown.options if option.text.strip()]

    captcha_element = driver.find_element(By.ID, "captcha-code")
    captcha_code = captcha_element.text

    return case_type_options, case_year_options, captcha_code

@app.route('/',methods = ['POST','GET'])
def index():
    if request.method =='GET':
        case_type_options,case_year_options,captcha_code = driver_load() 
        return render_template('index.html', captcha_code = captcha_code, case_type_options = case_type_options, case_year_options=case_year_options)
    else:
        case_type = request.form.get("case_type")
        case_num  =request.form.get("case_num")
        case_year = request.form.get("case_year")
        user_captcha = request.form.get("captcha_code")

        case_type_element = Select(driver.find_element(By.ID,"case_type"))
        case_type_element.select_by_visible_text(case_type)

        driver.find_element(By.ID,"case_number").send_keys(case_num)

        case_year_element = Select(driver.find_element(By.ID, "case_year"))
        case_year_element.select_by_visible_text(case_year)

        driver.find_element(By.ID, "captchaInput").send_keys(user_captcha)

        driver.find_element(By.ID,"search").click()

        time.sleep(1)

        row = driver.find_element(By.CSS_SELECTOR, "#caseTable tbody tr")
        cols = row.find_elements(By.TAG_NAME,"td")
        if len(cols) >= 4:
            case_info_raw = cols[1].get_attribute("innerHTML").strip().split("<br>")
            petitioner_info_raw = cols[2].get_attribute("innerHTML").strip().split("<br>")
            listing_info_raw = cols[3].get_attribute("innerHTML").strip().split("<br>")

            def clean_html(text):
                return BeautifulSoup(text, "html.parser").text.strip()

            case_info = [clean_html(item) for item in case_info_raw if item.strip()]
            petitioner_info = [clean_html(item) for item in petitioner_info_raw if item.strip()]
            listing_info = [clean_html(item) for item in listing_info_raw if item.strip()]

        # Prepare final dictionary
            case_data = {
                "case_number": case_info[0] if len(case_info) > 0 else "N/A",
                "status": case_info[1] if len(case_info) > 1 else "N/A",
                "petitioner": petitioner_info[0] if len(petitioner_info) > 0 else "N/A",
                "respondent": petitioner_info[2] if len(petitioner_info) > 2 else "N/A",
                "next_date": listing_info[0].replace("NEXT DATE:", "").strip() if len(listing_info) > 0 else "N/A",
                "last_date": listing_info[1].replace("Last Date:", "").strip() if len(listing_info) > 1 else "N/A",
                "court_no": listing_info[2].replace("COURT NO:", "").strip() if len(listing_info) > 2 else "N/A"
            }
        else:
            case_data = {"error": "Unexpected table format"}
        return render_template('case_info.html',result = case_data)
app.run(debug=True)