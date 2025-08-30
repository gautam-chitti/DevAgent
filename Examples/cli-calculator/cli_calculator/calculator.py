import argparse

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

parser = argparse.ArgumentParser()
parser.add_argument("operation", help="Operation to perform (add/subtract/multiply/divide)")
parser.add_argument("x", type=int, help="First number")
parser.add_argument("y", type=int, help="Second number")
args = parser.parse_args()

if args.operation == "add":
    print(add(args.x, args.y))
elif args.operation == "subtract":
    print(subtract(args.x, args.y))
elif args.operation == "multiply":
    print(multiply(args.x, args.y))
elif args.operation == "divide":
    result = divide(args.x, args.y)
    if isinstance(result, str):
        print(result)
    else:
        print("Result: ", result)
else:
    print('Invalid operation! Please choose from add/subtract/multiply/divide')