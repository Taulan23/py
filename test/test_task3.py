from task3 import add_fractions

def test_task3():
    """Тестирует решение третьего задания"""
    test_cases = [
        ((1, 3, 1, 2), (5, 6)),    # 1/3 + 1/2 = 5/6
        ((1, 1, 1, 1), (2, 1)),    # 1/1 + 1/1 = 2/1
        ((1, 4, 1, 4), (1, 2)),    # 1/4 + 1/4 = 1/2
        ((2, 3, 1, 6), (5, 6)),    # 2/3 + 1/6 = 5/6
        ((3, 4, 1, 4), (1, 1)),    # 3/4 + 1/4 = 1/1
    ]
    
    print("Тестирование задания 3:")
    for i, ((a, b, c, d), expected) in enumerate(test_cases, 1):
        result = add_fractions(a, b, c, d)
        status = "✓" if result == expected else "✗"
        print(f"Тест {i}: {a}/{b} + {c}/{d} = {result[0]}/{result[1]} (ожидалось {expected[0]}/{expected[1]}) {status}")
        
        if result != expected:
            print(f"  ОШИБКА: для {a}/{b} + {c}/{d} получено {result[0]}/{result[1]}, ожидалось {expected[0]}/{expected[1]}")

if __name__ == "__main__":
    test_task3() 