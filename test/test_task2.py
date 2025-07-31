import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task2 import calculate_previous_sunday_date

def test_task2():
    """Тестирует решение второго задания"""
    test_cases = [
        ((13, 30), 6),   # Ввод: 13 30, Вывод: 6
        ((9, 24), 2),    # Ввод: 9 24, Вывод: 2
        ((15, 8), 15),   # 8 + 7 = 15
        ((1, 25), 1),    # 25 + 7 = 32, 32 - 31 = 1
        ((31, 25), 1),   # 25 + 7 = 32, 32 - 31 = 1
    ]
    
    print("Тестирование задания 2:")
    for i, ((n, m), expected) in enumerate(test_cases, 1):
        result = calculate_previous_sunday_date(n, m)
        status = "✓" if result == expected else "✗"
        print(f"Тест {i}: n={n}, m={m} → {result} (ожидалось {expected}) {status}")
        
        if result != expected:
            print(f"  ОШИБКА: для n={n}, m={m} получено {result}, ожидалось {expected}")

if __name__ == "__main__":
    test_task2() 