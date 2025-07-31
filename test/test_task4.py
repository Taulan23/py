from task4 import build_sequence

def test_task4():
    """Тестирует решение четвёртого задания"""
    test_cases = [
        ((5, "LRRRL"), [1, 2, 3, 5, 4, 0]),           # Пример из задания
        ((6, "RRLLRR"), [0, 1, 4, 5, 6, 3, 2]),       # Пример из задания
        ((3, "LLL"), [3, 2, 1, 0]),                    # Все влево
        ((3, "RRR"), [0, 1, 2, 3]),                    # Все вправо
        ((4, "LRLR"), [1, 3, 4, 2, 0]),               # Чередование (исправлено)
    ]
    
    print("Тестирование задания 4:")
    for i, ((N, S), expected) in enumerate(test_cases, 1):
        result = build_sequence(N, S)
        status = "✓" if result == expected else "✗"
        print(f"Тест {i}: N={N}, S='{S}' → {result} (ожидалось {expected}) {status}")
        
        if result != expected:
            print(f"  ОШИБКА: для N={N}, S='{S}' получено {result}, ожидалось {expected}")

if __name__ == "__main__":
    test_task4() 