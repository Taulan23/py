#!/usr/bin/env python3
"""
Тестирование всех решений для Т-Академии. Аналитика (2025)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Запускает все тесты для заданий Т-Академии"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ РЕШЕНИЙ Т-АКАДЕМИИ. АНАЛИТИКА (2025)")
    print("=" * 60)
    print()
    
    # Тест задания 1
    print("=" * 20 + " TEST_TASK1 " + "=" * 20)
    try:
        from test_task1 import test_task1
        test_task1()
    except ImportError as e:
        print(f"Ошибка импорта test_task1: {e}")
    except Exception as e:
        print(f"Ошибка выполнения test_task1: {e}")
    print()
    
    # Тест задания 2
    print("=" * 20 + " TEST_TASK2 " + "=" * 20)
    try:
        from test_task2 import test_task2
        test_task2()
    except ImportError as e:
        print(f"Ошибка импорта test_task2: {e}")
    except Exception as e:
        print(f"Ошибка выполнения test_task2: {e}")
    print()
    
    # Тест задания 3
    print("=" * 20 + " TEST_TASK3 " + "=" * 20)
    try:
        from test_task3 import test_task3
        test_task3()
    except ImportError as e:
        print(f"Ошибка импорта test_task3: {e}")
    except Exception as e:
        print(f"Ошибка выполнения test_task3: {e}")
    print()
    
    # Тест задания 4
    print("=" * 20 + " TEST_TASK4 " + "=" * 20)
    try:
        from test_task4 import test_task4
        test_task4()
    except ImportError as e:
        print(f"Ошибка импорта test_task4: {e}")
    except Exception as e:
        print(f"Ошибка выполнения test_task4: {e}")
    print()
    
    # Тест задания 5
    print("=" * 20 + " TEST_TASK5 " + "=" * 20)
    try:
        from test_task5 import test_task5
        test_task5()
    except ImportError as e:
        print(f"Ошибка импорта test_task5: {e}")
    except Exception as e:
        print(f"Ошибка выполнения test_task5: {e}")
    print()
    
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests() 