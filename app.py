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
    case_num=db.Column(db.String(), nullable = False)
    case_year= db.Column(db.String(), nullable = False)
    case_status = db.Column(db.String())
    petitioner = db.Column(db.String())
    respondent =db.Column(db.String())
    listing_date =db.Column(db.String())
    next_date = db.Column(db.String())
    court_no = db.Column(db.String())
class Orders:
    id=db.Column(db.Integer,primary_key=True)
    case_id = db.Column(db.Integer,db.ForeignKey('case.id'),nullable=False)
    order_date = db.Column(db.String())
    corrigendum_link = db.Column(db.String())
    corrigendum_date = db.Column(db.String())
    hindi_order = db.Column(db.String())

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

            orders_link_tag = cols[1].find_elements(By.TAG_NAME, "a")[-1]
            orders_url = orders_link_tag.get_attribute("href")

            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[1])
            driver.get(orders_url)

            orders_page_html = driver.page_source
            soup = BeautifulSoup(orders_page_html,"html.parser")
            orders_table = soup.find("table",{"id":"caseTable"})
            orders = []

            if orders_table:
                rows = orders_table.find("tbody").find_all("tr")
                for row in rows:
                    order_cols = row.find_all("td")

                    order_dict = {
                        "order_date": order_cols[2].text.strip() if len(order_cols) > 2 else "N/A",
                "corrigendum_link": order_cols[3].find("a")["href"].strip() if len(order_cols) > 3 and order_cols[3].find("a") else None,
                "corrigendum_date": order_cols[3].text.strip() if len(order_cols) > 3 else None,
                "hindi_order": order_cols[4].find("a")["href"].strip() if len(order_cols) > 4 and order_cols[4].find("a") else None
                    }
                    orders.append(order_dict)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

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
            #case_obj = Case(case_type = case_type, case_num = case_num, case_year = case_year, case_status=case_data['status'],petitioner = case_data['petitioner'],respondent = case_data['respondent'],listing_date = case_data['last_date'],next_date = case_data['next_date'],court_no=case_data['court_no'])

            #db.session.add(case_obj)
            #db.session.commit()
        else:
            case_data = {"error": "Unexpected table format"}
        return render_template('case_info.html',result = case_data)
if __name__ == '__main__':
    app.run(debug=True)
    #with app.app_context():
        #db.create_all()


