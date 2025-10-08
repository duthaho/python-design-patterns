from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Set, Union


class ExprVisitor(ABC):
    """Abstract base class for expression visitors."""

    @abstractmethod
    def visit_number(self, n: "NumberLiteral"): ...

    @abstractmethod
    def visit_variable(self, v: "Variable"): ...

    @abstractmethod
    def visit_binary(self, b: "BinaryOperation"): ...

    @abstractmethod
    def visit_unary(self, u: "UnaryOperation"): ...


class Expr(ABC):
    """Abstract base class for expressions."""

    @abstractmethod
    def accept(self, visitor: ExprVisitor):
        """Accept a visitor."""
        ...


@dataclass(frozen=True)
class NumberLiteral(Expr):
    """Represents a numeric literal."""

    value: Union[int, float]

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_number(self)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Variable(Expr):
    """Represents a variable reference."""

    name: str

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_variable(self)

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class BinaryOperation(Expr):
    """Represents a binary operation (e.g., +, -, *, /)."""

    left: Expr
    operator: str
    right: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_binary(self)

    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


@dataclass(frozen=True)
class UnaryOperation(Expr):
    """Represents a unary operation (e.g., -, +)."""

    operator: str
    operand: Expr

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_unary(self)

    def __str__(self) -> str:
        return f"({self.operator}{self.operand})"


class EvaluatorVisitor(ExprVisitor):
    """Evaluates expressions with given variable context."""

    def __init__(self, context: Dict[str, Union[int, float]]) -> None:
        self.context = context

    def visit_number(self, n: NumberLiteral) -> Union[int, float]:
        return n.value

    def visit_variable(self, v: Variable) -> Union[int, float]:
        if v.name not in self.context:
            raise ValueError(f"Undefined variable: {v.name}")
        return self.context[v.name]

    def visit_binary(self, b: BinaryOperation) -> Union[int, float]:
        left = b.left.accept(self)
        right = b.right.accept(self)

        operations = {
            "+": lambda l, r: l + r,
            "-": lambda l, r: l - r,
            "*": lambda l, r: l * r,
            "/": lambda l, r: l / r if r != 0 else self._raise_division_error(),
            "%": lambda l, r: l % r,
            "**": lambda l, r: l**r,
        }

        if b.operator not in operations:
            raise ValueError(f"Unknown operator: {b.operator}")

        return operations[b.operator](left, right)

    def visit_unary(self, u: UnaryOperation) -> Union[int, float]:
        operand = u.operand.accept(self)

        if u.operator == "-":
            return -operand
        elif u.operator == "+":
            return +operand
        else:
            raise ValueError(f"Unknown unary operator: {u.operator}")

    @staticmethod
    def _raise_division_error():
        raise ZeroDivisionError("Division by zero")


class OptimizerVisitor(ExprVisitor):
    """Optimizes expressions through constant folding."""

    def visit_number(self, n: NumberLiteral) -> Expr:
        return n

    def visit_variable(self, v: Variable) -> Expr:
        return v

    def visit_binary(self, b: BinaryOperation) -> Expr:
        # Recursively optimize children
        left = b.left.accept(self)
        right = b.right.accept(self)

        # Constant folding: if both operands are numbers, compute result
        if isinstance(left, NumberLiteral) and isinstance(right, NumberLiteral):
            try:
                operations = {
                    "+": lambda l, r: l + r,
                    "-": lambda l, r: l - r,
                    "*": lambda l, r: l * r,
                    "/": lambda l, r: l / r if r != 0 else None,
                    "%": lambda l, r: l % r,
                    "**": lambda l, r: l**r,
                }

                if b.operator in operations:
                    result = operations[b.operator](left.value, right.value)
                    if result is not None:
                        return NumberLiteral(result)
            except (ZeroDivisionError, ValueError):
                pass  # Keep original expression if operation fails

        # Algebraic optimizations
        if b.operator == "+":
            if isinstance(left, NumberLiteral) and left.value == 0:
                return right  # 0 + x = x
            if isinstance(right, NumberLiteral) and right.value == 0:
                return left  # x + 0 = x

        elif b.operator == "*":
            if isinstance(left, NumberLiteral) and left.value == 0:
                return NumberLiteral(0)  # 0 * x = 0
            if isinstance(right, NumberLiteral) and right.value == 0:
                return NumberLiteral(0)  # x * 0 = 0
            if isinstance(left, NumberLiteral) and left.value == 1:
                return right  # 1 * x = x
            if isinstance(right, NumberLiteral) and right.value == 1:
                return left  # x * 1 = x

        # Return optimized expression
        return BinaryOperation(left, b.operator, right)

    def visit_unary(self, u: UnaryOperation) -> Expr:
        operand = u.operand.accept(self)

        # Constant folding for unary operations
        if isinstance(operand, NumberLiteral):
            if u.operator == "-":
                return NumberLiteral(-operand.value)
            elif u.operator == "+":
                return NumberLiteral(+operand.value)

        return UnaryOperation(u.operator, operand)


