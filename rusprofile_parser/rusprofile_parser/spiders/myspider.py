import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.http import HtmlResponse

class MySpider(scrapy.Spider):
    name = 'myspider'
    allowed_domains = ['rusprofile.ru']

    def start_requests(self):
        url = 'https://www.rusprofile.ru/search-advanced'
        yield scrapy.Request(url, callback=self.parse_with_selenium)

    def parse_with_selenium(self, response):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Запуск браузера в фоновом режиме (без GUI)

        driver = webdriver.Chrome(options=options)
        driver.get(response.url)

        try:
            # Находим чекбокс для ОКВЭД 56.10.1 и выбираем его
            okved_checkbox = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//input[@name="okveds[]" and @value="56.10.1"]'))
            )
            okved_checkbox.click()

            # Находим кнопку "Готово" и нажимаем на нее
            submit_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Готово")]'))
            )
            submit_button.click()

            # Ждем загрузки результатов
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.company-item__title'))
            )

            # Получаем HTML-код страницы с результатами
            body = driver.page_source

            # Создаем объект Response для обработки в Scrapy
            response = HtmlResponse(url=response.url, body=body, encoding='utf-8')

            # Парсим страницу с результатами
            yield from self.parse(response)

        finally:
            driver.quit()

    def parse(self, response):
        # Парсинг страницы с результатами
        companies = response.css('.company-item__title')
        company_infos = response.css('.company-item-info')

        for company, info in zip(companies, company_infos):
            company_name = company.css('a span::text').get().strip()
            inn = info.css('dl dt:contains("ИНН") + dd::text').get().strip()

            yield {
                'company_name': company_name,
                'inn': inn,
            }

    def parse_company_info(self, response):
        company_name = response.meta['company_name']
        inn = response.css('.company-item-info dl dt:contains("ИНН") + dd::text').get().strip()

        yield {
            'company_name': company_name,
            'inn': inn,
        }
