import math

def gcd(a, b):
    """
    Вычисляет наибольший общий делитель двух чисел.
    """
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    """
    Вычисляет наименьшее общее кратное двух чисел.
    """
    return abs(a * b) // gcd(a, b)

def add_fractions(a, b, c, d):
    """
    Складывает две рациональные дроби a/b и c/d.
    
    Args:
        a, b, c, d (int): числители и знаменатели дробей
    
    Returns:
        tuple: (числитель, знаменатель) несократимой дроби
    """
    # Находим общий знаменатель (НОК)
    common_denominator = lcm(b, d)
    
    # Приводим дроби к общему знаменателю
    numerator1 = a * (common_denominator // b)
    numerator2 = c * (common_denominator // d)
    
    # Складываем числители
    total_numerator = numerator1 + numerator2
    
    # Сокращаем дробь
    divisor = gcd(total_numerator, common_denominator)
    final_numerator = total_numerator // divisor
    final_denominator = common_denominator // divisor
    
    return final_numerator, final_denominator

def main():
    # Читаем входные данные
    a, b, c, d = map(int, input().split())
    
    # Проверяем ограничения
    if not all(1 <= x <= 100 for x in [a, b, c, d]):
        print("Ошибка: все числа должны быть от 1 до 100")
        return
    
    # Вычисляем сумму дробей
    numerator, denominator = add_fractions(a, b, c, d)
    
    # Выводим результат
    print(numerator, denominator)

if __name__ == "__main__":
    main() 