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
from colorama import init, Fore, Back, Style
from collections import defaultdict

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
    'region_file': 'region.json',
    'table_display': {
        'use_colors': True,
        'table_format': 'simple',  # Изменено с 'grid' на 'simple' для скорости
        'max_rows': 10,           # Уменьшено с 20 до 10
        'show_stats': False,      # Отключено по умолчанию
        'refresh_interval': 0.5   # Добавлен интервал обновления экрана
    },
    'thresholds': {
        'warning_time': 30.0,
        'critical_time': 50.0,
        'max_count_warning': 5
    },
    'stats_file': 'timer_stats.json',
    'performance': {
        'fast_mode': True,        # Быстрый режим
        'cache_data': True,       # Кэширование данных
        'minimal_display': False   # Минимальный вывод
    }
}

# Глобальные переменные для кэширования
_cached_data = {}
_last_update_time = 0
_colors_initialized = False

def init_colorama():
    """Инициализация colorama для цветного вывода (с кэшированием)"""
    global _colors_initialized
    if _colors_initialized:
        return True
    try:
        init(autoreset=True)
        _colors_initialized = True
        return True
    except Exception:
        return False

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

def get_number_color(number_str, config):
    """Определяет цвет для числа на основе его значения"""
    if not config['table_display']['use_colors']:
        return ""
    
    try:
        value = float(number_str.replace(':', '.'))
        if value >= config['thresholds']['critical_time']:
            return Fore.RED
        elif value >= config['thresholds']['warning_time']:
            return Fore.YELLOW
        else:
            return Fore.GREEN
    except:
        return ""

def get_counter_color(current_count, max_count, config):
    """Определение цвета счетчика на основе значений"""
    if not config['table_display']['use_colors'] or max_count == 0:
        return ""
    
    remaining = max_count - current_count
    if remaining <= 0:
        return Fore.RED
    elif remaining == 1:
        return Fore.GREEN
    elif remaining == 2:
        return Fore.YELLOW
    elif remaining <= config['thresholds']['max_count_warning']:
        return Fore.RED
    return ""

def load_stats_data(filename):
    """Загружает статистические данные из файла"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"⚠️ Ошибка загрузки статистики: {e}")
        return {}

def save_stats_data(stats_data, filename):
    """Сохраняет статистические данные в файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения статистики: {e}")
        return False

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
        
        # Обновляем счетчики серий
        series_filename = filename.replace('.json', '_series.json')
        update_series_counters(number, series_filename)
        
    except Exception as e:
        print(f"❌ Ошибка сохранения числа: {e}")

def update_series_counters(current_value, series_filename):
    """Обновляет счетчики серий для пользовательских меток"""
    try:
        # Конвертируем значение в число
        try:
            value = float(current_value.replace(':', '.'))
        except:
            return
        
        # Загружаем существующие счетчики
        series_data = load_series_data(series_filename)
        
        # Обновляем счетчики для каждой метки
        for mark in series_data['user_marks']:
            mark_str = str(mark)
            
            if value <= mark:
                # Значение не превысило метку - увеличиваем текущую серию
                series_data['current_series'][mark_str] = series_data['current_series'].get(mark_str, 0) + 1
                
                # Проверяем и обновляем максимальную серию
                current_count = series_data['current_series'][mark_str]
                max_count = series_data['max_series'].get(mark_str, 0)
                
                if current_count > max_count:
                    series_data['max_series'][mark_str] = current_count
            else:
                # Значение превысило метку - сбрасываем текущую серию
                series_data['current_series'][mark_str] = 0
        
        # Сохраняем обновленные счетчики
        save_stats_data(series_data, series_filename)
        
    except Exception as e:
        print(f"⚠️ Ошибка при обновлении счетчиков: {e}")

