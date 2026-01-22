from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from ir.tip_ast import _Expression, _Ast, Program, Function, Parenthesize, Reference, Dereference, Assignment, Id, Int, \
    Field, Declaration, DereferenceAssignment, Return, Arithmetic, Comparison, If, While, Output, FunctionCall, Input, \
    Null, Allocation, Struct, FieldAccess, FieldAssignment, DereferenceFieldAssignment

"""
Type -> int
	| ↑ Type
	| (Type, …, Type) -> Type
	| µ TypeVar.Type
	| TypeVar
	| {Id: Type, ... Id: Type}
	| absence
"""
class _Type:
    pass

@dataclass
class Type(_Type):
    value: _Expression

    def __str__(self):
        return f"[{self.value}]"

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return self.value == other.value

    def __hash__(self):
        return hash(self.value)

class IntType(_Type):
    def __str__(self):
        return "int"

    def __eq__(self, other):
        return isinstance(other, IntType)

    def __hash__(self):
        return hash("int")

@dataclass
class PointerType(_Type):
    base: Type

    def __str__(self):
        return f"↑{self.base}"

    def __eq__(self, other):
        if not isinstance(other, PointerType):
            return False
        return self.base == other.base

    def __hash__(self):
        return hash(self.base)

@dataclass
class FunctionType(_Type):
    params: list[Type]
    result: Type

    def __str__(self):
        params_str = ', '.join(str(p) for p in self.params)
        return f"({params_str}) -> {self.result}"

    def __eq__(self, other):
        if not isinstance(other, FunctionType):
            return False
        return self.params == other.params and self.result == other.result

    def __hash__(self):
        return hash((tuple(self.params), self.result))

@dataclass
class TypeVar(_Type):
    def __str__(self):
        return "typevar"

    def __eq__(self, other):
        return isinstance(other, TypeVar)

    def __hash__(self):
        return hash("typevar")

@dataclass
class RecursiveType(_Type):
    var: TypeVar
    body: Type

    def __eq__(self, other):
        if not isinstance(other, RecursiveType):
            return False
        return self.var == other.var and self.body == other.body

    def __hash__(self):
        return hash((self.var, self.body))

@dataclass
class StructType(_Type):
    field_map: dict

    def __eq__(self, other):
        if not isinstance(other, StructType):
            return False
        return self.field_map == other.field_map

    def __hash__(self):
        return hash(tuple(sorted(self.field_map.items(), key=lambda x: str(x[0]))))

    def __str__(self):
        items = ', '.join(f"{k}: {v}" for k, v in self.field_map.items())
        return f"{{{items}}}"

@dataclass
class AbsenceType(_Type):
    def __str__(self):
        return '*'

    def __eq__(self, other):
        return isinstance(other, AbsenceType)

    def __hash__(self):
        return hash("absence")

@dataclass
class TypeEqualityConstraint:
    left: Type
    right: Type

    def __str__(self):
        return f"  - {self.left} = {self.right}"


def removeParenthesize(expression):
    """
    remove parenthesize and get pure expression
    + spa p23 - "parenthesized expression are not present in the abstract syntax"
    :param expression: (( Exp ))
    :return: Exp
    """
    if isinstance(expression, Parenthesize):
        return removeParenthesize(expression.expression)
    else:
        return expression


@dataclass
class ASTVisitor:
    def visit(self, node: _Ast) -> Any:
        """노드 타입에 따라 적절한 visit 메서드 호출"""
        # 예: Function 노드 -> 'visit_Function' 찾기
        method_name = f'visit_{node.__class__.__name__}'

        # 해당 메서드가 있으면 그것을, 없으면 generic_visit 사용
        visitor = getattr(self, method_name, lambda n: self.generic_visit(method_name))

        return visitor(node)

    def generic_visit(self, method_name: str) -> Any:
        print('no node: ' + method_name)


