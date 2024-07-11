import os
import logging
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Загрузка переменных окружения из .env файла
load_dotenv()


class LoginHandler:
    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)  # Если logger не передан, используем текущий модульный логгер

    def login(self):
        self.logger.info("Выполняем вход в систему...")

        try:
            # Переходим на страницу авторизации
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
            self.logger.info("Кнопка Войти (1) на главной странице нажата с помощью JavaScript")



            # Ввод электронной почты
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "fome_email"))
            )
            email_input.clear()
            email_input.send_keys(os.getenv('EMAIL'))  # Получение электронной почты из переменной окружения

            # Ввод пароля
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "form_pass"))
            )
            password_input.clear()
            password_input.send_keys(os.getenv('PASSWORD'))  # Получение пароля из переменной окружения

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
            self.logger.info("Кнопка Войти (2) во всплывающем окне нажата с помощью JavaScript")

            # # Дождитесь исчезновения всплывающего окна
            # WebDriverWait(self.driver, 10).until(
            #     EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.vModal-content'))
            # )

            self.logger.info("Окно авторизации закрыто")

            return True

        except (TimeoutException, NoSuchElementException) as e:
            self.logger.error(f"Ошибка при авторизации: {e}")
            return False