def load_series_data(filename):
    """Загружает данные счетчиков серий"""
    try:
        data = load_stats_data(filename)
        if not data:
            # Инициализируем стандартные метки если файл пустой
            return {
                'user_marks': [3.0, 4.0, 5.0, 6.0, 7.0],
                'max_series': {str(mark): 0 for mark in [3.0, 4.0, 5.0, 6.0, 7.0]},
                'current_series': {str(mark): 0 for mark in [3.0, 4.0, 5.0, 6.0, 7.0]}
            }
        return data
    except:
        return {
            'user_marks': [3.0, 4.0, 5.0, 6.0, 7.0],
            'max_series': {str(mark): 0 for mark in [3.0, 4.0, 5.0, 6.0, 7.0]},
            'current_series': {str(mark): 0 for mark in [3.0, 4.0, 5.0, 6.0, 7.0]}
        }

def display_results(current_values, new_numbers_list, config):
    """Оптимизированное отображение результатов"""
    global _last_update_time
    
    # Проверяем интервал обновления экрана
    current_time = time.time()
    if current_time - _last_update_time < config['table_display'].get('refresh_interval', 0.5):
        return
    
    _last_update_time = current_time
    
    # Быстрый режим - минимальный вывод
    if config.get('performance', {}).get('fast_mode', False):
        display_fast_mode(current_values, new_numbers_list, config)
        return
    
    # Обычный режим (оптимизированный)
    clear_screen()
    
    # Инициализация цветов один раз
    colors_enabled = _colors_initialized and config['table_display']['use_colors']
    
    # Упрощенный заголовок
    if colors_enabled:
        print(f"{Fore.CYAN}📊 Мониторинг чисел - {datetime.now().strftime('%H:%M:%S')}{Style.RESET_ALL}")
    else:
        print(f"📊 Мониторинг чисел - {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    # Текущие показания (компактно)
    timer_data = []
    for i, value in enumerate(current_values[:3]):  # Показываем только 3 строки
        if value != "?":
            if colors_enabled:
                number_color = get_number_color(value, config)
                colored_value = f"{number_color}{value}{Style.RESET_ALL}"
                status = f"{Fore.GREEN}✓{Style.RESET_ALL}"
            else:
                colored_value = value
                status = "✓"
        else:
            if colors_enabled:
                colored_value = f"{Fore.RED}{value}{Style.RESET_ALL}"
                status = f"{Fore.RED}✗{Style.RESET_ALL}"
            else:
                colored_value = value
                status = "✗"
        
        timer_data.append([f"Строка {i + 1}", colored_value, status])
    
    print(tabulate(timer_data, headers=["Позиция", "Значение", "Статус"], 
                   tablefmt=config['table_display']['table_format']))
    
    # История (ограниченная)
    if new_numbers_list:
        print(f"\n📈 Последние числа:")
        max_rows = min(len(new_numbers_list), 5)  # Показываем только 5 последних
        
        history_data = []
        for i, entry in enumerate(new_numbers_list[:max_rows]):
            if isinstance(entry, dict):
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
                number = entry['number']
                if colors_enabled:
                    number_color = get_number_color(number, config)
                    colored_number = f"{number_color}{number}{Style.RESET_ALL}"
                else:
                    colored_number = number
                history_data.append([i + 1, colored_number, timestamp])
        
        print(tabulate(history_data, headers=["№", "Число", "Время"], 
                       tablefmt=config['table_display']['table_format']))
    
    # Управление
    print(f"\n⚙️ Управление: Ctrl+C=Выход | Пробел=Замер")

def display_fast_mode(current_values, new_numbers_list, config):
    """Сверхбыстрый режим отображения"""
    # Очищаем только одну строку, а не весь экран
    print(f"\r🔍 {datetime.now().strftime('%H:%M:%S')} | ", end="")
    
    # Показываем только текущие значения
    for i, value in enumerate(current_values[:3]):
        if value != "?":
            print(f"#{i+1}:{value} ", end="")
        else:
            print(f"#{i+1}:? ", end="")
    
    # Показываем последнее число
    if new_numbers_list and isinstance(new_numbers_list[0], dict):
        last_number = new_numbers_list[0]['number']
        print(f"| Последнее: {last_number}", end="")
    
    print("     ", end="", flush=True)  # Очищаем остаток строки

def get_cached_data(key, loader_func, cache_duration=5.0):
    """Универсальная функция кэширования данных"""
    global _cached_data
    
    current_time = time.time()
    cache_key = f"{key}_data"
    time_key = f"{key}_time"
    
    # Проверяем актуальность кэша
    if (cache_key in _cached_data and 
        time_key in _cached_data and 
        current_time - _cached_data[time_key] < cache_duration):
        return _cached_data[cache_key]
    
    # Обновляем кэш
    try:
        data = loader_func()
        _cached_data[cache_key] = data
        _cached_data[time_key] = current_time
        return data
    except Exception:
        return _cached_data.get(cache_key, {})

def load_numbers_cached(filename, config):
    """Кэшированная загрузка чисел"""
    if config.get('performance', {}).get('cache_data', True):
        return get_cached_data('numbers', lambda: load_numbers(filename))
    return load_numbers(filename)

def load_series_data_cached(filename, config):
    """Кэшированная загрузка данных серий"""
    if config.get('performance', {}).get('cache_data', True):
        return get_cached_data('series', lambda: load_series_data(filename))
    return load_series_data(filename)

def view_saved_data(config):
    """Просмотр сохраненных данных с цветным форматированием"""
    try:
        # Инициализация цветов
        colors_enabled = init_colorama() and config['table_display']['use_colors']
        header_color = Fore.CYAN if colors_enabled else ""
        reset_color = Style.RESET_ALL if colors_enabled else ""
        
        if not os.path.exists(config['output_file']):
            print(f"{Fore.RED if colors_enabled else ''}❌ Файл {config['output_file']} не найден{reset_color}")
            return
        
        with open(config['output_file'], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        numbers = data.get('numbers', [])
        
        if not numbers:
            print(f"{Fore.YELLOW if colors_enabled else ''}📭 Нет сохраненных данных{reset_color}")
            return
        
        # Заголовок с информацией о файле
        print(f"{header_color}📊 Данные из файла: {config['output_file']}{reset_color}")
        print(f"{header_color}📅 Последнее обновление: {data.get('last_updated', 'Неизвестно')}{reset_color}")
        print(f"{header_color}🔢 Всего чисел: {data.get('total_count', len(numbers))}{reset_color}")
        
        if 'system_info' in data:
            print(f"{header_color}🖥️  Система: {data['system_info'].get('platform', 'Неизвестно')}{reset_color}")
        print()
        
        # Анализ данных для статистики
        try:
            recent_values = []
            for entry in numbers[:10]:
                if isinstance(entry, dict):
                    val = float(entry['number'].replace(':', '.'))
                    recent_values.append(val)
            
            if recent_values:
                avg_recent = sum(recent_values) / len(recent_values)
                min_val = min(recent_values)
                max_val = max(recent_values)
                
                # Статистическая таблица
                print(f"{header_color}=== 📈 Анализ данных ==={reset_color}")
                stats_analysis = [
                    ["Среднее (10 последних)", f"{Fore.BLUE if colors_enabled else ''}{avg_recent:.2f}{reset_color}"],
                    ["Минимальное значение", f"{Fore.GREEN if colors_enabled else ''}{min_val:.2f}{reset_color}"],
                    ["Максимальное значение", f"{Fore.RED if colors_enabled else ''}{max_val:.2f}{reset_color}"],
                    ["Диапазон", f"{max_val - min_val:.2f}"]
                ]
                print(tabulate(stats_analysis, headers=["Метрика", "Значение"], 
                              tablefmt=config['table_display']['table_format']))
                print()
        except:
            pass
        
        # Основные данные с цветным кодированием
        print(f"{header_color}=== 📊 История данных ==={reset_color}")
        display_data = []
        max_display = min(len(numbers), config['table_display']['max_rows'])
        
        for i, entry in enumerate(numbers[:max_display]):
            if isinstance(entry, dict):
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%d.%m.%Y %H:%M:%S")
                
                # Применяем цветовое кодирование
                number_color = get_number_color(entry['number'], config) if colors_enabled else ""
                colored_number = f"{number_color}{entry['number']}{reset_color}"
                
                # Цвет для индекса (последние 5 записей выделяем)
                index_color = Fore.BLUE if colors_enabled and i < 5 else ""
                colored_index = f"{index_color}{i + 1}{reset_color}"
                
                # Цвет для времени (последние 24 часа выделяем)
                try:
                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    hours_ago = (datetime.now() - entry_time).total_seconds() / 3600
                    time_color = Fore.GREEN if colors_enabled and hours_ago < 24 else ""
                    colored_time = f"{time_color}{timestamp}{reset_color}"
                except:
                    colored_time = timestamp
                
                display_data.append([colored_index, colored_number, colored_time])
            else:
                display_data.append([i + 1, entry, "---"])
        
        print(tabulate(display_data, headers=["№", "Число", "Время"], 
                       tablefmt=config['table_display']['table_format']))
        
        if len(numbers) > max_display:
            remaining = len(numbers) - max_display
            print(f"\n{Fore.YELLOW if colors_enabled else ''}... и еще {remaining} записей{reset_color}")
        
        # Таблица пользовательских меток
        print(f"\n{header_color}=== 🎯 Пользовательские метки ==={reset_color}")
        series_filename = config['output_file'].replace('.json', '_series.json')
        series_data = load_series_data(series_filename)
        
        marks_table = []
        for mark in sorted(series_data['user_marks']):
            mark_str = str(mark)
            max_series = series_data['max_series'].get(mark_str, 0)
            current_series = series_data['current_series'].get(mark_str, 0)
            
            # Цветовое кодирование для счетчиков
            max_color = Fore.BLUE if colors_enabled and max_series > 0 else ""
            current_color = get_counter_color(current_series, max_series, config) if colors_enabled else ""
            
            colored_max = f"{max_color}{max_series}{reset_color}"
            colored_current = f"{current_color}{current_series}{reset_color}"
            
            marks_table.append([mark, colored_max, colored_current])
        
        print(tabulate(marks_table, headers=["Метка", "Макс.серия", "Текущ.серия"], 
                       tablefmt=config['table_display']['table_format']))
        
        # Кнопки управления
        print(f"\n{Fore.GREEN if colors_enabled else ''}⚙️  Доступные действия:{reset_color}")
        print("   [R] - Обновить данные")
        print("   [S] - Показать статистику")
        print("   [Q] - Выйти")
        
    except Exception as e:
        print(f"{Fore.RED if colors_enabled else ''}❌ Ошибка при просмотре данных: {e}{reset_color}")

def show_full_stats(config):
    """Показать расширенную статистику"""
    try:
        # Инициализация цветов
        colors_enabled = init_colorama() and config['table_display']['use_colors']
        header_color = Fore.CYAN if colors_enabled else ""
        reset_color = Style.RESET_ALL if colors_enabled else ""
        
        if not os.path.exists(config['output_file']):
            print(f"{Fore.RED if colors_enabled else ''}❌ Файл данных не найден{reset_color}")
            return
        
        with open(config['output_file'], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        numbers = data.get('numbers', [])
        
        if not numbers:
            print(f"{Fore.YELLOW if colors_enabled else ''}📭 Нет данных для анализа{reset_color}")
            return
        
        print(f"{header_color}=== 📊 Расширенная статистика ==={reset_color}")
        
        # Анализ всех данных
        all_values = []
        for entry in numbers:
            if isinstance(entry, dict):
                try:
                    val = float(entry['number'].replace(':', '.'))
                    all_values.append(val)
                except:
                    continue
        
        if all_values:
            # Основная статистика
            total = len(all_values)
            avg_val = sum(all_values) / len(all_values)
            min_val = min(all_values)
            max_val = max(all_values)
            
            # Медиана
            sorted_vals = sorted(all_values)
            median_val = sorted_vals[len(sorted_vals) // 2]
            
            # Диапазоны
            range_val = max_val - min_val
            
            # Количество в диапазонах
            low_count = sum(1 for v in all_values if v < config['thresholds']['warning_time'])
            medium_count = sum(1 for v in all_values if config['thresholds']['warning_time'] <= v < config['thresholds']['critical_time'])
            high_count = sum(1 for v in all_values if v >= config['thresholds']['critical_time'])
            
            # Основная таблица
            main_stats = [
                ["Всего записей", f"{Fore.BLUE if colors_enabled else ''}{total}{reset_color}"],
                ["Среднее значение", f"{avg_val:.2f}"],
                ["Медиана", f"{median_val:.2f}"],
                ["Минимум", f"{Fore.GREEN if colors_enabled else ''}{min_val:.2f}{reset_color}"],
                ["Максимум", f"{Fore.RED if colors_enabled else ''}{max_val:.2f}{reset_color}"],
                ["Диапазон", f"{range_val:.2f}"],
                ["Стандартное отклонение", f"{(sum((x - avg_val) ** 2 for x in all_values) / len(all_values)) ** 0.5:.2f}"]
            ]
            
            print(tabulate(main_stats, headers=["Метрика", "Значение"], 
                          tablefmt=config['table_display']['table_format']))
            
            # Распределение по диапазонам
            print(f"\n{header_color}=== 📈 Распределение по диапазонам ==={reset_color}")
            distribution_stats = [
                [f"< {config['thresholds']['warning_time']}", f"{Fore.GREEN if colors_enabled else ''}{low_count}{reset_color}", f"{low_count/total*100:.1f}%"],
                [f"{config['thresholds']['warning_time']} - {config['thresholds']['critical_time']}", f"{Fore.YELLOW if colors_enabled else ''}{medium_count}{reset_color}", f"{medium_count/total*100:.1f}%"],
                [f"> {config['thresholds']['critical_time']}", f"{Fore.RED if colors_enabled else ''}{high_count}{reset_color}", f"{high_count/total*100:.1f}%"]
            ]
            
            print(tabulate(distribution_stats, headers=["Диапазон", "Количество", "Процент"], 
                          tablefmt=config['table_display']['table_format']))
            
            # Топ-10 самых больших и маленьких значений
            print(f"\n{header_color}=== 🔝 Топ-10 максимальных ==={reset_color}")
            top_max = sorted(all_values, reverse=True)[:10]
            top_max_data = [[i+1, f"{Fore.RED if colors_enabled else ''}{val:.2f}{reset_color}"] for i, val in enumerate(top_max)]
            print(tabulate(top_max_data, headers=["Место", "Значение"], 
                          tablefmt=config['table_display']['table_format']))
            
            print(f"\n{header_color}=== 🔻 Топ-10 минимальных ==={reset_color}")
            top_min = sorted(all_values)[:10]
            top_min_data = [[i+1, f"{Fore.GREEN if colors_enabled else ''}{val:.2f}{reset_color}"] for i, val in enumerate(top_min)]
            print(tabulate(top_min_data, headers=["Место", "Значение"], 
                          tablefmt=config['table_display']['table_format']))
            
    except Exception as e:
        print(f"{Fore.RED if colors_enabled else ''}❌ Ошибка при анализе статистики: {e}{reset_color}")

def clear_stats(config):
    """Очистить файл статистики"""
    try:
        colors_enabled = init_colorama() and config['table_display']['use_colors']
        
        if os.path.exists(config['stats_file']):
            os.remove(config['stats_file'])
            print(f"{Fore.GREEN if colors_enabled else ''}✅ Файл статистики очищен{Style.RESET_ALL if colors_enabled else ''}")
        else:
            print(f"{Fore.YELLOW if colors_enabled else ''}⚠️ Файл статистики не найден{Style.RESET_ALL if colors_enabled else ''}")
    except Exception as e:
        print(f"{Fore.RED if colors_enabled else ''}❌ Ошибка при очистке статистики: {e}{Style.RESET_ALL if colors_enabled else ''}")

def export_to_csv(config, filename):
    """Экспортировать данные в CSV"""
    try:
        import csv
        colors_enabled = init_colorama() and config['table_display']['use_colors']
        
        if not os.path.exists(config['output_file']):
            print(f"{Fore.RED if colors_enabled else ''}❌ Файл данных не найден{Style.RESET_ALL if colors_enabled else ''}")
            return
        
        with open(config['output_file'], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        numbers = data.get('numbers', [])
        
        if not numbers:
            print(f"{Fore.YELLOW if colors_enabled else ''}📭 Нет данных для экспорта{Style.RESET_ALL if colors_enabled else ''}")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Номер', 'Значение', 'Время', 'ID']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for i, entry in enumerate(numbers):
                if isinstance(entry, dict):
                    writer.writerow({
                        'Номер': i + 1,
                        'Значение': entry['number'],
                        'Время': entry['timestamp'],
                        'ID': entry.get('id', i + 1)
                    })
                else:
                    writer.writerow({
                        'Номер': i + 1,
                        'Значение': entry,
                        'Время': 'N/A',
                        'ID': i + 1
                    })
        
        print(f"{Fore.GREEN if colors_enabled else ''}✅ Данные экспортированы в файл: {filename}{Style.RESET_ALL if colors_enabled else ''}")
        print(f"{Fore.BLUE if colors_enabled else ''}📊 Экспортировано записей: {len(numbers)}{Style.RESET_ALL if colors_enabled else ''}")
        
    except Exception as e:
        print(f"{Fore.RED if colors_enabled else ''}❌ Ошибка при экспорте: {e}{Style.RESET_ALL if colors_enabled else ''}")

def show_series_counters(config):
    """Показать только таблицу счетчиков серий"""
    try:
        colors_enabled = init_colorama() and config['table_display']['use_colors']
        header_color = Fore.CYAN if colors_enabled else ""
        reset_color = Style.RESET_ALL if colors_enabled else ""
        
        print(f"{header_color}🎯 Пользовательские метки{reset_color}")
        print("=" * 50)
        
        series_filename = config['output_file'].replace('.json', '_series.json')
        series_data = load_series_data(series_filename)
        
        marks_table = []
        for mark in sorted(series_data['user_marks']):
            mark_str = str(mark)
            max_series = series_data['max_series'].get(mark_str, 0)
            current_series = series_data['current_series'].get(mark_str, 0)
            
            # Цветовое кодирование для счетчиков
            max_color = Fore.BLUE if colors_enabled and max_series > 0 else ""
            current_color = get_counter_color(current_series, max_series, config) if colors_enabled else ""
            
            colored_max = f"{max_color}{max_series}{reset_color}"
            colored_current = f"{current_color}{current_series}{reset_color}"
            
            marks_table.append([mark, colored_max, colored_current])
        
        print(tabulate(marks_table, headers=["Метка", "Макс.серия", "Текущ.серия"], 
                       tablefmt=config['table_display']['table_format']))
        
        print(f"\n{Fore.GREEN if colors_enabled else ''}📊 Объяснение:{reset_color}")
        print("   Макс.серия - рекорд подряд НЕ превысивших метку")
        print("   Текущ.серия - текущая серия НЕ превысивших метку")
        print("   Серия сбрасывается при превышении метки")
        
    except Exception as e:
        print(f"{Fore.RED if colors_enabled else ''}❌ Ошибка при отображении счетчиков: {e}{Style.RESET_ALL if colors_enabled else ''}")

def clear_series_counters(config):
    """Сбросить счетчики серий"""
    try:
        colors_enabled = init_colorama() and config['table_display']['use_colors']
        
        series_filename = config['output_file'].replace('.json', '_series.json')
        
        if os.path.exists(series_filename):
            os.remove(series_filename)
            print(f"{Fore.GREEN if colors_enabled else ''}✅ Счетчики серий сброшены{Style.RESET_ALL if colors_enabled else ''}")
        else:
            print(f"{Fore.YELLOW if colors_enabled else ''}⚠️ Файл счетчиков не найден{Style.RESET_ALL if colors_enabled else ''}")
            
    except Exception as e:
        print(f"{Fore.RED if colors_enabled else ''}❌ Ошибка при сбросе счетчиков: {e}{Style.RESET_ALL if colors_enabled else ''}")

def clear_cache():
    """Очистка кэша данных"""
    global _cached_data
    _cached_data.clear()
    print("🧹 Кэш очищен")

def toggle_performance_mode(config):
    """Переключение режима производительности"""
    current_mode = config.get('performance', {}).get('fast_mode', True)
    config['performance']['fast_mode'] = not current_mode
    
    mode_name = "быстрый" if config['performance']['fast_mode'] else "обычный"
    print(f"⚡ Переключен на {mode_name} режим")
    
    # Обновляем настройки отображения
    if config['performance']['fast_mode']:
        config['table_display']['refresh_interval'] = 0.3
        config['table_display']['max_rows'] = 5
        config['scan_interval'] = 0.6
    else:
        config['table_display']['refresh_interval'] = 0.5
        config['table_display']['max_rows'] = 10
        config['scan_interval'] = 1.0
    
    return config

def main():
    """Основная функция программы"""
    parser = argparse.ArgumentParser(description='Универсальная программа распознавания чисел с экрана')
    parser.add_argument('--view', action='store_true', help='Просмотр сохраненных данных')
    parser.add_argument('--config', default='config.json', help='Файл конфигурации')
    parser.add_argument('--setup', action='store_true', help='Настройка программы')
    parser.add_argument('--debug', action='store_true', help='Режим отладки')
    parser.add_argument('--stats', action='store_true', help='Просмотр расширенной статистики')
    parser.add_argument('--series', action='store_true', help='Просмотр счетчиков серий')
    parser.add_argument('--clear-stats', action='store_true', help='Очистить файл статистики')
    parser.add_argument('--clear-series', action='store_true', help='Сбросить счетчики серий')
    parser.add_argument('--clear-cache', action='store_true', help='Очистить кэш данных')
    parser.add_argument('--fast-mode', action='store_true', help='Включить быстрый режим')
    parser.add_argument('--normal-mode', action='store_true', help='Включить обычный режим')
    parser.add_argument('--export', type=str, help='Экспортировать данные в CSV файл')
    
    args = parser.parse_args()
    
    # Настройка Tesseract
    if not setup_tesseract():
        sys.exit(1)
    
    # Загрузка конфигурации
    config = load_config(args.config)
    
    if args.debug:
        config['debug_mode'] = True
    
    if args.clear_cache:
        clear_cache()
        return
    
    if args.fast_mode:
        config['performance']['fast_mode'] = True
        print("⚡ Быстрый режим включен")
        save_config(config, args.config)
        return
    
    if args.normal_mode:
        config['performance']['fast_mode'] = False
        print("🐌 Обычный режим включен")
        save_config(config, args.config)
        return
    
    if args.setup:
        print("🔧 Настройка программы...")
        config['history_size'] = int(input(f"Размер истории [{config['history_size']}]: ") or config['history_size'])
        config['scan_interval'] = float(input(f"Интервал сканирования [{config['scan_interval']}]: ") or config['scan_interval'])
        
        # Настройка режима производительности
        fast_mode = input(f"Быстрый режим (y/n) [{config.get('performance', {}).get('fast_mode', True)}]: ").lower()
        if fast_mode in ['y', 'yes', 'да']:
            config['performance']['fast_mode'] = True
        elif fast_mode in ['n', 'no', 'нет']:
            config['performance']['fast_mode'] = False
        
        save_config(config, args.config)
        return
    
    if args.view:
        view_saved_data(config)
        return
    
    if args.stats:
        show_full_stats(config)
        return
    
    if args.series:
        show_series_counters(config)
        return
    
    if args.clear_stats:
        clear_stats(config)
        return
    
    if args.clear_series:
        clear_series_counters(config)
        return
    
    if args.export:
        export_to_csv(config, args.export)
        return
    
    # Основная работа программы
    print("🚀 Запуск программы распознавания чисел...")
    print(f"📋 Конфигурация: {args.config}")
    
    # Инициализация цветов
    init_colorama()
    
    # Показываем текущий режим
    mode_name = "⚡ быстрый" if config.get('performance', {}).get('fast_mode', True) else "🐌 обычный"
    print(f"🔧 Режим работы: {mode_name}")
    
    if config.get('performance', {}).get('fast_mode', True):
        print("💡 Быстрый режим: упрощенный интерфейс, кэширование, ускоренное сканирование")
        print("💡 Для переключения используйте: python3 123456789000.py --normal-mode")
    else:
        print("💡 Обычный режим: полный интерфейс, детальная статистика")
        print("💡 Для переключения используйте: python3 123456789000.py --fast-mode")
    
    # Загружаем существующие данные
    new_numbers_list = load_numbers_cached(config['output_file'], config)
    print(f"📁 Загружено {len(new_numbers_list)} записей")
    
    # Выбираем область
    region = select_region(config)
    print(f"🎯 Область мониторинга: {region}")
    
    last_top = None
    save_counter = 0  # Счетчик для уменьшения частоты сохранений
    
    try:
        print("🔄 Начало мониторинга...")
        print("💡 Советы по производительности:")
        if config.get('performance', {}).get('fast_mode', True):
            print("   • Быстрый режим активен - данные обновляются каждые 0.3с")
            print("   • Сохранение происходит не при каждом изменении")
            print("   • Для полной статистики переключитесь в обычный режим")
        print("   • Ctrl+C для выхода")
        print()
        
        while True:
            screenshot = pyautogui.screenshot(region=region)
            processed_img = preprocess_image(screenshot, config)

            digits = recognize_text(processed_img, config)
            current_top = digits[0]

            # Проверяем новое число
            if current_top != "?" and (last_top is None or current_top != last_top):
                # Сохраняем только каждое 3-е изменение для ускорения
                if config.get('performance', {}).get('fast_mode', True):
                    save_counter += 1
                    if save_counter >= 3:
                        save_single_number(current_top, config['output_file'])
                        save_counter = 0
                else:
                    save_single_number(current_top, config['output_file'])
                
                new_entry = {
                    'number': current_top,
                    'timestamp': datetime.now().isoformat(),
                    'id': len(new_numbers_list) + 1
                }
                new_numbers_list.insert(0, new_entry)
                
                # Ограничиваем размер списка в памяти
                if len(new_numbers_list) > config.get('history_size', 10) * 2:
                    new_numbers_list = new_numbers_list[:config.get('history_size', 10)]
                
                last_top = current_top
                if not config.get('performance', {}).get('fast_mode', True):
                    print(f"🔢 Новое число: {current_top}")

            display_results(digits, new_numbers_list, config)
            
            # Динамический интервал сканирования
            scan_interval = config['scan_interval']
            if config.get('performance', {}).get('fast_mode', True):
                scan_interval = max(0.3, scan_interval * 0.7)  # Уменьшаем интервал в быстром режиме
            
            time.sleep(scan_interval)

    except KeyboardInterrupt:
        print(f"\n✅ Программа завершена")
        print(f"📊 Всего обработано: {len(new_numbers_list)} чисел")
        print(f"💾 Данные сохранены в: {config['output_file']}")

if __name__ == "__main__":
        main()
