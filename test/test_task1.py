import sys
from io import StringIO
from task1 import is_honestly_even

def test_task1():
    """Тестирует решение первого задания"""
    test_cases = [
        (2, 1),      # 2 - честно чётное
        (1, 0),      # 1 - не честно чётное
        (10, 0),     # 10 - не честно чётное (1 нечётная)
        (30, 0),     # 30 - не честно чётное (3 нечётная)
        (4826, 1),   # 4826 - честно чётное
        (8802, 1),   # 8802 - честно чётное
        (79, 0),     # 79 - не честно чётное
        (301, 0),    # 301 - не честно чётное
        (2468, 1),   # 2468 - честно чётное
        (13579, 0),  # 13579 - не честно чётное
    ]
    
    print("Тестирование задания 1:")
    for i, (input_num, expected) in enumerate(test_cases, 1):
        result = is_honestly_even(input_num)
        status = "✓" if result == expected else "✗"
        print(f"Тест {i}: {input_num} → {result} (ожидалось {expected}) {status}")
        
        if result != expected:
            print(f"  ОШИБКА: для числа {input_num} получено {result}, ожидалось {expected}")

if __name__ == "__main__":
    test_task1() 