# 사용 예제: 모든 변수 이름 수집
@dataclass
class ConstraintCollector(ASTVisitor):
    record_constraints: list[tuple[str, TypeEqualityConstraint]] = field(default_factory=list)
    record_fields: set[Id] = field(default_factory=set)

    constraints: list[TypeEqualityConstraint] = field(default_factory=list)
    unique_constraints: list[TypeEqualityConstraint] = field(default_factory=list)
    #unique_constraint_elements: list[Type] = field(default_factory=list)

    def print_constraints(self):
        # 수집한 constraints
        print('[constraints]')
        for c in self.constraints:
            print(f" - {str(c)}")

        # 중복 없는 constraints
        print('\n[unique_constraints]')
        for c in self.unique_constraints:
            print(f" - {str(c)}")

        # 중복 없는 type variable
        # print('\n[unique_constraint_elements]')
        # for c in self.unique_constraint_elements:
        #     print(f" - {str(c)}")

    def set_unique_constraints(self):
        if len(self.constraints) > 0:
            self.unique_constraints = []
            for c in self.constraints:
                if c not in self.unique_constraints:
                    self.unique_constraints.append(c)

            # self.unique_constraint_elements = []
            # for c in self.unique_constraints:
            #     if c.left not in self.unique_constraint_elements:
            #         self.unique_constraint_elements.append(c.left)
            #     if c.right not in self.unique_constraint_elements:
            #         self.unique_constraint_elements.append(c.right)

    def set_record_field(self):
        for element in self.record_constraints:
            type = element[0]
            value = element[1]
            if type == 'field_access':
                # [E] = { ..., X: [E.X] ,... } , 없는 field 는 TypeVar 로 추가
                for f in self.record_fields:
                    if f not in value.right.field_map:
                        value.right.field_map[f] = TypeVar()

            elif type == 'struct':
                # [{ X1:E1, ... Xn:En }] = { X1:[E1], ... Xn:[En] } , 없는 field 는 absence 로 추가
                for f in self.record_fields:
                    if f not in value.right.field_map:
                        value.right.field_map[f] = AbsenceType()
            else:
                print('[ERROR]')

            # 원본 제약 배열에 넣어주기
            self.constraints.append(value)

    def visit_list(self, node: list):
        for item in node:
            self.visit(item)

    def visit_Program(self, node: Program):
        for func in node.functions:
            # function 단위로 타입 검사를 하기 때문에 여기서 전부 올바른지 확인해야 함
            self.visit(func)

    def visit_Function(self, node: Function):
        # X(X1, ..., Xn) { ...return E; }: [X] = ([X1], ..., [Xn]) -> [E]
        params = []
        if node.parameters is not None:
            if isinstance(node.parameters, list):
                params = node.parameters
            else:
                params = [node.parameters]

        if node.name.name == 'main':
            # main(X1, ..., Xn) { ...return E; }: [X1] = ... [Xn] = [E] = int
            self.constraints.extend(
                TypeEqualityConstraint(Type(param), IntType())
                for param in params
            )
            self.constraints.append(
                TypeEqualityConstraint(
                    Type(removeParenthesize(node.return_statement.expression)),
                    IntType()
                )
            )

        # Function type constraint 추가
        temp = [Type(p) for p in params]

        self.visit(node.return_statement.expression)

        constraint1 = TypeEqualityConstraint(
            Type(node.name),
            FunctionType(
                temp,
                Type(node.return_statement.expression)
            )
        )
        self.constraints.append(constraint1)

        self.visit(node.statements)

    def visit_Reference(self, node: Reference):
        # &X: [&X] = ↑[X]
        # Reference type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            PointerType(Type(node.id))
        )
        self.constraints.append(constraint1)

    def visit_Dereference(self, node: Dereference):
        # *E: [E] = ↑[*E]
        self.visit(node.expression)

        # Dereference type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node.expression),
            PointerType(Type(node))
        )
        self.constraints.append(constraint1)

    def visit_Parenthesize(self, node: Parenthesize):
        self.visit(node.expression)

    def visit_FunctionCall(self, node: FunctionCall):
        """
        [q] = ↑ int
        [x(q, x)] = int
        [x] = ([q], [x]) -> [x(q, x)]
        => [x] = µt.(↑ int, t) -> int

        g = (x) -> foo
        foo(1, g(x))

        recursive 발생 조건
        - callee 가 인자로 다시 들어가는 경우
        """
        # E(E1, ..., En): [E] = ([E1], ..., [En]) -> [E(E1, ..., En)]
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
        self.constraints.append(constraint1)

    def visit_Allocation(self, node: Allocation):
        # alloc E: [alloc E] = ↑[E]
        self.visit(node.expression)

        # Allocation type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            PointerType(Type(node.expression))
        )
        self.constraints.append(constraint1)

    def visit_Int(self, node: Int):
        # I: [I] = int
        # Int type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            IntType()
        )
        self.constraints.append(constraint1)

    def visit_Id(self, node: Id):
        pass

    def visit_Input(self, node: Input):
        # input: [input] = int
        # Input type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            IntType()
        )
        self.constraints.append(constraint1)

    def visit_Assignment(self, node: Assignment):
        # X = E: [X] = [E]
        # Assignment type constraint 추가
        self.visit(node.expression)

        constraint1 = TypeEqualityConstraint(
            Type(node.id),
            Type(node.expression)
        )
        self.constraints.append(constraint1)

    def visit_Declaration(self, node: Declaration):
        pass

    def visit_DereferenceAssignment(self, node: DereferenceAssignment):
        # *E1 = E2: [E1] = ↑[E2]
        self.visit(node.target)
        self.visit(node.expression)

        # DereferenceAssignment type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node.target.expression),
            PointerType(Type(node.expression))
        )
        self.constraints.append(constraint1)

    def visit_If(self, node: If):
        # if(E) S: [E] = int
        # if(E) S1 else S2: [E] = int
        # If type constraint 추가
        self.visit(node.condition)

        constraint1 = TypeEqualityConstraint(
            Type(node.condition),
            IntType()
        )
        self.constraints.append(constraint1)

        self.visit(node.true_statement)
        if node.false_statement != None:
            self.visit(node.false_statement)

    def visit_Comparison(self, node: Comparison):
        # Comparison type constraint 추가
        self.visit(node.left_expression)
        self.visit(node.right_expression)

        constraint1 = TypeEqualityConstraint(
            Type(node.left_expression),
            Type(node.right_expression)
        )
        constraint2 = TypeEqualityConstraint(
            Type(node),
            IntType()
        )
        self.constraints += [constraint1, constraint2]

    def visit_Arithmetic(self, node: Arithmetic):
        # Arithmetic type constraint 추가
        self.visit(node.left_expression)
        self.visit(node.right_expression)

        constraint1 = TypeEqualityConstraint(
            Type(node),
            IntType()
        )
        # E1 op E2: [E1] = [E2] = [E1 or E2] = int
        constraint2 = TypeEqualityConstraint(
            Type(removeParenthesize(node.left_expression)),
            IntType()
        )
        constraint3 = TypeEqualityConstraint(
            Type(removeParenthesize(node.right_expression)),
            IntType()
        )
        self.constraints += [constraint1, constraint2, constraint3]

    def visit_Struct(self, node: Struct):
        # { X1:E1, ... Xn:En }: [{ X1:E1, ... Xn:En }] = { X1:[E1], ... Xn:[En] }
        field_map = dict()

        for f in node.fields:
            # field 목록 수집
            self.record_fields.add(f.key)

            if f.key not in field_map:
                self.visit(f.Value)
                field_map[f.key] = Type(f.Value)

        constraint1 = TypeEqualityConstraint(
            Type(node),
            StructType(field_map)
        )
        #self.constraints.append(constraint1)
        # record 에 absence 와 TypeVar 을 넣어주기 위해 지연
        self.record_constraints.append(("struct", constraint1))

    def visit_FieldAccess(self, node: FieldAccess):
        # E.X: [E] = { ..., X: [E.X] ,... }
        # field 목록 수집
        self.record_fields.add(node.id)

        field_map = dict()
        field_map[node.id] = Type(node)
        constraint1 = TypeEqualityConstraint(
            Type(node.expression),
            StructType(field_map)
        )
        #self.constraints.append(constraint1)
        # record 에 absence 와 TypeVar 를 넣어주기 위해 지연
        self.record_constraints.append(("field_access", constraint1))