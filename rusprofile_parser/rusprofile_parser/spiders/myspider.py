import logging
from urllib import response

import scrapy
from scrapy.http import HtmlResponse
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from scrapy.exceptions import IgnoreRequest
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
from dotenv import load_dotenv
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# Загрузка переменных окружения из .env файла
load_dotenv()

class MySpider(scrapy.Spider):
    name = 'myspider'
    allowed_domains = ['rusprofile.ru']
    start_urls = ['https://www.rusprofile.ru/search-advanced']
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.driver = None

    def setup_driver(self):
        service = ChromeService(ChromeDriverManager().install())
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f"user-agent={self.USER_AGENT}")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    @property
    def logger(self):
        return logging.getLogger(__name__)

    def login(self):
        self.setup_driver()
        try:
            self.driver.get("https://www.rusprofile.ru/search-advanced")
            # Симуляция клика на кнопку Войти(1) на главной странице с помощью JavaScript
            self.driver.execute_script('''
                            var loginButton1 = document.querySelector('div#menu-personal-trigger');
                            if (loginButton1) {
                                loginButton1.click();
                                return true;
                            } else {
                                return false;
                            }
                        ''')
            # Ввод электронной почты
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "fome_email"))
            )
            email_input.clear()
            email_input.send_keys(os.getenv('EMAIL'))
            # Ввод пароля
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "form_pass"))
            )
            password_input.clear()
            password_input.send_keys(os.getenv('PASSWORD'))
            # Симуляция клика на кнопку Войти(2) во всплывающем окне с помощью JavaScript
            self.driver.execute_script('''
                            var loginButton2 = document.querySelector('div.vModal-buttons button.btn.btn-blue');
                            if (loginButton2) {
                                loginButton2.click();
                                return true;
                            } else {
                                return false;
                            }
                        ''')
            # Ожидание появления кнопки "Продолжить работу"
            try:
                button_continue = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//a[contains(@class, 'btn-blue') and contains(text(), 'Продолжить работу')]"))
                )
                # Используем ActionChains для выполнения клика
                ActionChains(self.driver).move_to_element(button_continue).click().perform()
                time.sleep(10)
                return True
            except TimeoutException:
                return False
        except Exception as e:
            return False


    def start_requests(self):
        if not self.login():
            return
        if self.driver is None:
            self.logger.error("Драйвер не инициализирован. Прекращаем выполнение.")
            return
        # После успешного входа, начинаем скрапинг
        for url in self.start_urls:
            yield SeleniumRequest(url=url, callback=self.parse_with_selenium, wait_time=10,
                                      cookies=self.driver.get_cookies())

    def parse_with_selenium(self, response):
        driver = self.driver

        if driver is None:
            self.logger.error("Драйвер не инициализирован в parse_with_selenium.")
            return


        try:
            driver.get(response.url)
            self.logger.info("Открыта страница: %s", driver.current_url)

            # Ждем появления элемента для раскрытия списка "Виды деятельности"
            activity_type_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH,
                                            '//div[@class="toggle-fields has-list-tree"]//legend[contains(text(), "Вид деятельности")]'))
            )
            activity_type_button.click()




            # Ожидание появления всплывающего окна
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.modal-pop-body'))
            )

            # Ждем появления элемента для раскрытия списка "ОКВЭД"
            okved_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH,
                                            '//div[@class="toggle-fields has-list-tree"]//legend[contains(text(), "ОКВЭД")]'))
            )
            okved_button.click()
            print("Кликнули на кнопку 'ОКВЭД'")

            # Коды ОКВЭД для поиска
            okved_codes = ["49.41", "56.1", "96.02"]

            for okved_code in okved_codes:
                try:
                    # Ожидание поиска по кодам ОКВЭД
                    search_field = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Название или код"]'))
                    )
                    search_field.clear()
                    search_field.send_keys(okved_code)
                    time.sleep(1)  # Give time for data entry
                    self.logger.info("Введен номер ОКВЭД: %s", okved_code)

                    # Симуляция клика на чекбокс с помощью JavaScript
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

                except Exception as e:
                    self.logger.error(f"Ошибка при обработке ОКВЭД {okved_code}: {e}")
                    continue

            # Симуляция клика на "Готово"
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

                # Оэидание загрузки результата
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.company-item__title'))
                )
                self.logger.info("Загрузка результатов завершена")

                # Get HTML code of results page
                body = driver.page_source

                # Create Response object for Scrapy processing
                response = HtmlResponse(url=response.url, body=body, encoding='utf-8')

                # Parse results page
                yield from self.parse_results(response)

            except Exception as e:
                self.logger.error(f"Ошибка при получении результатов: {e}")


        except Exception as e:
            self.logger.error(f"Ошибка при обработке страницы: {e}")

    def parse_results(self, response):
        # Parsing results page
        companies = response.css('.company-item__title')
        company_infos = response.css('.company-item-info')

        for company, info in zip(companies, company_infos):
            company_name = company.css('a span::text').get().strip()

            # Check for INN element
            inn_element = info.css('dl dt:contains("ИНН") + dd::text').get()
            if not inn_element:
                # Alternative methods to find INN
                inn_element = info.css('div:contains("ИНН") + span::text').get()
                if not inn_element:
                    inn_element = info.css('div.company-info__text:contains("ИНН") + span::text').get()
            inn = inn_element.strip() if inn_element else None

            # Get primary activity type
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

    def closed(self, reason):
        self.driver.quit()
