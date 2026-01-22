import sys

from typing import List, Any
from dataclasses import dataclass, field
from enum import Enum

from lark import Lark, ast_utils, Transformer, Visitor, Tree

this_module = sys.modules[__name__]

class ComparisonOperator(Enum):
    GT = ">"
    EQ = "=="

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
    # x, y, z, ...
    name: str

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Id):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

@dataclass
class Int(_Expression):
    # 0, 1, -1, ...
    value: int

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if not isinstance(other, Int):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

@dataclass
class Field(_Ast):
    # Id : Exp
    key: Id
    Value: _Expression

    def __eq__(self, other):
        if not isinstance(other, Field):
            return False
        return self.key == other.key and self.Value == other.Value

    def __hash__(self):
        return hash((self.key, self.Value))

@dataclass
class Declaration(_Statement):
    # var Id
    ids: List[Id]

    def __eq__(self, other):
        if not isinstance(other, Declaration):
            return False
        return self.ids == other.ids

    def __hash__(self):
        return hash(tuple(self.ids))

@dataclass
class Assignment(_Statement):
    # Id = Exp;
    id: Id
    expression: _Expression

    def __eq__(self, other):
        if not isinstance(other, Assignment):
            return False
        return self.id == other.id and self.expression == other.expression

    def __hash__(self):
        return hash((self.id, self.expression))

@dataclass
class Dereference(_Expression):
    # * Exp
    expression: _Expression

    def __str__(self):
        return f"*{self.expression}"

    def __eq__(self, other):
        if not isinstance(other, Dereference):
            return False
        return self.expression == other.expression

    def __hash__(self):
        return hash(self.expression)

@dataclass
class DereferenceAssignment(_Statement):
    # *Exp = Exp;
    target: Dereference
    expression: _Expression

    def __eq__(self, other):
        if not isinstance(other, DereferenceAssignment):
            return False
        return self.target == other.target and self.expression == other.expression

    def __hash__(self):
        return hash((self.target, self.expression))

@dataclass
class Return(_Statement):
    # return Exp;
    expression: _Expression

    def __eq__(self, other):
        if not isinstance(other, Return):
            return False
        return self.expression == other.expression

    def __hash__(self):
        return hash(self.expression)

@dataclass
class Function(_Ast):
    # Id ( Id, ... Id ) { [ var id, ... Id ] stm return exp; }
    name: Id
    parameters: List[Id]
    statements: List[_Statement]
    return_statement: Return

    def __eq__(self, other):
        if not isinstance(other, Function):
            return False
        return (self.name == other.name and self.parameters == other.parameters and
                self.statements == other.statements and self.return_statement == other.return_statement)

    def __hash__(self):
        return hash((self.name, tuple(self.parameters), tuple(self.statements), self.return_statement))

@dataclass
class Program(_Ast):
    # Fun, ... Fun
    functions: List[Function]

    def __eq__(self, other):
        if not isinstance(other, Program):
            return False
        return self.functions == other.functions

    def __hash__(self):
        return hash(tuple(self.functions))

@dataclass
class Arithmetic(_Expression):
    # Exp + Exp
    left_expression: _Expression
    operator: ArithmeticOperator
    right_expression: _Expression

    def __str__(self):
        op_map = {
            ArithmeticOperator.ADD: '+',
            ArithmeticOperator.SUB: '-',
            ArithmeticOperator.MUL: '*',
            ArithmeticOperator.DIV: '/'
        }
        return f"{self.left_expression} {op_map[self.operator]} {self.right_expression}"

    def __eq__(self, other):
        if not isinstance(other, Arithmetic):
            return False
        return (self.left_expression == other.left_expression and
                self.operator == other.operator and self.right_expression == other.right_expression)

    def __hash__(self):
        return hash((self.left_expression, self.operator, self.right_expression))

@dataclass
class Comparison(_Expression):
    # Exp == Exp
    left_expression: _Expression
    operator: ComparisonOperator
    right_expression: _Expression

    def __str__(self):
        op_map = {
            ComparisonOperator.EQ: '==',
            ComparisonOperator.GT: '>'
        }
        return f"{self.left_expression} {op_map[self.operator]} {self.right_expression}"

    def __eq__(self, other):
        if not isinstance(other, Comparison):
            return False
        return (self.left_expression == other.left_expression and
                self.operator == other.operator and self.right_expression == other.right_expression)

    def __hash__(self):
        return hash((self.left_expression, self.operator, self.right_expression))

@dataclass
class If(_Statement):
    # if(Exp) { Stm } [ else { Stm } ]
    condition: _Expression
    true_statement: _Statement
    false_statement: _Statement

    def __eq__(self, other):
        if not isinstance(other, If):
            return False
        return (self.condition == other.condition and
                self.true_statement == other.true_statement and self.false_statement == other.false_statement)

    def __hash__(self):
        return hash((self.condition, self.true_statement, self.false_statement))

