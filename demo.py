#!/usr/bin/env python3
"""
Демонстрационный скрипт для создания тестовых данных
"""

import json
import random
from datetime import datetime, timedelta

def create_demo_data():
    """Создает демонстрационные данные для тестирования"""
    
    # Генерируем случайные числа
    numbers = []
    start_time = datetime.now() - timedelta(hours=2)
    
    for i in range(25):
        # Генерируем случайное число в формате XXX.XX
        number = f"{random.randint(100, 999)}.{random.randint(10, 99)}"
        
        # Время с интервалом в несколько минут
        timestamp = start_time + timedelta(minutes=i*5)
        
        entry = {
            'number': number,
            'timestamp': timestamp.isoformat(),
            'id': i + 1
        }
        
        numbers.append(entry)
    
    # Сортируем по времени (новые сначала)
    numbers.reverse()
    
    # Создаем структуру данных
    data = {
        'last_updated': datetime.now().isoformat(),
        'total_count': len(numbers),
        'system_info': {
            'platform': 'Demo Data',
            'python_version': '3.11.0'
        },
        'numbers': numbers
    }
    
    # Сохраняем в файл
    with open('numbers.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✅ Демонстрационные данные созданы!")
    print(f"📊 Создано {len(numbers)} записей")
    print("🔍 Используйте './run.sh --view' для просмотра")

if __name__ == "__main__":
    create_demo_data() 