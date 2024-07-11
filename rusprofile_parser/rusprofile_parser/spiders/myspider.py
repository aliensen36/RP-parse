import logging
import time
import scrapy
from scrapy.http import HtmlResponse
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from scrapy.exceptions import IgnoreRequest
from login_handler.login_handler import LoginHandler


class MySpider(scrapy.Spider):
    name = 'myspider'
    allowed_domains = ['rusprofile.ru']
    start_urls = ['https://www.rusprofile.ru/search-advanced']
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.driver = None  # Определение driver
        self.report_file = 'scrapy_execution_report.txt'  # Имя файла для отчета

        # Настройка логгера для записи в файл
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler(self.report_file, 'a', 'utf-8')])

    @property
    def logger(self):
        # Возвращает логгер для текущего класса
        return logging.getLogger(__name__)

    def _write_to_report(self, message):
        # Запись сообщения в файл отчета
        with open(self.report_file, 'a', encoding='utf-8') as file:
            file.write(f"{message}\n")


    def start_requests(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f"user-agent={self.USER_AGENT}")

        self.driver = webdriver.Chrome(options=chrome_options)

        # Передаем driver и logger в LoginHandler
        self.login_handler = LoginHandler(self.driver, self.logger)
        if not self.login_handler.login():
            self.logger.error("Не удалось выполнить вход")
            self._write_to_report("Не удалось выполнить вход")
            return

        # После успешной авторизации начинаем парсинг
        for url in self.start_urls:
            yield SeleniumRequest(url=url, callback=self.parse_with_selenium, wait_time=10)

    def parse_with_selenium(self, response):
        # driver уже инициализирован в методе start_requests
        driver = self.driver

        try:
            driver.get(response.url)
            self.logger.info("Открыта страница: %s", driver.current_url)
            self._write_to_report(f"Открыта страница: {driver.current_url}")

            # JavaScript для получения текущего User-Agent
            user_agent = driver.execute_script("return navigator.userAgent;")
            self.logger.info("Текущий User-Agent: %s", user_agent)

            # Ждем появления элемента для раскрытия списка "Виды деятельности"
            activity_type_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH,
                                            '//div[@class="toggle-fields has-list-tree"]//legend[contains(text(), "Вид деятельности")]'))
            )
            activity_type_button.click()
            self.logger.info("Кликнули на кнопку 'Виды деятельности'")
            self._write_to_report("Кликнули на кнопку 'Виды деятельности'")

            # ОКВЭДы для поиска
            okved_codes = ["56.1", "49.41", "96.02"]

            for okved_code in okved_codes:
                try:
                    # Ждем появления поля поиска и вводим номер ОКВЭД
                    search_field = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Название или код"]'))
                    )
                    search_field.clear()
                    search_field.send_keys(okved_code)
                    time.sleep(1)  # Даем время для ввода данных
                    self.logger.info("Введен номер ОКВЭД: %s", okved_code)
                    self._write_to_report(f"Введен номер ОКВЭД: {okved_code}")

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
                    self._write_to_report(f"Кликнули на чекбокс: {okved_code}")

                except Exception as e:
                    self.logger.error(f"Ошибка при обработке ОКВЭД {okved_code}: {e}")
                    self._write_to_report(f"Ошибка при обработке ОКВЭД {okved_code}: {e}")
                    continue

            # Симулируем клик на кнопку "Готово" с помощью JavaScript
            try:
                driver.execute_script('''
                    var submitButton = document.evaluate("//button[contains(text(), 'Готово')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    if (submitButton) {
                        submitButton.click();
                        return true;
                    } else {
                        return false;
                    }
                ''')
                self.logger.info("Кликнули на кнопку 'Готово'")
                self._write_to_report("Кликнули на кнопку 'Готово'")

                # Ждем загрузки результатов
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.company-item__title'))
                )
                self.logger.info("Загрузка результатов завершена")
                self._write_to_report("Загрузка результатов завершена")

                # Получаем HTML-код страницы с результатами
                body = driver.page_source

                # Создаем объект Response для обработки в Scrapy
                response = HtmlResponse(url=response.url, body=body, encoding='utf-8')

                # Парсим страницу с результатами
                yield from self.parse_results(response)

            except Exception as e:
                self.logger.error(f"Ошибка при получении результатов: {e}")

        finally:
            driver.quit()

    def parse_results(self, response):
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

        def parse_error(self, failure):
            if failure.check(IgnoreRequest):
                self.logger.error(f"IgnoreRequest: {failure.value}")

        def process_exception(self, request, exception, spider):
            if isinstance(exception, IgnoreRequest):
                self.logger.error(f"IgnoreRequest: {exception}")