@dataclass
class While(_Statement):
    # while ( Exp ) { Stm }
    condition: _Expression
    statements: List[_Statement]

    def __eq__(self, other):
        if not isinstance(other, While):
            return False
        return self.condition == other.condition and self.statements == other.statements

    def __hash__(self):
        return hash((self.condition, tuple(self.statements)))

@dataclass
class Output(_Statement):
    # output Exp;
    expression: _Expression

    def __eq__(self, other):
        if not isinstance(other, Output):
            return False
        return self.expression == other.expression

    def __hash__(self):
        return hash(self.expression)

@dataclass
class FunctionCall(_Expression):
    # Exp ( Exp, ... Exp )
    callee: _Expression
    expressions: List[_Expression]

    def __str__(self):
        args = ', '.join(str(e) for e in self.expressions)
        return f"{self.callee}({args})"

    def __eq__(self, other):
        if not isinstance(other, FunctionCall):
            return False
        return self.callee == other.callee and self.expressions == other.expressions

    def __hash__(self):
        return hash((self.callee, tuple(self.expressions)))

@dataclass
class Parenthesize(_Expression):
    # ( Exp )
    expression: _Expression

    def __str__(self):
        return f"({self.expression})"

    def __eq__(self, other):
        if not isinstance(other, Parenthesize):
            return False
        return self.expression == other.expression

    def __hash__(self):
        return hash(self.expression)

@dataclass
class Input(_Expression):
    # input

    def __str__(self):
        return "input"

    def __eq__(self, other):
        return isinstance(other, Input)

    def __hash__(self):
        return hash("input")

@dataclass
class Null(_Expression):
    # null

    def __str__(self):
        return "null"

    def __eq__(self, other):
        return isinstance(other, Null)

    def __hash__(self):
        return hash("null")

@dataclass
class Reference(_Expression):
    # & Id
    id: Id

    def __str__(self):
        return f"&{self.id}"

    def __eq__(self, other):
        if not isinstance(other, Reference):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

@dataclass
class Allocation(_Expression):
    # alloc Exp
    expression: _Expression

    def __str__(self):
        return f"alloc {self.expression}"

    def __eq__(self, other):
        if not isinstance(other, Allocation):
            return False
        return self.expression == other.expression

    def __hash__(self):
        return hash(self.expression)

@dataclass
class Struct(_Expression):
    # { Id : Exp, ... Id : Exp }
    fields: List[Field]

    def __str__(self):
        items = ', '.join(f"{f.key}: {f.Value}" for f in self.fields)
        return f"{{{items}}}"

    def __eq__(self, other):
        if not isinstance(other, Struct):
            return False
        return self.fields == other.fields

    def __hash__(self):
        return hash(tuple(self.fields))

@dataclass
class FieldAccess(_Expression):
    # Exp . Id
    expression: _Expression
    id: Id

    def __str__(self):
        return f"{self.expression}.{self.id}"

    def __eq__(self, other):
        if not isinstance(other, FieldAccess):
            return False
        return self.expression == other.expression and self.id == other.id

    def __hash__(self):
        return hash((self.expression, self.id))

@dataclass
class FieldAssignment(_Statement):
    # Id . Id = Exp;
    id: Id
    key: Id
    expression: _Expression

    def __eq__(self, other):
        if not isinstance(other, FieldAssignment):
            return False
        return self.id == other.id and self.key == other.key and self.expression == other.expression

    def __hash__(self):
        return hash((self.id, self.key, self.expression))

@dataclass
class DereferenceFieldAssignment(_Statement):
    # ( * Exp ) . Id = Exp;
    target: Dereference
    key: Id
    expression: _Expression

    def __eq__(self, other):
        if not isinstance(other, DereferenceFieldAssignment):
            return False
        return self.target == other.target and self.key == other.key and self.expression == other.expression

    def __hash__(self):
        return hash((self.target, self.key, self.expression))

class ASTBuilder(Transformer):
    def ids(self, items):
        return items

    def stmts(self, items):
        return items

    def exprs(self, items):
        return items

    def prog(self, items):
        return Program(items)

    def func(self, items):
        return Function(items[0], items[1], items[2], items[3])

    def stmt_return(self, items):
        return Return(items[0])

    def id(self, items):
        return Id(items[0])

    def int(self, items):
        return Int(items[0])

    def stmt_decl(self, items):
        return Declaration(items)

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
        return DereferenceAssignment(Dereference(items[0]), items[1])

    def prim_struct(self, items):
        return Struct(items)

    def factor_field(self, items):
        return FieldAccess(items[0], items[1])

    def stmt_field_assign(self, items):
        return FieldAssignment(items[0], items[1], items[2])

    def stmt_deref_field_assign(self, items):
        return DereferenceFieldAssignment(Dereference(items[0]), items[1], items[2])

    def prim_null(self, items):
        return Null()

def getTransformer():
    return ast_utils.create_transformer(this_module, ASTBuilder())