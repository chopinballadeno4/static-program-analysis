"""
I: [[I]] = int
E1 op E2: [[E1]] = [[E2]] = [[E1 op E2]] = int
E1 == E2: [[E1]] = [[E2]] ∧ [[E1 == E2]] = int
input: [[input]] = int
X = E: [[X]] = [[E]]
output E: [[E]] = int
if (E) S: [[E]] = int
if (E) S1 else S2: [[E]] = int
while (E) S: [[E]] = int
X(X1,...,Xn) { ...return E; }: [[X]] = ([[X1]],...,[[Xn]]) → [[E]]
E(E1,...,En): [[E]] = ([[E1]],...,[[En]]) → [[E(E1,...,En)]]
alloc E: [[alloc E]] = [[E]]
&X: [[&X]] = [[X]]
null: [[null]] = α
*E: [[E]] = [[*E]]
*E1 = E2: [[E1]] = [[E2]]

Type -> int
	| ↑ Type
	| (Type, …, Type) -> Type
	| µ TypeVar.Type
	| TypeVar
	| {Id: Type, ... Id: Type}
	| absence
"""
from __future__ import annotations
from dataclasses import dataclass, field
from ir import tip_ast as ast

class _Type:
    pass

@dataclass
class Type(_Type):
    value: ast._Expression

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
        return f"{self.left} = {self.right}"


def removeParenthesize(expression):
    """
    remove parenthesize and get pure expression
    + spa p23 - "parenthesized expression are not present in the abstract syntax"
    :param expression: (( Exp ))
    :return: Exp
    """
    if isinstance(expression, ast.Parenthesize):
        return removeParenthesize(expression.expression)
    else:
        return expression

@dataclass
class ConstraintCollector:
    target_ast: ast._Ast

    record_fields: set[ast.Id] = field(init=False, default_factory=set)
    record_constraints: list[tuple[str, TypeEqualityConstraint]] = field(init=False,default_factory=list)
    constraints: list[TypeEqualityConstraint] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.visit(self.target_ast)
        # Record 타입은 field 수집을 위해 constraint 에 마지막에 추가
        self.set_record_field()

    def visit(self, node: ast._Ast):
        # 노드 타입에 따라 적절한 visit 메서드 호출
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name)

        return visitor(node)

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

    def visit_Program(self, node: ast.Program):
        for func in node.functions:
            # function 단위로 타입 검사를 하기 때문에 여기서 전부 올바른지 확인해야 함
            self.visit(func)

    def visit_Function(self, node: ast.Function):
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

    def visit_Reference(self, node: ast.Reference):
        # &X: [&X] = ↑[X]
        # Reference type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            PointerType(Type(node.id))
        )
        self.constraints.append(constraint1)

    def visit_Dereference(self, node: ast.Dereference):
        # *E: [E] = ↑[*E]
        self.visit(node.expression)

        # Dereference type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node.expression),
            PointerType(Type(node))
        )
        self.constraints.append(constraint1)

    def visit_Parenthesize(self, node: ast.Parenthesize):
        self.visit(node.expression)

    def visit_FunctionCall(self, node: ast.FunctionCall):
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

    def visit_Allocation(self, node: ast.Allocation):
        # alloc E: [alloc E] = ↑[E]
        self.visit(node.expression)

        # Allocation type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            PointerType(Type(node.expression))
        )
        self.constraints.append(constraint1)

    def visit_Int(self, node: ast.Int):
        # I: [I] = int
        # Int type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            IntType()
        )
        self.constraints.append(constraint1)

    def visit_Id(self, node: ast.Id):
        pass

    def visit_Input(self, node: ast.Input):
        # input: [input] = int
        # Input type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node),
            IntType()
        )
        self.constraints.append(constraint1)

    def visit_Assignment(self, node: ast.Assignment):
        # X = E: [X] = [E]
        # Assignment type constraint 추가
        self.visit(node.expression)

        constraint1 = TypeEqualityConstraint(
            Type(node.id),
            Type(node.expression)
        )
        self.constraints.append(constraint1)

    def visit_Declaration(self, node: ast.Declaration):
        pass

    def visit_DereferenceAssignment(self, node: ast.DereferenceAssignment):
        # *E1 = E2: [E1] = ↑[E2]
        self.visit(node.target)
        self.visit(node.expression)

        # DereferenceAssignment type constraint 추가
        constraint1 = TypeEqualityConstraint(
            Type(node.target.expression),
            PointerType(Type(node.expression))
        )
        self.constraints.append(constraint1)

    def visit_If(self, node: ast.If):
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

    def visit_Comparison(self, node: ast.Comparison):
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

    def visit_Arithmetic(self, node: ast.Arithmetic):
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

    def visit_Struct(self, node: ast.Struct):
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

    def visit_FieldAccess(self, node: ast.FieldAccess):
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