import sys
from asyncio import Condition

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

@dataclass
class Int(_Expression):
    # 0, 1, -1, ...
    value: int

@dataclass
class Field(_Ast):
    # Id : Exp
    key: Id
    Value: _Expression

@dataclass
class Declaration(_Statement):
    # var Id
    ids: List[Id]

@dataclass
class Assignment(_Statement):
    # Id = Exp;
    id: Id
    expression: _Expression

@dataclass
class DereferenceAssignment(_Statement):
    # *Exp = Exp;
    target: _Expression
    expression: _Expression

@dataclass
class Return(_Statement):
    # return Exp;
    expression: _Expression

@dataclass
class Function(_Ast):
    # Id ( Id, ... Id ) { [ var id, ... Id ] stm return exp; }
    name: Id
    parameters: List[Id]
    statements: List[_Statement]
    return_statement: Return

@dataclass
class Program(_Ast):
    # Fun, ... Fun
    functions: List[Function]

@dataclass
class Arithmetic(_Expression):
    # Exp + Exp
    left_expression: _Expression
    operator: ArithmeticOperator
    right_expression: _Expression

@dataclass
class Comparison(_Expression):
    # Exp == Exp
    left_expression: _Expression
    operator: ComparisonOperator
    right_expression: _Expression

@dataclass
class If(_Statement):
    # if(Exp) { Stm } [ else { Stm } ]
    condition: _Expression
    true_statement: _Statement
    false_statement: _Statement

@dataclass
class While(_Statement):
    # while ( Exp ) { Stm }
    condition: _Expression
    statements: List[_Statement]

@dataclass
class Output(_Statement):
    # output Exp;
    expression: _Expression

@dataclass
class FunctionCall(_Expression):
    # Exp ( Exp, ... Exp )
    callee: _Expression
    expressions: List[_Expression]

@dataclass
class Parenthesize(_Expression):
    # ( Exp )
    expression: _Expression

@dataclass
class Input(_Expression):
    # input
    pass

@dataclass
class Null(_Expression):
    # null
    pass

@dataclass
class Reference(_Expression):
    # * Exp
    id: Id

@dataclass
class Dereference(_Expression):
    # & Id
    expression: _Expression

@dataclass
class Allocation(_Expression):
    # alloc Exp
    expression: _Expression

@dataclass
class Struct(_Expression):
    # { Id : Exp, ... Id : Exp }
    fields: List[Field]

@dataclass
class FieldAccess(_Expression):
    # Exp . Id
    expression: _Expression
    id: Id

@dataclass
class FieldAssignment(_Statement):
    # Id . Id = Exp;
    id: Id
    key: Id
    expression: _Expression

@dataclass
class DereferenceFieldAssignment(_Statement):
    # ( * Exp ) . Id = Exp;
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

"""
Type -> int
	| ↑ Type
	| (Type, …, Type) -> Type
	| µ TypeVar.Type
	| TypeVar
"""
class IntType:
    pass

@dataclass
class Type:
    value: _Expression

@dataclass
class PointerType:
    base: Type

@dataclass
class FunctionType:
    params: list[Type]
    result: Type

@dataclass
class TypeVar:
    name: str

@dataclass
class RecursiveType:
    var: TypeVar
    body: Type

@dataclass
class TypeEqualityConstraint:
    left: Type
    right: Type

@dataclass
class FunctionTypeConstraint:
    #typeVariable: list = field(default_factory=list)
    typeConstraint: list = field(default_factory=list)

    def __str__(self):
        if not self.typeConstraint:
            return "FunctionTypeConstraint:\n  (empty)"
        return "FunctionTypeConstraint:\n" + "\n".join(
            f"  - {item}" for item in self.typeConstraint
        )


    return result
