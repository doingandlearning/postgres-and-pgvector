# i want to pick a random number between 1 and 100
import random
def pick_random_number():
    return random.uniform(1, 100)

if __name__ == "__main__":
    random_number = pick_random_number()
    print(f"Random number between 1 and 100: {random_number}") 