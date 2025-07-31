import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task5 import max_mood_on_stairs

# Тест 1: n=4, k=1, a=[-1, -2, -3, -4] → ожидается -4
n, k = 4, 1
a = [-1, -2, -3, -4]
result = max_mood_on_stairs(n, k, a)
print(f"Тест 1: Результат: {result}, Ожидалось: -4")

# Тест 4: n=5, k=1, a=[-2, 3, -1, 3, -2] → ожидается 4
n, k = 5, 1
a = [-2, 3, -1, 3, -2]
result = max_mood_on_stairs(n, k, a)
print(f"Тест 4: Результат: {result}, Ожидалось: 4")

# Тест с k=2: n=5, k=2, a=[-2, 3, -1, 3, -2]
n, k = 5, 2
a = [-2, 3, -1, 3, -2]
result = max_mood_on_stairs(n, k, a)
print(f"Тест с k=2: Результат: {result}") 