class CodeGeneratorVisitor(ExprVisitor):
    """Generates Python code from AST."""

    def visit_number(self, n: NumberLiteral) -> str:
        return str(n.value)

    def visit_variable(self, v: Variable) -> str:
        return v.name

    def visit_binary(self, b: BinaryOperation) -> str:
        left = b.left.accept(self)
        right = b.right.accept(self)
        return f"({left} {b.operator} {right})"

    def visit_unary(self, u: UnaryOperation) -> str:
        operand = u.operand.accept(self)
        return f"({u.operator}{operand})"


class VariableCollectorVisitor(ExprVisitor):
    """Collects all unique variable names in an expression."""

    def __init__(self) -> None:
        self.variables: Set[str] = set()

    def visit_number(self, n: NumberLiteral) -> None:
        pass  # Numbers don't contain variables

    def visit_variable(self, v: Variable) -> None:
        self.variables.add(v.name)

    def visit_binary(self, b: BinaryOperation) -> None:
        b.left.accept(self)
        b.right.accept(self)

    def visit_unary(self, u: UnaryOperation) -> None:
        u.operand.accept(self)

    def get_variables(self) -> Set[str]:
        """Return collected variable names."""
        return self.variables


class TypeCheckerVisitor(ExprVisitor):
    """Validates expression structure and types."""

    def __init__(self, known_variables: Set[str]) -> None:
        self.known_variables = known_variables
        self.errors: List[str] = []

    def visit_number(self, n: NumberLiteral) -> bool:
        return True

    def visit_variable(self, v: Variable) -> bool:
        if v.name not in self.known_variables:
            self.errors.append(f"Unknown variable: {v.name}")
            return False
        return True

    def visit_binary(self, b: BinaryOperation) -> bool:
        left_valid = b.left.accept(self)
        right_valid = b.right.accept(self)

        valid_operators = {"+", "-", "*", "/", "%", "**"}
        if b.operator not in valid_operators:
            self.errors.append(f"Invalid operator: {b.operator}")
            return False

        return left_valid and right_valid

    def visit_unary(self, u: UnaryOperation) -> bool:
        operand_valid = u.operand.accept(self)

        valid_operators = {"+", "-"}
        if u.operator not in valid_operators:
            self.errors.append(f"Invalid unary operator: {u.operator}")
            return False

        return operand_valid

    def is_valid(self) -> bool:
        """Check if expression is valid."""
        return len(self.errors) == 0

    def get_errors(self) -> List[str]:
        """Get list of validation errors."""
        return self.errors


