def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y != 0:
        return x / y
    else:
        return "Error! Division by zero is not allowed."

print("Select operation.")
print("1.Add")
print("2.Subtract")
print("3.Multiply")
print("4.Divide")

while True:
    choice = input("\nEnter choice(1/2/3/4): ")
    
    if choice in ('1', '2', '3', '4'):
        num1 = float(input("\nEnter first number: "))
        num2 = float(input("Enter second number: "))
        
        if choice == '1':
            print(f"\n{num1} + {num2} = {add(num1, num2)}")
            
        elif choice == '2':
            print(f"\n{num1} - {num2} = {subtract(num1, num2)}")
        
        elif choice == '3':
            print(f"\n{num1} * {num2} = {multiply(num1, num2)}")
            
        elif choice == '4':
            result = divide(num1, num2)
            if isinstance(result, str):
                print("\n", result)
            else:
                print(f"\n{num1} / {num2} = {divide(num1, num2)}")
        break
    else:
        print("Invalid input! Please enter a valid choice.")