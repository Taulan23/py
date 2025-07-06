import time
import json
from collections import defaultdict
import os
import keyboard
from tabulate import tabulate
import threading
from colorama import init, Fore, Back, Style
import numpy as np
import sounddevice as sd
import warnings
import pytesseract
from PIL import ImageGrab
import cv2
import pyautogui

class TimerApp:
    def __init__(self):
        init()
        self.running = False
        self.sound_mode = False
        self.screen_capture_mode = False
        self.start_time = None
        self.elapsed_time = 0.0
        self.stats_file = "timer_stats.json"
        self.stats = defaultdict(int)
        self.display_event = threading.Event()
        self.time_limit = 60.0
        self.user_ranges = []
        self.max_values = {}
        self.last_exceeded = {}
        self.since_last_exceeded = {}
        self.audio_threshold = 0.05
        self.sample_rate = 44100
        self.audio_stream = None
        self.input_device = None
        self.silence_counter = 0
        self.capture_area = None
        self.last_display_time = 0
        
        # Настройка пути к Tesseract OCR (измените на свой)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        self.setup_terminal()
        self.setup_audio()
        self.setup_user_ranges()

    def setup_terminal(self):
        if os.name == 'nt':
            os.system('mode con: cols=140 lines=50')

    def setup_audio(self):
        """Настройка аудиоустройства с обработкой ошибок"""
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if not input_devices:
                print(Fore.YELLOW + "\nАудиовходы не найдены! Режим по звуку недоступен." + Style.RESET_ALL)
                return

            print(Fore.CYAN + "\nДоступные аудиовходы:" + Style.RESET_ALL)
            for i, dev in enumerate(input_devices):
                print(f"{i}: {dev['name']}")

            while True:
                choice = input("\nВыберите устройство (Enter - по умолчанию): ")
                if not choice:
                    self.input_device = None
                    print("Используется устройство по умолчанию")
                    break
                try:
                    self.input_device = int(choice)
                    if 0 <= self.input_device < len(input_devices):
                        break
                    print(Fore.RED + "Неверный номер устройства!" + Style.RESET_ALL)
                except ValueError:
                    print(Fore.RED + "Введите число!" + Style.RESET_ALL)

            # Тестовая проверка аудио
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                test_stream = sd.InputStream(
                    device=self.input_device, 
                    channels=1, 
                    samplerate=self.sample_rate,
                    blocksize=1024
                )
                test_stream.start()
                test_stream.stop()
                test_stream.close()

        except Exception as e:
            print(Fore.RED + f"\nОшибка аудио: {str(e)}" + Style.RESET_ALL)
            self.input_device = None

    def setup_user_ranges(self):
        print(Fore.CYAN + "\nУстановите 5 временных меток (в секундах):" + Style.RESET_ALL)
        for i in range(5):
            while True:
                try:
                    val = float(input(f"Метка {i+1}: "))
                    if val <= 0:
                        print(Fore.RED + "Значение должно быть больше 0" + Style.RESET_ALL)
                        continue
                    self.user_ranges.append(val)
                    self.max_values[val] = 0
                    self.last_exceeded[val] = None
                    self.since_last_exceeded[val] = 0
                    break
                except ValueError:
                    print(Fore.RED + "Введите число (например: 1.23)" + Style.RESET_ALL)

        self.user_ranges = sorted(list(set(self.user_ranges)))
        print(Fore.GREEN + "\nУстановленные метки: " + ", ".join(f"{x:.2f}" for x in self.user_ranges) + Style.RESET_ALL)
        
        # Настройка чувствительности
        while True:
            try:
                thresh = float(input("\nПорог громкости (0.01-0.5, по умолчанию 0.05): ") or "0.05")
                if 0.01 <= thresh <= 0.5:
                    self.audio_threshold = thresh
                    break
                print(Fore.RED + "Допустимый диапазон: 0.01-0.5" + Style.RESET_ALL)
            except ValueError:
                print(Fore.RED + "Введите число!" + Style.RESET_ALL)

        input("\nНажмите Enter для старта...")
        self.clear_console()

    def setup_screen_capture(self):
        """Настройка области захвата экрана"""
        print(Fore.CYAN + "\nРежим настройки захвата экрана:" + Style.RESET_ALL)
        print("1. Откройте страницу с таймером в браузере")
        print("2. Наведите курсор в левый верхний угол области таймера")
        input("3. Нажмите Enter чтобы запомнить первую точку...")
        
        x1, y1 = pyautogui.position()
        print(f"Первая точка: {x1}, {y1}")
        
        print("4. Наведите курсор в правый нижний угол области таймера")
        input("5. Нажмите Enter чтобы запомнить вторую точку...")
        
        x2, y2 = pyautogui.position()
        print(f"Вторая точка: {x2}, {y2}")
        
        self.capture_area = (x1, y1, x2, y2)
        print(Fore.GREEN + f"\nОбласть захвата установлена: {self.capture_area}" + Style.RESET_ALL)
        input("Нажмите Enter чтобы продолжить...")
        self.clear_console()

    def read_time_from_screen(self):
        """Чтение времени с экрана с помощью OCR"""
        if not self.capture_area:
            return None
            
        try:
            # Захват области экрана
            screenshot = ImageGrab.grab(bbox=self.capture_area)
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Улучшение изображения для распознавания
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            # Распознавание текста
            custom_config = r'--oem 3 --psm 6 outputbase digits'
            text = pytesseract.image_to_string(thresh, config=custom_config)
            
            # Парсинг времени (формат MM:SS.ss или HH:MM:SS)
            time_str = text.strip().replace(',', '.')
            time_parts = time_str.split(':')
            
            if len(time_parts) == 3:  # HH:MM:SS
                hours, mins, secs = map(float, time_parts)
                return hours * 3600 + mins * 60 + secs
            elif len(time_parts) == 2:  # MM:SS.ss
                mins, secs = map(float, time_parts)
                return mins * 60 + secs
                
            return None
        except Exception as e:
            print(Fore.RED + f"\nОшибка распознавания времени: {str(e)}" + Style.RESET_ALL)
            return None

    def audio_callback(self, indata, frames, time, status):
        """Обработчик звука с защитой от ошибок"""
        try:
            if not self.sound_mode:
                return

            volume = np.linalg.norm(indata) * 10
            if volume > self.audio_threshold:
                self.silence_counter = 0
                if not self.running:
                    self.start()
            else:
                self.silence_counter += frames / self.sample_rate
                if self.running and self.silence_counter > 1.0:  # 1 секунда тишины
                    self.stop()
        except Exception as e:
            print(Fore.RED + f"\nAudio error: {str(e)}" + Style.RESET_ALL)
            self.stop_audio()

    def start_audio(self):
        """Безопасный запуск аудиопотока"""
        try:
            if self.input_device is None:
                print(Fore.YELLOW + "\nАудиоустройство не настроено!" + Style.RESET_ALL)
                return False

            self.audio_stream = sd.InputStream(
                device=self.input_device,
                samplerate=self.sample_rate,
                channels=1,
                callback=self.audio_callback,
                blocksize=2048
            )
            self.audio_stream.start()
            return True
        except Exception as e:
            print(Fore.RED + f"\nНе удалось запустить аудио: {str(e)}" + Style.RESET_ALL)
            return False

    def stop_audio(self):
        """Корректная остановка аудио"""
        if self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except:
                pass
            finally:
                self.audio_stream = None

    def toggle_audio_mode(self):
        """Переключение режима с защитой"""
        if self.sound_mode:
            self.sound_mode = False
            self.stop_audio()
            print(Fore.YELLOW + "\nРежим звука ВЫКЛ" + Style.RESET_ALL)
        else:
            if self.start_audio():
                self.sound_mode = True
                print(Fore.GREEN + "\nРежим звука ВКЛ (ожидание сигнала...)" + Style.RESET_ALL)
            else:
                self.sound_mode = False
                print(Fore.RED + "\nОшибка активации режима звука" + Style.RESET_ALL)

    def toggle_screen_capture_mode(self):
        """Переключение режима захвата экрана"""
        if self.screen_capture_mode:
            self.screen_capture_mode = False
            print(Fore.YELLOW + "\nРежим захвата экрана ВЫКЛ" + Style.RESET_ALL)
        else:
            self.setup_screen_capture()
            self.screen_capture_mode = True
            print(Fore.GREEN + "\nРежим захвата экрана ВКЛ" + Style.RESET_ALL)

    def load_stats(self):
        """Загрузка статистики из файла"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    saved_data = json.load(f)
                    self.stats = defaultdict(int, {float(k): v for k, v in saved_data.get('stats', {}).items()})
                    self.max_values = {float(k): v for k, v in saved_data.get('max_values', {}).items()}
                    self.last_exceeded = {float(k): (float(v) if v else None) for k, v in saved_data.get('last_exceeded', {}).items()}
                    self.since_last_exceeded = {float(k): v for k, v in saved_data.get('since_last_exceeded', {}).items()}
        except Exception as e:
            print(Fore.RED + f"\nОшибка загрузки статистики: {str(e)}" + Style.RESET_ALL)

    def save_stats(self):
        """Сохранение статистики в файл"""
        try:
            with open(self.stats_file, 'w') as f:
                data_to_save = {
                    'stats': {str(k): v for k, v in self.stats.items()},
                    'max_values': {str(k): v for k, v in self.max_values.items()},
                    'last_exceeded': {str(k): (str(v) if v else None) for k, v in self.last_exceeded.items()},
                    'since_last_exceeded': {str(k): v for k, v in self.since_last_exceeded.items()}
                }
                json.dump(data_to_save, f, indent=4)
        except Exception as e:
            print(Fore.RED + f"\nОшибка сохранения статистики: {str(e)}" + Style.RESET_ALL)

    def get_counter_color(self, current_count, max_count):
        """Определение цвета счетчика"""
        if max_count == 0:
            return Style.RESET_ALL
        remaining = max_count - current_count
        if remaining <= 0:
            return Fore.RED
        elif remaining == 1:
            return Fore.GREEN
        elif remaining == 2:
            return Fore.YELLOW
        elif remaining <= 3:
            return Fore.RED
        return Style.RESET_ALL

    def start_stop(self):
        """Обработчик старта/остановки"""
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        """Запуск таймера"""
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.display_event.set()
            threading.Thread(target=self.update_display, daemon=True).start()

    def stop(self):
        """Остановка таймера"""
        if self.running:
            self.running = False
            self.display_event.clear()
            self.elapsed_time = time.time() - self.start_time
            self.process_result()

    def process_result(self):
        """Обработка результатов замера"""
        current_time = min(self.elapsed_time, self.time_limit)
        formatted_time = int(current_time * 100) / 100
        
        self.stats[formatted_time] += 1
        
        for time_val in self.user_ranges:
            if current_time >= time_val:
                self.last_exceeded[time_val] = formatted_time
                self.since_last_exceeded[time_val] = 0
            else:
                self.since_last_exceeded[time_val] += 1
                if self.since_last_exceeded[time_val] > self.max_values[time_val]:
                    self.max_values[time_val] = self.since_last_exceeded[time_val]
        
        self.save_stats()
        self.display_results(formatted_time)

    def update_display(self):
        """Обновление дисплея с поддержкой всех режимов"""
        while self.display_event.is_set():
            try:
                # Автозапуск при распознавании времени с экрана
                if self.screen_capture_mode and not self.running:
                    screen_time = self.read_time_from_screen()
                    if screen_time is not None and screen_time > 0:
                        self.start()
                        self.start_time = time.time() - screen_time
                
                current_time = time.time() - self.start_time if self.running else 0
                
                if time.time() - self.last_display_time < 0.1:
                    time.sleep(0.01)
                    continue
                    
                self.last_display_time = time.time()
                self.print_working_screen(current_time)
                
                if current_time >= self.time_limit:
                    self.stop()
                    break
            except Exception as e:
                print(Fore.RED + f"\nDisplay error: {str(e)}" + Style.RESET_ALL)
                break

    def print_working_screen(self, current_time):
        """Вывод интерфейса с проверкой ошибок"""
        try:
            self.clear_console()
            
            # Заголовок
            print(Fore.CYAN + "\nТерминальный таймер (лимит: 1 мин)" + Style.RESET_ALL)
            print("="*80)
            mode = []
            if self.sound_mode:
                mode.append(Fore.GREEN + "Звук:ON" + Style.RESET_ALL)
            if self.screen_capture_mode:
                mode.append(Fore.BLUE + "Экран:ON" + Style.RESET_ALL)
            mode_str = " | ".join(mode) if mode else Fore.RED + "Ручной" + Style.RESET_ALL
            print(f"Управление: Пробел=старт/стоп | S=статистика | A=звук | C=экран | Esc=выход | Режим: {mode_str}")
            print("="*80)
            
            # Таймер
            mins, secs = divmod(min(current_time, self.time_limit), 60)
            color = Fore.RED if current_time >= self.time_limit - 5 else Fore.YELLOW if current_time >= self.time_limit - 10 else ""
            print(f"\nТАЙМЕР: {color}{int(mins):02d}:{secs:05.2f}{Style.RESET_ALL}")
            
            # Прогресс-бар
            progress = min(current_time / self.time_limit * 100, 100)
            print(f"Прогресс: [{'#' * int(progress/5)}{' ' * (20 - int(progress/5))}] {progress:.1f}%")
            
            # Таблица
            table_data = []
            for val in sorted(self.user_ranges):
                exceeded = current_time >= val
                count = self.since_last_exceeded.get(val, 0)
                max_count = self.max_values.get(val, 0)
                
                color = self.get_counter_color(count, max_count)
                row = [
                    f"{val:.2f}",
                    str(max_count),
                    f"{color}{count}{Style.RESET_ALL}",
                    f"{self.last_exceeded.get(val):.2f}" if self.last_exceeded.get(val) else "-",
                    Fore.RED + "ДА" if exceeded else Fore.GREEN + "НЕТ"
                ]
                table_data.append(row)
            
            print("\n" + tabulate(
                table_data,
                headers=["Метка", "Макс", "Счетчик", "Посл.прев.", "Текущ."],
                tablefmt="grid",
                stralign="center"
            ))
            
            # Статус
            if current_time >= self.time_limit:
                status = Fore.RED + "АВТОСТОП" + Style.RESET_ALL
            elif self.running:
                status = Fore.YELLOW + "СТОП (Пробел)" + Style.RESET_ALL
            else:
                status = Fore.GREEN + "СТАРТ (Пробел)" + Style.RESET_ALL
            print(f"\n{status}")
            
        except Exception as e:
            print(Fore.RED + f"\nInterface error: {str(e)}" + Style.RESET_ALL)

    def display_results(self, current_time):
        """Отображение результатов замера"""
        try:
            self.clear_console()
            
            print(Fore.CYAN + "\nТерминальный таймер (лимит: 1 мин)" + Style.RESET_ALL)
            print("="*80)
            print("Пробел=старт/стоп | S=статистика | A=звук | C=экран | Esc=выход")
            print("="*80)
            
            print("\n" + "="*80)
            if current_time >= self.time_limit:
                print(f" Достигнут лимит времени: {current_time:.2f} сек ")
            else:
                print(f" Текущий результат: {current_time:.2f} сек ")
            print(f" Это время встречалось {self.stats[current_time]} раз(а)")
            print("="*80 + "\n")
            
            self.print_full_table(current_time)
            print("\nНажмите ПРОБЕЛ для нового замера или Esc для выхода")
        except Exception as e:
            print(Fore.RED + f"\nResults error: {str(e)}" + Style.RESET_ALL)

    def print_full_table(self, current_time):
        """Вывод полной таблицы результатов"""
        try:
            table_data = []
            for val in sorted(self.user_ranges):
                exceeded = current_time >= val
                count = self.since_last_exceeded.get(val, 0)
                max_count = self.max_values.get(val, 0)
                
                color = self.get_counter_color(count, max_count)
                row = [
                    f"{val:.2f}",
                    str(max_count),
                    f"{color}{count}{Style.RESET_ALL}",
                    f"{self.last_exceeded.get(val):.2f}" if self.last_exceeded.get(val) else "-",
                    Fore.RED + "ДА" if exceeded else Fore.GREEN + "НЕТ"
                ]
                table_data.append(row)
            
            print(tabulate(
                table_data,
                headers=["Метка", "Макс", "Счетчик", "Посл.прев.", "Текущ."],
                tablefmt="grid",
                stralign="center"
            ))
        except Exception as e:
            print(Fore.RED + f"\nTable error: {str(e)}" + Style.RESET_ALL)

    def show_all_stats(self):
        """Отображение всей статистики"""
        try:
            self.clear_console()
            
            print(Fore.CYAN + "\nТерминальный таймер (лимит: 1 мин)" + Style.RESET_ALL)
            print("="*80)
            print("Пробел=старт/стоп | S=статистика | A=звук | C=экран | Esc=выход")
            print("="*80)
            
            print("\n" + "="*80)
            print(" ВСЯ СТАТИСТИКА ")
            print("="*80 + "\n")
            
            table_data = []
            for val in sorted(self.user_ranges):
                count = self.since_last_exceeded.get(val, 0)
                max_count = self.max_values.get(val, 0)
                
                color = self.get_counter_color(count, max_count)
                row = [
                    f"{val:.2f}",
                    str(max_count),
                    f"{color}{count}{Style.RESET_ALL}",
                    f"{self.last_exceeded.get(val):.2f}" if self.last_exceeded.get(val) else "-",
                    str(sum(1 for t in self.stats.keys() if t < val))
                ]
                table_data.append(row)
            
            print(tabulate(
                table_data,
                headers=["Метка", "Макс", "Тек.счет", "Посл.прев.", "Всего"],
                tablefmt="grid",
                stralign="center"
            ))
        except Exception as e:
            print(Fore.RED + f"\nStats error: {str(e)}" + Style.RESET_ALL)

    def clear_console(self):
        """Очистка консоли с обработкой ошибок"""
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except:
            print("\n" * 50)

    def run(self):
        """Основной цикл программы"""
        try:
            keyboard.add_hotkey('space', self.start_stop)
            keyboard.add_hotkey('s', self.show_all_stats)
            keyboard.add_hotkey('a', self.toggle_audio_mode)
            keyboard.add_hotkey('c', self.toggle_screen_capture_mode)
            
            self.load_stats()
            self.clear_console()
            self.show_all_stats()
            keyboard.wait('esc')
        except Exception as e:
            print(Fore.RED + f"\nMain error: {str(e)}" + Style.RESET_ALL)
        finally:
            self.stop_audio()
            print(Fore.YELLOW + "\nПрограмма завершена." + Style.RESET_ALL)

if __name__ == "__main__":
    try:
        app = TimerApp()
        app.run()
    except Exception as e:
        print(Fore.RED + f"\nКритическая ошибка: {str(e)}" + Style.RESET_ALL)
    finally:
        try:
            sd._terminate()
        except:
            pass