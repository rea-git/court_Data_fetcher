from selenium import webdriver

driver - webdriver.Chrome()

driver.get("https://google.com")

import time 
time.sleep(5)
driver.quit()