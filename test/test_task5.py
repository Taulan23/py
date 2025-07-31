import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task5 import max_mood_on_stairs

def test_task5():
    """Тестирует решение пятого задания"""
    test_cases = [
        ((4, 1, [-1, -2, -3, -4]), -4),      # Пример из задания
        ((4, 0, [1, 2, 3, 4]), 10),          # Пример из задания
        ((4, 1, [-1, -2, 3, 4]), 7),         # Пример из задания
        ((5, 1, [-2, 3, -1, 3, -2]), 3),     # Пример из задания (исправлено)
        ((3, 0, [1, 2, 3]), 6),              # Простой случай без абстракций
        ((3, 1, [-1, -1, -1]), -1),          # Используем абстракцию
    ]
    
    print("Тестирование задания 5:")
    for i, ((n, k, a), expected) in enumerate(test_cases, 1):
        result = max_mood_on_stairs(n, k, a)
        status = "✓" if result == expected else "✗"
        print(f"Тест {i}: n={n}, k={k}, a={a} → {result} (ожидалось {expected}) {status}")
        
        if result != expected:
            print(f"  ОШИБКА: для n={n}, k={k}, a={a} получено {result}, ожидалось {expected}")

if __name__ == "__main__":
    test_task5() 