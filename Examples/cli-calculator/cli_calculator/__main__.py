import argparse
from calculator import add, subtract, multiply, divide

# Create a parser for command line arguments
parser = argparse.ArgumentParser(description='A simple CLI Calculator')

# Add the arguments
parser.add_argument('--operation', type=str, required=True, help='Operation to perform (add, sub, mul or div)')
parser.add_argument('--num1', type=int, required=True, help='First number for operation')
parser.add_argument('--num2', type=int, required=True, help='Second number for operation')

# Parse the arguments
args = parser.parse_args()

if args.operation == 'add':
    print(f"Result: {add(args.num1, args.num2)}")
elif args.operation == 'sub':
    print(f"Result: {subtract(args.num1, args.num2)}")
elif args.operation == 'mul':
    print(f"Result: {multiply(args.num1, args.num2)}")
elif args.operation == 'div':
    if args.num2 != 0:  # Check for division by zero
        print(f"Result: {divide(args.num1, args.num2)}")
    else:
        print("Error: Division by zero is not allowed.")
else:
    print('Invalid operation. Please choose from add (addition), sub (subtraction), mul (multiplication) or div (division).')