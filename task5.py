def max_mood_on_stairs(n, k, a):
    """
    Вычисляет максимальное настроение, которое можно получить на последней ступеньке.
    
    Args:
        n (int): количество ступенек
        k (int): максимальное количество абстрагированных переходов
        a (list): список изменений настроения для каждой ступеньки
    
    Returns:
        int: максимальное возможное настроение
    """
    # dp[i][j] - максимальное настроение на ступеньке i с j абстрагированными переходами
    dp = [[float('-inf')] * (k + 1) for _ in range(n + 1)]
    
    # Начальное состояние: мальчик стоит перед первой ступенькой с настроением 0
    dp[0][0] = 0
    
    # Перебираем все ступеньки
    for i in range(n):
        # Перебираем количество использованных абстрагированных переходов
        for j in range(k + 1):
            if dp[i][j] == float('-inf'):
                continue
            
            current_mood = dp[i][j]
            
            # Вариант 1: перейти на следующую ступеньку
            if i + 1 <= n:
                dp[i + 1][j] = max(dp[i + 1][j], current_mood + a[i])
            
            # Вариант 2: перепрыгнуть через одну ступеньку
            if i + 2 <= n:
                dp[i + 2][j] = max(dp[i + 2][j], current_mood + a[i] + a[i + 1])
            
            # Вариант 3: абстрагированный переход (если ещё есть попытки)
            if j < k:
                # Можно перейти на любую ступеньку от i+1 до n
                for next_step in range(i + 1, n + 1):
                    # При абстрагированном переходе получаем настроение целевой ступеньки
                    mood_gain = a[next_step - 1]
                    dp[next_step][j + 1] = max(dp[next_step][j + 1], current_mood + mood_gain)
    
    # Также проверяем возможность использовать абстрагированный переход с самого начала
    if k > 0:
        for step in range(1, n + 1):
            mood_gain = a[step - 1]
            dp[step][1] = max(dp[step][1], mood_gain)
    
    # Находим максимальное настроение на последней ступеньке
    max_mood = float('-inf')
    for j in range(k + 1):
        max_mood = max(max_mood, dp[n][j])
    
    return max_mood

def main():
    # Читаем входные данные
    n, k = map(int, input().split())
    a = list(map(int, input().split()))
    
    # Проверяем ограничения
    if not (1 <= n <= 1000):
        print("Ошибка: n должно быть от 1 до 1000")
        return
    
    if not (0 <= k <= 100):
        print("Ошибка: k должно быть от 0 до 100")
        return
    
    if len(a) != n:
        print("Ошибка: количество элементов в массиве должно быть равно n")
        return
    
    if not all(x <= 100 for x in a):
        print("Ошибка: все элементы массива должны быть не больше 100")
        return
    
    # Вычисляем максимальное настроение
    result = max_mood_on_stairs(n, k, a)
    print(result)

if __name__ == "__main__":
    main() 