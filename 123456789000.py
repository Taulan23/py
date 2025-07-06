import pytesseract
import pyautogui
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import time
import os
import sys
import json
import shutil
import threading
import platform
import argparse
from tabulate import tabulate

# Конфигурация по умолчанию
DEFAULT_CONFIG = {
    'history_size': 10,
    'debug_mode': False,
    'output_file': 'numbers.json',
    'scan_interval': 1.0,
    'tesseract_config': '--psm 11 --oem 3 -c tessedit_char_whitelist=0123456789.:',
    'image_processing': {
        'enhance_contrast': True,
        'sharpen': True,
        'threshold': 120,
        'clahe_clip_limit': 2.0,
        'clahe_tile_grid': [8, 8]
    },
    'region_file': 'region.json'
}

def get_system_info():
    """Получает информацию о системе"""
    system = platform.system()
    arch = platform.machine()
    return {
        'system': system,
        'architecture': arch,
        'platform': f"{system} {arch}",
        'python_version': platform.python_version()
    }

def find_tesseract():
    """Автоматически находит Tesseract в системе"""
    system_info = get_system_info()
    
    # Возможные пути для разных систем
    possible_paths = []
    
    if system_info['system'] == 'Windows':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\%USERNAME%\AppData\Local\Tesseract-OCR\tesseract.exe'
        ]
    elif system_info['system'] == 'Darwin':  # macOS
        possible_paths = [
            '/opt/homebrew/bin/tesseract',  # Apple Silicon
            '/usr/local/bin/tesseract',     # Intel Mac
            '/usr/bin/tesseract'
        ]
    else:  # Linux и другие Unix-системы
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/bin/tesseract'
        ]
    
    # Проверяем пути
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Пытаемся найти в PATH
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        return tesseract_path
    
    return None

def setup_tesseract():
    """Настраивает Tesseract OCR"""
    tesseract_path = find_tesseract()
    
    if not tesseract_path:
        print("❌ Tesseract OCR не найден в системе!")
        print("\n📦 Инструкции по установке:")
        system_info = get_system_info()
        
        if system_info['system'] == 'Windows':
            print("   Windows: Скачайте с https://github.com/UB-Mannheim/tesseract/wiki")
        elif system_info['system'] == 'Darwin':
            print("   macOS: brew install tesseract")
        else:
            print("   Ubuntu/Debian: sudo apt-get install tesseract-ocr")
            print("   CentOS/RHEL: sudo yum install tesseract")
        
        sys.exit(1)
    
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"✅ Tesseract найден: {tesseract_path}")
    
    try:
        version = pytesseract.get_tesseract_version()
        print(f"📋 Версия Tesseract: {version}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при проверке Tesseract: {e}")
        return False

def load_config(config_file='config.json'):
    """Загружает конфигурацию из файла"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Объединяем с настройками по умолчанию
            merged_config = DEFAULT_CONFIG.copy()
            merged_config.update(config)
            return merged_config
        return DEFAULT_CONFIG
    except Exception as e:
        print(f"⚠️ Ошибка загрузки конфигурации: {e}")
        return DEFAULT_CONFIG

def save_config(config, config_file='config.json'):
    """Сохраняет конфигурацию в файл"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ Конфигурация сохранена в {config_file}")
    except Exception as e:
        print(f"❌ Ошибка сохранения конфигурации: {e}")

