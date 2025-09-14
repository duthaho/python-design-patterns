from abc import ABC, abstractmethod


class OperationComponent(ABC):
    @abstractmethod
    def to_string(self) -> str:
        pass

    @abstractmethod
    def evaluate(self) -> float:
        pass


class Number(OperationComponent):
    def __init__(self, value: float) -> None:
        self.value = value

    def to_string(self) -> str:
        # Display integers without decimal point
        if isinstance(self.value, int) or self.value.is_integer():
            return str(int(self.value))
        return str(self.value)

    def evaluate(self) -> float:
        return self.value


class BinaryOperation(OperationComponent):
    SUPPORTED_OPERATORS = {"+", "-", "*", "/", "**", "%"}

    def __init__(
        self, operator: str, left: OperationComponent, right: OperationComponent
    ) -> None:
        if operator not in self.SUPPORTED_OPERATORS:
            raise ValueError(f"Unsupported operator: {operator}")
        self.left = left
        self.right = right
        self.operator = operator

    def to_string(self) -> str:
        return f"({self.left.to_string()} {self.operator} {self.right.to_string()})"

    def evaluate(self) -> float:
        left_val = self.left.evaluate()
        right_val = self.right.evaluate()

        if self.operator == "+":
            return left_val + right_val
        elif self.operator == "-":
            return left_val - right_val
        elif self.operator == "*":
            return left_val * right_val
        elif self.operator == "/":
            if right_val == 0:
                raise ZeroDivisionError("Division by zero")
            return left_val / right_val
        elif self.operator == "**":
            return left_val**right_val
        elif self.operator == "%":
            if right_val == 0:
                raise ZeroDivisionError("Modulo by zero")
            return left_val % right_val


class UnaryOperation(OperationComponent):
    SUPPORTED_OPERATORS = {"-", "+", "abs", "sqrt"}

    def __init__(self, operator: str, operand: OperationComponent) -> None:
        if operator not in self.SUPPORTED_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {operator}")
        self.operator = operator
        self.operand = operand

    def to_string(self) -> str:
        if self.operator in ["-", "+"]:
            return f"({self.operator}{self.operand.to_string()})"
        else:
            return f"{self.operator}({self.operand.to_string()})"

    def evaluate(self) -> float:
        operand_val = self.operand.evaluate()

        if self.operator == "-":
            return -operand_val
        elif self.operator == "+":
            return operand_val
        elif self.operator == "abs":
            return abs(operand_val)
        elif self.operator == "sqrt":
            if operand_val < 0:
                raise ValueError("Square root of negative number")
            return operand_val**0.5


if __name__ == "__main__":
    # Build expression: (5 + 3) * 2 - (-4)
    five = Number(5)
    three = Number(3)
    add = BinaryOperation("+", five, three)

    two = Number(2)
    multiply = BinaryOperation("*", add, two)

    four = Number(4)
    negate = UnaryOperation("-", four)

    final_expr = BinaryOperation("-", multiply, negate)

    print(f"Expression: {final_expr.to_string()}")  # ((5 + 3) * 2) - (-4)
    print(f"Result: {final_expr.evaluate()}")  # 20.0

    # More complex example: sqrt(abs(-16)) + (10 % 3)
    complex_expr = BinaryOperation(
        "+",
        UnaryOperation("sqrt", UnaryOperation("abs", Number(-16))),
        BinaryOperation("%", Number(10), Number(3)),
    )
    print(f"\nComplex expression: {complex_expr.to_string()}")
    print(f"Result: {complex_expr.evaluate()}")
