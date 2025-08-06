from flask import Flask, render_template, request, session, redirect, url_for
from flask_restful import Resource, Api, reqparse
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

import time
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'test' 

db = SQLAlchemy(app)

class Case(db.Model):
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
    orders = db.relationship('Orders', backref='Case', lazy=True)
class Orders(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    case_id = db.Column(db.Integer,db.ForeignKey('case.id'),nullable=False)
    order_date = db.Column(db.String())
    corrigendum_link = db.Column(db.String())
    corrigendum_date = db.Column(db.String())
    hindi_order = db.Column(db.String())


def driver_load():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options = chrome_options)
    #driver=webdriver.Chrome()
    return driver
def case_options(driver):
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
        print("Loading driver...")
        driver = driver_load()
        print("Opening URL...")
        driver.get("https://delhihighcourt.nic.in/app/get-case-type-status")
        print("Sleeping...")
        time.sleep(2)
        print("Getting case options...")
        case_type_options,case_year_options,captcha_code = case_options(driver)
        print("Getting cases from DB...")
        case_list=[]
        case_history = Case.query.all()
        if len(case_history)>0:
            for case in case_history:
                case_data = {
                "case_id":case.id,
                "case_type":case.case_type,
                "case_num": case.case_num,
                "case_year":case.case_year,
            }
                case_list.append(case_data)
        session['captcha_code'] = captcha_code
        session['case_type_options'] = case_type_options
        session['case_year_options'] = case_year_options

        app.config['driver'] = driver

        return render_template('index.html', captcha_code = captcha_code, case_type_options = case_type_options, case_year_options=case_year_options,case_list=case_list)
    else:
        driver = app.config.get('driver') 
        case_type = request.form.get("case_type")
        case_num  =request.form.get("case_num")
        case_year = request.form.get("case_year")
        user_captcha = request.form.get("captcha_code")

        if user_captcha !=session.get("captcha_code"):
            driver.quit()
            return render_template("error.html",message = "CAPTCHA is incorrect. Pleaes try again")
        
        case_type_element = Select(driver.find_element(By.ID,"case_type"))
        case_type_element.select_by_visible_text(case_type)

        driver.find_element(By.ID,"case_number").send_keys(case_num)

        case_year_element = Select(driver.find_element(By.ID, "case_year"))
        case_year_element.select_by_visible_text(case_year)

        driver.find_element(By.ID, "captchaInput").send_keys(user_captcha)

        search = driver.find_element(By.ID,"search")
        driver.execute_script("arguments[0].click()",search)

        time.sleep(2)
        
        row = driver.find_element(By.CSS_SELECTOR, "#caseTable tbody tr")
        cols = row.find_elements(By.TAG_NAME,"td")
        if len(cols) >= 4:
            case_info_raw = cols[1].get_attribute("innerHTML").strip().split("<br>")
            petitioner_info_raw = cols[2].get_attribute("innerHTML").strip().split("<br>")
            listing_info_raw = cols[3].get_attribute("innerHTML").strip().split("<br>")

            orders_link_tag = cols[1].find_elements(By.TAG_NAME, "a")[-1]
            orders_url = orders_link_tag.get_attribute("href")
            driver.quit()
            driver = driver_load()
            driver.get(f"{orders_url}")
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source,"html.parser")
            orders_table = soup.find("table",{"id":"caseTable"})
            orders = []
            driver.quit()
            if orders_table:
                tbody = orders_table.find("tbody")
                if tbody:
                    rows = tbody.find_all("tr")
                    for row in rows:
                        order_cols = row.find_all("td")
                        if len(order_cols)<5:
                            continue
                        order_dict = {
                            "order_date": order_cols[2].text.strip() if len(order_cols) > 2 else "N/A",
                            "corrigendum_link": order_cols[1].find("a")["href"].strip() if order_cols[1].find("a") else None,
                            "corrigendum_date": order_cols[3].text.strip() if len(order_cols) > 3 else None,
                            "hindi_order": order_cols[4].find("a")["href"].strip() if order_cols[4].find("a") else None
                            }
                        orders.append(order_dict)
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
            check = Case.query.filter_by(case_type = case_type, case_num = case_num, case_year = case_year).first()
            if not check:
                case_obj = Case(case_type = case_type, case_num = case_num, case_year = case_year, case_status=case_data['status'],petitioner = case_data['petitioner'],respondent = case_data['respondent'],listing_date = case_data['last_date'],next_date = case_data['next_date'],court_no=case_data['court_no'])
                db.session.add(case_obj)
                db.session.commit()
                if orders:
                    for order in orders:
                        order_obj = Orders(case_id=case_obj.id,order_date = order['order_date'],corrigendum_link=order['corrigendum_link'],corrigendum_date=order['corrigendum_date'],hindi_order=order['hindi_order'])
                        db.session.add(order_obj)
                        db.session.commit()
        else:
            case_data = {"error": "No data Found"}

        return render_template('case_info.html',result = case_data, orders = orders)
@app.route('/<int:id>')
def view_case(id):
    case = Case.query.filter_by(id=id).first()
    case_data = {
                "case_number": case.case_num,
                "status": case.case_status,
                "petitioner": case.petitioner,
                "respondent": case.respondent,
                "next_date": case.next_date,
                "last_date": case.listing_date,
                "court_no": case.court_no
            }
    order_list = []
    print(case.orders)
    if case.orders:
        for order in case.orders:
            order_data = {
                "order_date": order.order_date if order else "N/A",
                "corrigendum_link": order.corrigendum_link if order else None,
                "corrigendum_date": order.corrigendum_date if order else None,
                "hindi_order": order.hindi_order if order else None
                    }
            print(order_data)
            order_list.append(order_data)
    return render_template('case_info.html',result = case_data,orders=order_list)
if __name__ == '__main__':
    app.run(debug=True)