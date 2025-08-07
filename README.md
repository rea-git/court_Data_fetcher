# court_Data_fetcher

## Technologies Used
- Selenium  
- BeautifulSoup  
- Flask  
- SQLite (with SQLAlchemy)

---

## Project Overview

This project creates a local Flask-based web application that fetches case data from the **Delhi High Court** website using Selenium automation and BeautifulSoup scraping, and stores it in a local database.

---

## Core Logic

### Step 1: Flask - `GET` Request
- The application loads the Delhi High Court case status page using Selenium WebDriver.
- Case types and years are scraped from the dropdown HTML using BeautifulSoup.
- The captcha (a random number generated on the website) is also extracted using Selenium.
- All of the above is rendered on the Flask frontend for the user to input case details.

### Step 2: Flask - `POST` Request
- User submits case type, number, year, and captcha through the form.
- Selenium uses the stored WebDriver to submit these details on the real court website.
- The resulting HTML page (showing case information and orders) is parsed using BeautifulSoup.
- The extracted case details and orders are:
  - Displayed to the user
  - Stored in the local SQLite database (only if not already saved)

---

## Data Storage & Access

- If the case data is new, it is stored in a SQLite database via SQLAlchemy ORM.
- A route like `/case/<case_id>` provides access to the stored case history.

---

## Captcha Handling

- The Delhi High Court website uses a numeric captcha (random number).
- Using Selenium, the generated number is captured and displayed on the local site.
- Users must enter the same captcha manually into the form to match what the real site expects.

## How to Run This Flask App

## 1. Clone github
```bash
git clone https://github.com/rea.git/court_Data_fetcher
cd court_Data_fetcher
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment
```bash
venv\Scripts\activate
```

### 4. Install Required Packages
```bash
pip install -r requirements.txt
```

### 6. Run the App

```bash
run.bat
```
