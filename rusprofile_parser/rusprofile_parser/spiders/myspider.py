import scrapy
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.http import HtmlResponse

class MySpider(scrapy.Spider):
    name = 'myspider'
    allowed_domains = ['rusprofile.ru']
    start_urls = ['https://www.rusprofile.ru/search-advanced']
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_with_selenium, headers={'User-Agent': self.USER_AGENT})

    def parse_with_selenium(self, response):
        options = webdriver.ChromeOptions()
        # Убираем опцию headless для отображения браузера
        # options.add_argument("--headless")

        driver = webdriver.Chrome(options=options)
        driver.get(response.url)

        try:
            self.logger.info("Открыта страница: %s", driver.current_url)

            # Ждем появления элемента для раскрытия списка "Виды деятельности"
            activity_type_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@class="toggle-fields has-list-tree"]//legend[contains(text(), "Вид деятельности")]'))
            )
            activity_type_button.click()
            self.logger.info("Кликнули на кнопку 'Виды деятельности'")

            # ОКВЭДы для поиска
            okved_codes = ["56.1", "49.41", "96.02"]

            for okved_code in okved_codes:
                # Ждем появления поля поиска и вводим номер ОКВЭД
                search_field = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Название или код"]'))
                )
                search_field.clear()
                search_field.send_keys(okved_code)
                time.sleep(1)  # Даем время для ввода данных
                self.logger.info("Введен номер ОКВЭД: %s", okved_code)

                # Симулируем клик на чекбокс
                driver.execute_script(f'''
                    var checkbox = document.querySelector('input[id="okved-{okved_code}"]');
                    if (checkbox) {{
                        checkbox.click();
                        return true;
                    }} else {{
                        return false;
                    }}
                ''')
                self.logger.info("Кликнули на чекбокс: %s", okved_code)

            # Симулируем клик на кнопку "Готово" с помощью JavaScript
            driver.execute_script('''
                var submitButton = document.evaluate("//button[contains(text(), 'Готово')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                if (submitButton) {
                    submitButton.click();
                    return true;
                } else {
                    return false;
                }
            ''')

            # Ждем загрузки результатов
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.company-item__title'))
            )
            self.logger.info("Загрузка результатов завершена")

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

            # Проверяем наличие элемента с ИНН
            inn_element = info.css('dl dt:contains("ИНН") + dd::text').get()
            if not inn_element:
                # Альтернативные методы поиска ИНН
                inn_element = info.css('div:contains("ИНН") + span::text').get()
                if not inn_element:
                    inn_element = info.css('div.company-info__text:contains("ИНН") + span::text').get()
            inn = inn_element.strip() if inn_element else None

            # Получаем основной вид деятельности
            okved_element = info.css('dl dt:contains("Основной вид деятельности") + dd::text').get()
            okved = okved_element.strip() if okved_element else None

            if not inn:
                self.logger.warning(f"ИНН не найден для компании: {company_name}")
                self.logger.debug(f"HTML компании: {info.get()}")

            yield {
                'company_name': company_name,
                'inn': inn,
                'okved': okved,
            }

# Настройки для логирования
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'myspider.log',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# Применение настроек логирования
import logging.config
logging.config.dictConfig(LOGGING)
