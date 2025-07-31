def build_sequence(N, S):
    """
    Строит последовательность согласно правилам из строки S.
    
    Args:
        N (int): длина строки S
        S (str): строка из символов 'L' и 'R'
    
    Returns:
        list: итоговая последовательность
    """
    # Начинаем с последовательности [0]
    sequence = [0]
    
    # Обрабатываем каждый символ в строке S
    for i in range(1, N + 1):
        char = S[i - 1]  # S[i-1] соответствует S_i в задании
        
        if char == 'L':
            # Вставляем число i слева от числа i-1
            # Находим позицию числа i-1
            pos = sequence.index(i - 1)
            sequence.insert(pos, i)
        elif char == 'R':
            # Вставляем число i справа от числа i-1
            # Находим позицию числа i-1
            pos = sequence.index(i - 1)
            sequence.insert(pos + 1, i)
    
    return sequence

def main():
    # Читаем входные данные
    N = int(input())
    S = input().strip()
    
    # Проверяем ограничения
    if not (1 < N < 5 * 10**5):
        print("Ошибка: N должно быть от 2 до 500000")
        return
    
    if len(S) != N:
        print("Ошибка: длина строки S должна быть равна N")
        return
    
    # Проверяем, что строка содержит только 'L' и 'R'
    if not all(c in 'LR' for c in S):
        print("Ошибка: строка S должна содержать только символы 'L' и 'R'")
        return
    
    # Строим последовательность
    result = build_sequence(N, S)
    
    # Выводим результат
    print(' '.join(map(str, result)))

if __name__ == "__main__":
    main() 