import sys

from typing import List
from dataclasses import dataclass
from enum import Enum

from lark import Lark, ast_utils, Transformer

this_module = sys.modules[__name__]

class ComparisonOperator(Enum):
    GT = ">"
    EQ = "="

class ArithmeticOperator(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"

class _Ast(ast_utils.Ast):
    pass

class _Statement(_Ast):
    pass

class _Expression(_Ast):
    pass

@dataclass
class Id(_Expression):
    name: str

@dataclass
class Int(_Expression):
    value: int

@dataclass
class Field(_Ast):
    key: Id
    Value: _Expression

@dataclass
class Declaration(_Statement):
    id: Id

@dataclass
class Assignment(_Statement):
    id: Id
    expression: _Expression

@dataclass
class DereferenceAssignment(_Statement):
    target: _Expression
    expression: _Expression

@dataclass
class Return(_Statement):
    expression: _Expression

@dataclass
class Function(_Ast):
    name: Id
    parameters: List[Id]
    statements: List[_Statement]
    return_statement: Return

@dataclass
class Arithmetic(_Expression):
    left_expression: _Expression
    operator: ArithmeticOperator
    right_expression: _Expression

@dataclass
class Comparison(_Expression):
    left_expression: _Expression
    operator: ComparisonOperator
    right_expression: _Expression

@dataclass
class If(_Statement):
    condition: _Expression
    true_statement: _Statement
    false_statement: _Statement

@dataclass
class While(_Statement):
    condition: _Expression
    statements: List[_Statement]

@dataclass
class Output(_Statement):
    expression: _Expression

@dataclass
class FunctionCall(_Expression):
    callee: _Expression
    expressions: List[_Expression]

@dataclass
class Parenthesize(_Expression):
    expressions: _Expression

@dataclass
class Input(_Expression):
    pass

@dataclass
class Null(_Expression):
    pass

@dataclass
class Reference(_Expression):
    id: Id

@dataclass
class Dereference(_Expression):
    expression: _Expression

@dataclass
class Allocation(_Expression):
    expression: _Expression

@dataclass
class Struct(_Expression):
    fields: List[Field]

@dataclass
class FieldAccess(_Expression):
    expression: _Expression
    id: Id

@dataclass
class FieldAssignment(_Statement):
    id: Id
    key: Id
    expression: _Expression

@dataclass
class DereferenceFieldAssignment(_Statement):
    target: _Expression
    key: Id
    expression: _Expression

class ASTBuilder(Transformer):
    def ids(self, items):
        return items

    def stmts(self, items):
        return items

    def exprs(self, items):
        return items

    def func(self, items):
        return Function(items[0], items[1], items[2], items[3])

    def stmt_return(self, items):
        return Return(items[0])

    def id(self, items):
        return Id(items[0])

    def int(self, items):
        return Int(items[0])

    def stmt_decl(self, items):
        return Declaration(items[0])

    def stmt_assign(self, items):
        return Assignment(items[0], items[1])

    def arith_add(self, items):
        return Arithmetic(items[0], ArithmeticOperator.ADD, items[1])

    def arith_sub(self, items):
        return Arithmetic(items[0], ArithmeticOperator.SUB, items[1])

    def term_mul(self, items):
        return Arithmetic(items[0], ArithmeticOperator.MUL, items[1])

    def term_div(self, items):
        return Arithmetic(items[0], ArithmeticOperator.DIV, items[1])

    def stmt_if(self, items):
        return If(items[0], items[1], items[2])

    def cmp_gt(self, items):
        return Comparison(items[0], ComparisonOperator.GT, items[1])

    def cmp_eq(self, items):
        return Comparison(items[0], ComparisonOperator.EQ, items[1])

    def stmt_while(self, items):
        return While(items[0], items[1])

    def stmt_output(self, items):
        return Output(items[0])

    def factor_call(self, items):
        return FunctionCall(items[0], items[1])

    def prim_paren(self, items):
        return Parenthesize(items[0])

    def prim_input(self, items):
        return Input()

    def prim_ref(self, items):
        return Reference(items[0])

    def prim_deref(self, items):
        return Dereference(items[0])

    def prim_alloc(self, items):
        return Allocation(items[0])

    def stmt_deref_assign(self, items):
        return DereferenceAssignment(items[0], items[1])

    def prim_struct(self, items):
        return Struct(items)

    def factor_field(self, items):
        return FieldAccess(items[0], items[1])

    def stmt_field_assign(self, items):
        return FieldAssignment(items[0], items[1], items[2])

    def stmt_deref_field_assign(self, items):
        return DereferenceFieldAssignment(items[0], items[1], items[2])

    def prim_null(self, items):
        return Null()

def getTransformer():
    return ast_utils.create_transformer(this_module, ASTBuilder())