def save_region(region, filename):
    """Сохраняет выбранную область в файл"""
    try:
        region_data = {
            'x': region[0],
            'y': region[1],
            'width': region[2],
            'height': region[3],
            'created': datetime.now().isoformat()
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(region_data, f, ensure_ascii=False, indent=2)
        print(f"💾 Область сохранена в {filename}")
    except Exception as e:
        print(f"❌ Ошибка сохранения области: {e}")

def load_region(filename):
    """Загружает сохраненную область из файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                region_data = json.load(f)
            return (region_data['x'], region_data['y'], region_data['width'], region_data['height'])
        return None
    except Exception as e:
        print(f"⚠️ Ошибка загрузки области: {e}")
        return None

def clear_screen():
    """Очищает экран кроссплатформенно"""
    os.system('cls' if os.name == 'nt' else 'clear')

def select_region(config):
    """Выбирает область для мониторинга с улучшенным интерфейсом"""
    # Проверяем, есть ли сохраненная область
    saved_region = load_region(config['region_file'])
    if saved_region:
        print(f"📁 Найдена сохраненная область: {saved_region}")
        choice = input("Использовать сохраненную область? (y/n): ").lower()
        if choice in ['y', 'yes', 'да', '']:
            return saved_region
    
    print("🎯 Выберите область для мониторинга:")
    print("   Перемещайте курсор мыши в нужную позицию")
    print("   Выберите разные точки для создания прямоугольной области")
    print("   Минимальный размер: 10×10 пикселей")
    print("   Нажмите Ctrl+C для отмены")
    print()
    
    try:
        # Первая точка
        print("1️⃣ Наведите курсор на ЛЕВЫЙ ВЕРХНИЙ угол области")
        print("   Текущая позиция:", end=" ")
        
        def show_position():
            while True:
                try:
                    x, y = pyautogui.position()
                    print(f"\r   Позиция: ({x:4d}, {y:4d})    ", end="", flush=True)
                    time.sleep(0.1)
                except:
                    break
        
        position_thread = threading.Thread(target=show_position, daemon=True)
        position_thread.start()
        
        input("\n   Нажмите Enter для фиксации позиции...")
        x1, y1 = pyautogui.position()
        print(f"   ✅ Зафиксировано: ({x1}, {y1})")
        
        # Вторая точка
        print("\n2️⃣ Наведите курсор на ПРАВЫЙ НИЖНИЙ угол области")
        print("   Текущая позиция:", end=" ")
        
        position_thread = threading.Thread(target=show_position, daemon=True)
        position_thread.start()
        
        input("\n   Нажмите Enter для фиксации позиции...")
        x2, y2 = pyautogui.position()
        print(f"   ✅ Зафиксировано: ({x2}, {y2})")
        
        # Вычисляем область
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Проверяем минимальный размер области
        if width < 10 or height < 10:
            print(f"\n❌ Слишком маленькая область: {width}×{height} пикселей")
            print("   Минимальный размер: 10×10 пикселей")
            print("   Попробуйте еще раз, выбрав разные точки")
            return select_region(config)
        
        region = (min(x1, x2), min(y1, y2), width, height)
        
        print(f"\n📏 Размер области: {width}×{height} пикселей")
        
        # Сохраняем область
        save_region(region, config['region_file'])
        
        return region
        
    except KeyboardInterrupt:
        print("\n❌ Выбор области отменен")
        sys.exit(0)

def preprocess_image(img, config):
    """Улучшенная обработка изображения с настройками"""
    try:
        img_np = np.array(img)
        
        # Конвертируем в HSV для лучшей обработки
        hsv = cv2.cvtColor(img_np, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # Улучшение контраста
        if config['image_processing']['enhance_contrast']:
            clahe = cv2.createCLAHE(
                clipLimit=config['image_processing']['clahe_clip_limit'],
                tileGridSize=tuple(config['image_processing']['clahe_tile_grid'])
            )
            v_enhanced = clahe.apply(v)
        else:
            v_enhanced = v
        
        # Обработка точек и символов
        _, dots_thresh = cv2.threshold(
            v_enhanced, 
            config['image_processing']['threshold'], 
            255, 
            cv2.THRESH_BINARY
        )
        dots = cv2.bitwise_not(dots_thresh)
        
        # Заточка изображения
        if config['image_processing']['sharpen']:
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(v_enhanced, -1, kernel)
        else:
            sharpened = v_enhanced
        
        # Адаптивная пороговая обработка
        binary = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 31, 7
        )
        
        # Объединение результатов
        combined = cv2.bitwise_or(binary, dots)
        
        # Морфологические операции
        kernel = np.ones((1, 1), np.uint8)
        final = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        
        return Image.fromarray(final)
        
    except Exception as e:
        if config['debug_mode']:
            print(f"⚠️ Ошибка обработки изображения: {e}")
        return img

def recognize_text(img, config):
    """Распознает текст с настраиваемыми параметрами"""
    try:
        text = pytesseract.image_to_string(img, config=config['tesseract_config'])
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Гарантируем возврат нужного количества строк
        while len(lines) < 3:
            lines.append("?")
        
        return lines[:3]
        
    except Exception as e:
        if config['debug_mode']:
            print(f"⚠️ Ошибка распознавания: {e}")
        return ["?", "?", "?"]

def load_numbers(filename):
    """Загружает числа из JSON файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('numbers', [])
        return []
    except Exception as e:
        print(f"⚠️ Ошибка загрузки данных: {e}")
        return []

def save_numbers(numbers_list, filename):
    """Сохраняет список чисел в JSON файл"""
    try:
        data = {
            'last_updated': datetime.now().isoformat(),
            'total_count': len(numbers_list),
            'system_info': get_system_info(),
            'numbers': numbers_list
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if len(numbers_list) > 0:
            print(f"💾 Данные сохранены ({len(numbers_list)} записей)")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")

def save_single_number(number, filename):
    """Добавляет одно число в JSON файл"""
    try:
        existing_numbers = load_numbers(filename)
        
        new_entry = {
            'number': number,
            'timestamp': datetime.now().isoformat(),
            'id': len(existing_numbers) + 1
        }
        
        existing_numbers.insert(0, new_entry)
        save_numbers(existing_numbers, filename)
        
    except Exception as e:
        print(f"❌ Ошибка сохранения числа: {e}")

def display_results(current_values, new_numbers_list, config):
    """Отображает результаты в улучшенном формате"""
    clear_screen()
    
    # Системная информация
    system_info = get_system_info()
    print(f"🖥️  Система: {system_info['platform']} | Python: {system_info['python_version']}")
    print(f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Текущие показания
    print("=== 📊 Текущие показания ===")
    timer_data = []
    for i, value in enumerate(current_values):
        status = "✅" if value != "?" else "❌"
        timer_data.append([f"Строка {i + 1}", value, status])
    
    print(tabulate(timer_data, headers=["Позиция", "Значение", "Статус"], tablefmt="grid"))
    
    # История
    print("\n=== 📈 История чисел ===")
    if not new_numbers_list:
        print("📭 Нет данных")
    else:
        history_data = []
        for i, entry in enumerate(new_numbers_list[:config['history_size']]):
            if isinstance(entry, dict):
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
                history_data.append([i + 1, entry['number'], timestamp])
            else:
                history_data.append([i + 1, entry, "---"])
        
        print(tabulate(history_data, headers=["№", "Число", "Время"], tablefmt="grid"))
    
    # Статистика
    print(f"\n📊 Статистика: {len(new_numbers_list)} чисел | Интервал: {config['scan_interval']}с")
    print("⚙️  Нажмите Ctrl+C для выхода")

def view_saved_data(config):
    """Просмотр сохраненных данных"""
    try:
        if not os.path.exists(config['output_file']):
            print(f"❌ Файл {config['output_file']} не найден")
            return
        
        with open(config['output_file'], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        numbers = data.get('numbers', [])
        
        if not numbers:
            print("📭 Нет сохраненных данных")
            return
        
        print(f"📊 Данные из файла: {config['output_file']}")
        print(f"📅 Последнее обновление: {data.get('last_updated', 'Неизвестно')}")
        print(f"🔢 Всего чисел: {data.get('total_count', len(numbers))}")
        
        if 'system_info' in data:
            print(f"🖥️  Система: {data['system_info'].get('platform', 'Неизвестно')}")
        print()
        
        # Показываем данные
        display_data = []
        for i, entry in enumerate(numbers[:50]):  # Показываем до 50 записей
            if isinstance(entry, dict):
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%d.%m.%Y %H:%M:%S")
                display_data.append([i + 1, entry['number'], timestamp])
            else:
                display_data.append([i + 1, entry, "---"])
        
        print(tabulate(display_data, headers=["№", "Число", "Время"], tablefmt="grid"))
        
        if len(numbers) > 50:
            print(f"\n... и еще {len(numbers) - 50} записей")
        
    except Exception as e:
        print(f"❌ Ошибка при просмотре данных: {e}")

def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(description='Универсальная программа распознавания чисел с экрана')
    parser.add_argument('--view', action='store_true', help='Просмотр сохраненных данных')
    parser.add_argument('--config', default='config.json', help='Файл конфигурации')
    parser.add_argument('--setup', action='store_true', help='Настройка программы')
    parser.add_argument('--debug', action='store_true', help='Режим отладки')
    
    args = parser.parse_args()
    
    # Настройка Tesseract
    if not setup_tesseract():
        sys.exit(1)
    
    # Загрузка конфигурации
    config = load_config(args.config)
    
    if args.debug:
        config['debug_mode'] = True
    
    if args.setup:
        print("🔧 Настройка программы...")
        config['history_size'] = int(input(f"Размер истории [{config['history_size']}]: ") or config['history_size'])
        config['scan_interval'] = float(input(f"Интервал сканирования [{config['scan_interval']}]: ") or config['scan_interval'])
        save_config(config, args.config)
        return
    
    if args.view:
        view_saved_data(config)
        return
    
    # Основная работа программы
    print("🚀 Запуск программы распознавания чисел...")
    print(f"📋 Конфигурация: {args.config}")
    
    # Загружаем существующие данные
    new_numbers_list = load_numbers(config['output_file'])
    print(f"📁 Загружено {len(new_numbers_list)} записей")
    
    # Выбираем область
    region = select_region(config)
    print(f"🎯 Область мониторинга: {region}")
    
    last_top = None
    
    try:
        print("🔄 Начало мониторинга...")
        while True:
            screenshot = pyautogui.screenshot(region=region)
            processed_img = preprocess_image(screenshot, config)
            
            digits = recognize_text(processed_img, config)
            current_top = digits[0]
            
            # Проверяем новое число
            if current_top != "?" and (last_top is None or current_top != last_top):
                save_single_number(current_top, config['output_file'])
                
                new_entry = {
                    'number': current_top,
                    'timestamp': datetime.now().isoformat(),
                    'id': len(new_numbers_list) + 1
                }
                new_numbers_list.insert(0, new_entry)
                
                last_top = current_top
                print(f"🔢 Новое число: {current_top}")
            
            display_results(digits, new_numbers_list, config)
            time.sleep(config['scan_interval'])
            
    except KeyboardInterrupt:
        print(f"\n✅ Программа завершена")
        print(f"📊 Всего обработано: {len(new_numbers_list)} чисел")
        print(f"💾 Данные сохранены в: {config['output_file']}")

if __name__ == "__main__":
    main()
