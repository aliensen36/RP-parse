from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Опции для Chrome
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

try:
    # Открываем страницу rusprofile
    driver.get('https://www.rusprofile.ru/search-advanced')

    # Ждем появления кнопки "Виды деятельности" и кликаем на нее
    activity_type_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@class="toggle-fields has-list-tree"]//legend[contains(text(), "Вид деятельности")]'))
    )
    activity_type_button.click()

    # Ждем появления поля поиска ОКВЭД и вводим значение 56.10.1
    search_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Название или код"]'))
    )
    search_field.clear()  # Очищаем поле перед вводом нового значения
    search_field.send_keys("56.10.1")

    # Симулируем клик на чекбокс "56.10.1." с помощью JavaScript
    driver.execute_script('''
        var checkbox = document.querySelector('input[id="okved-56.10.1"]');
        if (checkbox) {
            checkbox.click();
            return true;
        } else {
            return false;
        }
    ''')

    # Ждем некоторое время для завершения клика и проверяем статус чекбокса
    checkbox_selected = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//input[@id="okved-56.10.1"]'))
    ).is_selected()

    if checkbox_selected:
        print("Чекбокс '56.10.1.' успешно активирован.")
    else:
        print("Чекбокс '56.10.1.' не удалось активировать.")

except Exception as e:
    print(f"Ошибка при выполнении скрипта: {str(e)}")

finally:
    driver.quit()
