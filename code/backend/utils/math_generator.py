# backend/utils/math_generator.py
# Imports
import random

def generate_math_query(difficulty: int):
    """
    Difficulty 1; 5-20 : d1 + d2
    Difficulty 2; 10
    Difficulty 3; 11-19, 4-9, 15-49 : (d1 * d2) - d3
    
    """
    if difficulty == 1:
        num1 = random.randint(5, 20)
        num2 = random.randint(5, 20)
        return f"{num1} + {num2}", num1 + num2
    elif difficulty == 3:
        num1 = random.randint(11, 19)
        num2 = random.randint(4, 9)
        num3 = random.randint(15, 49)
        return f"({num1} * {num2}) - {num3}", (num1 * num2) - num3
    else:
        num1 = random.randint(10, 15)
        num2 = random.randint(3, 8)
        num3 = random.randint(5, 20)
        return f"{num1} * {num2} + {num3}", (num1 * num2) + num3