class PrettyPrintVisitor(ExprVisitor):
    """Pretty prints expression tree with indentation."""

    def __init__(self, indent: int = 0) -> None:
        self.indent = indent
        self.output: List[str] = []

    def visit_number(self, n: NumberLiteral) -> None:
        self.output.append("  " * self.indent + f"Number: {n.value}")

    def visit_variable(self, v: Variable) -> None:
        self.output.append("  " * self.indent + f"Variable: {v.name}")

    def visit_binary(self, b: BinaryOperation) -> None:
        self.output.append("  " * self.indent + f"BinaryOp: {b.operator}")

        left_visitor = PrettyPrintVisitor(self.indent + 1)
        b.left.accept(left_visitor)
        self.output.extend(left_visitor.output)

        right_visitor = PrettyPrintVisitor(self.indent + 1)
        b.right.accept(right_visitor)
        self.output.extend(right_visitor.output)

    def visit_unary(self, u: UnaryOperation) -> None:
        self.output.append("  " * self.indent + f"UnaryOp: {u.operator}")

        operand_visitor = PrettyPrintVisitor(self.indent + 1)
        u.operand.accept(operand_visitor)
        self.output.extend(operand_visitor.output)

    def get_result(self) -> str:
        """Return pretty-printed tree."""
        return "\n".join(self.output)


def demo_compiler_ast():
    """Demonstrate the compiler AST example."""
    # Example 1: (x + 2) * 3
    print("\nExample 1: (x + 2) * 3")
    print("-" * 70)

    expr1 = BinaryOperation(
        left=BinaryOperation(left=Variable("x"), operator="+", right=NumberLiteral(2)),
        operator="*",
        right=NumberLiteral(3),
    )

    # Evaluate
    evaluator = EvaluatorVisitor({"x": 5})
    result = expr1.accept(evaluator)
    print(f"Evaluation (x=5): {result}")

    # Generate code
    codegen = CodeGeneratorVisitor()
    code = expr1.accept(codegen)
    print(f"Generated code: {code}")

    # Collect variables
    collector = VariableCollectorVisitor()
    expr1.accept(collector)
    print(f"Variables used: {collector.get_variables()}")

    # Type check
    type_checker = TypeCheckerVisitor({"x", "y", "z"})
    is_valid = expr1.accept(type_checker)
    print(f"Type check passed: {is_valid}")

    # Pretty print
    printer = PrettyPrintVisitor()
    expr1.accept(printer)
    print(f"AST Structure:\n{printer.get_result()}")

    # Example 2: Optimization - 2 + 3
    print("\n\nExample 2: Constant Folding Optimization")
    print("-" * 70)

    expr2 = BinaryOperation(left=NumberLiteral(2), operator="+", right=NumberLiteral(3))

    print(f"Original: {expr2}")

    optimizer = OptimizerVisitor()
    optimized = expr2.accept(optimizer)
    print(f"Optimized: {optimized}")

    # Example 3: Complex optimization
    print("\n\nExample 3: Complex Optimization")
    print("-" * 70)

    # (x + 0) * 1 + (5 * 2)
    expr3 = BinaryOperation(
        left=BinaryOperation(
            left=BinaryOperation(
                left=Variable("x"), operator="+", right=NumberLiteral(0)
            ),
            operator="*",
            right=NumberLiteral(1),
        ),
        operator="+",
        right=BinaryOperation(
            left=NumberLiteral(5), operator="*", right=NumberLiteral(2)
        ),
    )

    print(f"Original: {expr3}")

    codegen = CodeGeneratorVisitor()
    print(f"Original code: {expr3.accept(codegen)}")

    optimized3 = expr3.accept(optimizer)
    print(f"Optimized: {optimized3}")
    print(f"Optimized code: {optimized3.accept(codegen)}")

    # Evaluate both
    eval_visitor = EvaluatorVisitor({"x": 7})
    print(f"Original result (x=7): {expr3.accept(eval_visitor)}")
    print(f"Optimized result (x=7): {optimized3.accept(eval_visitor)}")


def main():
    """Run all demonstrations."""
    demo_compiler_ast()


if __name__ == "__main__":
    main()