"""

@dataclass
class ASTVisitor:
    method_name: str

    def visit(self, node: _Ast) -> Any:
        """노드 타입에 따라 적절한 visit 메서드 호출"""
        # 예: Function 노드 -> 'visit_Function' 찾기
        self.method_name = f'visit_{node.__class__.__name__}'

        # 해당 메서드가 있으면 그것을, 없으면 generic_visit 사용
        visitor = getattr(self, self.method_name, self.generic_visit)

        return visitor(node)

    def generic_visit(self, node: _Ast) -> Any:
        print('no node: ' + self.method_name)


# 사용 예제: 모든 변수 이름 수집
@dataclass
class VariableCollector(ASTVisitor):
    functionDict = {}
    functionName = ""

    def visit_list(self, node: list):
        print('----- visit_list')

        for item in node:
            self.visit(item)

    def visit_Program(self, node: Program):
        print('----- visit_Program')

        for func in node.functions:
            # function 단위로 타입 검사를 하기 때문에 여기서 전부 올바른지 확인해야 함
            self.visit(func)

    def visit_Function(self, node: Function):
        # X(X1, ..., Xn) { ...return E; }: [X] = ([X1], ..., [Xn]) -> [E]
        # main(X1, ..., Xn) { ...return E; }: [X1] = ... [Xn] = [E] = int
        print('----- visit_Function')

        # function 추가
        functionName = node.name.name
        self.functionName = functionName
        self.functionDict[self.functionName] = FunctionTypeConstraint()

        # function 가져오기
        function = self.functionDict[self.functionName]

        # Function type constraint 추가
        params = node.parameters if isinstance(node.parameters, list) else [node.parameters]
        temp = [Type(p) for p in params]

        self.visit(node.return_statement.expression)

        constraint1 = TypeEqualityConstraint(
            Type(node.name),
            FunctionType(
                temp,
                Type(node.return_statement.expression)
            )
        )
        function.typeConstraint.append(constraint1)

        self.visit(node.statements)

        print(function)

    def visit_Reference(self, node: Reference):
        # &X: [&X] = ↑[X]
        print('----- visit_Reference')

        # function 가져오기
        function = self.functionDict[self.functionName]

        # Reference type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            PointerType(node.id)
        )
        function.typeConstraint.append(constraint1)

    def visit_Dereference(self, node: Dereference):
        # *E: [E] = ↑[*E]
        print('----- visit_Dereference')

        # function 가져오기
        function = self.functionDict[self.functionName]

        self.visit(node.expression)

        # Dereference type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node.expression),
            PointerType(node)
        )
        function.typeConstraint.append(constraint1)

    def visit_Parenthesize(self, node: Parenthesize):
        print('----- visit_Parenthesize')

        self.visit(node.expression)

    def visit_FunctionCall(self, node: FunctionCall):
        # E(E1, ..., En): [E] = ([E1], ..., [En]) -> [E(E1, ..., En)]
        print('----- visit_FunctionCall')

        # function 가져오기
        function = self.functionDict[self.functionName]

        # If type constraint 추가
        self.visit(node.callee)
        self.visit(node.expressions)

        constraint1 = TypeEqualityConstraint(
            Type(node.callee),
            FunctionType(
                [Type(expr) for expr in node.expressions],
                Type(node)
            )
        )
        function.typeConstraint.append(constraint1)

    def visit_Allocation(self, node: Allocation):
        # alloc E: [alloc E] = ↑[E]
        print('----- visit_Allocation')

        # function 가져오기
        function = self.functionDict[self.functionName]

        self.visit(node.expression)

        # Allocation type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            PointerType(node.expression)
        )
        function.typeConstraint.append(constraint1)

    def visit_Int(self, node: Int):
        # I: [I] = int
        print('----- visit_Int')

        # function 가져오기
        function = self.functionDict[self.functionName]

        # Int type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            IntType
        )
        function.typeConstraint.append(constraint1)

    def visit_Id(self, node: Id):
        print('----- visit_Id')
        pass

    def visit_Input(self, node: Input):
        # input: [input] = int
        print('----- visit_Input')

        # function 가져오기
        function = self.functionDict[self.functionName]

        # Input type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            IntType
        )
        function.typeConstraint.append(constraint1)

    def visit_Assignment(self, node: Assignment):
        # X = E: [X] = [E]
        print('----- visit_Assignment')

        # function 가져오기
        function = self.functionDict[self.functionName]

        # Assignment type constraint 추가
        self.visit(node.expression)

        constraint1 = TypeEqualityConstraint(
            Type(node.id),
            Type(node.expression)
        )
        function.typeConstraint.append(constraint1)

    def visit_Declaration(self, node: Declaration):
        print('----- visit_Declaration')
        pass

    def visit_DereferenceAssignment(self, node: DereferenceAssignment):
        # *E1 = E2: [E1] = ↑[E2]
        print('----- visit_DereferenceAssignment')

        # function 가져오기
        function = self.functionDict[self.functionName]

        self.visit(node.target)
        self.visit(node.expression)

        # DereferenceAssignment type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node.target),
            PointerType(node.expression)
        )
        function.typeConstraint.append(constraint1)

    def visit_If(self, node: If):
        # if(E) S: [E] = int
        # if(E) S1 else S2: [E] = int
        print('----- visit_If')

        # function 가져오기
        function = self.functionDict[self.functionName]

        # If type constraint 추가
        self.visit(node.condition)

        constraint1 = TypeEqualityConstraint(
            Type(node.condition),
            IntType
        )
        function.typeConstraint.append(constraint1)

        self.visit(node.true_statement)
        if node.false_statement != None:
            self.visit(node.false_statement)

    def visit_Comparison(self, node: Comparison):
        print('----- visit_Comparison')

        # function 가져오기
        function = self.functionDict[self.functionName]

        # Comparison type constraint 추가
        self.visit(node.left_expression)
        self.visit(node.right_expression)

        constraint1 = TypeEqualityConstraint(
            Type(node.left_expression),
            Type(node.right_expression)
        )
        constraint2 = TypeEqualityConstraint(
            Type(node),
            IntType
        )
        function.typeConstraint += [constraint1, constraint2]

    def visit_Arithmetic(self, node: Arithmetic):
        print('----- visit_Arithmetic')

        # function 가져오기
        function = self.functionDict[self.functionName]

        # Arithmetic type constraint 추가
        self.visit(node.left_expression)
        self.visit(node.right_expression)

        constraint1 = TypeEqualityConstraint(
            Type(node),
            IntType
        )
        constraint2 = TypeEqualityConstraint(
            Type(node.left_expression),
            IntType
        )
        constraint3 = TypeEqualityConstraint(
            Type(node.right_expression),
            IntType
        )
        function.typeConstraint += [constraint1, constraint2, constraint3]