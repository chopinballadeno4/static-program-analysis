"""
"""
from dataclasses import dataclass, field
from enum import Enum, auto

from ir import tip_cfg as cfg
from ir import tip_ast as ast
from ir.tip_ast import ArithmeticOperator, ComparisonOperator


class Top:
    def __repr__(self):
        return 'ㅜ'

class Bottom:
    def __repr__(self):
        return 'ㅗ'

class _Lattice:
    pass

@dataclass
class MapLattice(_Lattice):
    lattice: dict

    def __eq__(self, other):
        if not isinstance(other, MapLattice):
            return False

        for key, value in self.lattice.items():
            if key not in other.lattice:
                return False
            else:
                if value != other.lattice[key]:
                    return False

        return True

@dataclass
class ProductLattice(_Lattice):
    lattice: list[_Lattice] = field(default_factory=list)

class SignLattice(Enum):
    PLUS = "+"
    MINUS = "-"
    ZERO = "0"
    TOP = Top()
    BOTTOM = Bottom()

class State:
    pass

def check_expression(base_status, value):
    """
    - Exp = Int (-, 0, +)
    - Exp = Input (ㅜ)
    - Exp = Exp + Exp
    - Exp = Exp - Exp
    ...
    """
    if isinstance(value, ast.Int):
        int_value = int(value.value)
        if int_value > 0:
            return SignLattice.PLUS
        elif int_value < 0:
            return SignLattice.MINUS
        else:
            return SignLattice.ZERO
    elif isinstance(value, ast.Id):
        return base_status.lattice[str(value.name)]
    elif isinstance(value, ast.Input):
        return SignLattice.TOP
    elif isinstance(value, ast.Arithmetic):
        if value.operator is ast.ArithmeticOperator.ADD:
            if (check_expression(base_status, value.left_expression) == SignLattice.PLUS) and (check_expression(base_status, value.right_expression) == SignLattice.PLUS):
                return SignLattice.PLUS
            elif (check_expression(base_status, value.left_expression) == SignLattice.MINUS) and (check_expression(base_status, value.right_expression) == SignLattice.MINUS):
                return SignLattice.MINUS
            else:
                return SignLattice.TOP
        elif value.operator is ast.ArithmeticOperator.SUB:
            if (check_expression(base_status, value.left_expression) == SignLattice.MINUS) and (check_expression(base_status, value.right_expression) == SignLattice.PLUS):
                return SignLattice.MINUS
            elif (check_expression(base_status, value.left_expression) == SignLattice.PLUS) and (check_expression(base_status, value.right_expression) == SignLattice.MINUS):
                return SignLattice.PLUS
            else:
                return SignLattice.TOP
        # ...

def validate_sign(base_lattice, state):
    new_dict = {}

    if state.base_index == -1:
        for key, value in state.state_sign.lattice.items():
            sign: SignLattice = state.state_sign.lattice[key]
            new_dict[key] = sign

        return MapLattice(new_dict)
    else:
        if not isinstance(base_lattice, Bottom):
            for key, value in state.state_sign.lattice.items():
                sign: SignLattice = check_expression(base_lattice, value)
                new_dict[key] = sign

            for key, value in base_lattice.lattice.items():
                if key not in new_dict:
                    new_dict[key] = value

            return MapLattice(new_dict)
        else:
            return Bottom()

@dataclass
class ConstraintFunction:
    """
    f1, ..., fn : L^n -> L
     - Sn = fn(S1, ..., Sn)
    """
    #input_lattices: list[_Lattice] = field(init=False, default_factory=list)
    output_lattice: State

@dataclass
class CommonConstraintFunction:
    """
    f : L^n -> L^n
     - f(S1, ..., Sn) = (f1(S1, ..., Sn), ..., fn(S1, ..., Sn))
    """
    #input_lattices: list[_Lattice] = field(init=False, default_factory=list)
    output_lattices: list[ConstraintFunction]

    def execute(self, x):
        """
        f1, ..., fn : L^n -> L
        - Sn = fn(S1, ..., Sn)
        """
        new_x = []

        # each iteration it applies all the constraint functions
        for func in self.output_lattices:
            base_index = func.output_lattice.base_index
            print(base_index)
            new_x.append(validate_sign(x[base_index], func.output_lattice))

        return new_x

@dataclass
class SignState(State):
    """
    xi 은 i 번째 줄 직후의 변수와 요약값 매핑 상태를 표현
    """
    base_index: int
    state_sign: MapLattice

def validate_arithmetic_sign(l: SignLattice, arith: ArithmeticOperator, r: SignLattice):
    plus = SignLattice.PLUS
    minus = SignLattice.MINUS
    zero = SignLattice.ZERO
    top = SignLattice.TOP
    bottom = SignLattice.BOTTOM

    order = [bottom, zero, minus, plus, top]

    add_list = [
        [bottom, bottom, bottom, bottom, bottom],
        [bottom, zero, minus, plus, top],
        [bottom, minus, minus, top, top],
        [bottom, plus, top, plus, top],
        [bottom, top, top, top, top]
    ]
    sub_list = [
        [bottom, bottom, bottom, bottom, bottom],
        [bottom, zero, plus, minus, top],
        [bottom, minus, top, minus, top],
        [bottom, plus, plus, top, top],
        [bottom, top, top, top, top]
    ]
    mul_list = [
        [bottom, bottom, bottom, bottom, bottom],
        [bottom, zero, zero, zero, zero],
        [bottom, zero, plus, minus, top],
        [bottom, zero, minus, plus, top],
        [bottom, zero, top, top, top]
    ]
    div_list = [
        [bottom, bottom, bottom, bottom, bottom],
        [bottom, bottom, zero, zero, top],
        [bottom, bottom, top, top, top],
        [bottom, bottom, top, top, top],
        [bottom, bottom, top, top, top]
    ]

    table = {
        ArithmeticOperator.ADD: add_list,
        ArithmeticOperator.SUB: sub_list,
        ArithmeticOperator.MUL: mul_list,
        ArithmeticOperator.DIV: div_list,
    }

    return table[arith][order.index(l)][order.index(r)]

def validate_comparison_sign(l: SignLattice, com: ComparisonOperator, r: SignLattice):
    plus = SignLattice.PLUS
    minus = SignLattice.MINUS
    zero = SignLattice.ZERO
    top = SignLattice.TOP
    bottom = SignLattice.BOTTOM

    order = [bottom, zero, minus, plus, top]

    gt_list = [
        [bottom, bottom, bottom, bottom, bottom],
        [bottom, zero, plus, zero, top],
        [bottom, zero, top, zero, top],
        [bottom, plus, plus, top, top],
        [bottom, top, top, top, top]
    ]

    eq_list = [
        [bottom, bottom, bottom, bottom, bottom],
        [bottom, plus, zero, zero, top],
        [bottom, zero, top, zero, top],
        [bottom, zero, zero, top, top],
        [bottom, top, top, top, top]
    ]

    table = {
        ComparisonOperator.GT: gt_list,
        ArithmeticOperator.EQ: eq_list
    }

    return table[com][order.index(l)][order.index(r)]

@dataclass
class FixedPointSolver:
    target_cfg: cfg._Node

    checked_node: dict = field(init=False, default_factory=dict)
    constraint_functions: list[ConstraintFunction] = field(init=False, default_factory=list)
    fixed_point = None

    def __post_init__(self):
        self.visit_cfg(self.target_cfg, -1)
        common_constraint_function = CommonConstraintFunction(self.constraint_functions)

        self.fixed_point = self.naive_fixed_point_algorithm(common_constraint_function)

    def make_map_lattice(self, stmt: ast._Statement):
        map_lattice = {}

        if isinstance(stmt, ast.Declaration):
            for id in stmt.ids:
                if id not in map_lattice:
                    map_lattice[str(id.name)] = SignLattice.TOP
        elif isinstance(stmt, ast.Assignment):
            map_lattice[str(stmt.id)] = stmt.expression

        return map_lattice

    def visit_cfg(self, current_node, index: int):
        if isinstance(current_node, cfg.Entry):
            self.visit_cfg(current_node.successor, index)
        elif isinstance(current_node, cfg.NormalNode):
            if current_node not in self.checked_node:
                self.checked_node[current_node] = auto()
                self.constraint_functions.append(
                    ConstraintFunction(
                        SignState(
                            index,
                            MapLattice(self.make_map_lattice(current_node.statement))
                        )
                    )
                )
            self.visit_cfg(current_node.successor, index + 1)
        elif isinstance(current_node, cfg.BranchNode):
            if current_node not in self.checked_node:
                self.checked_node[current_node] = auto()
                self.constraint_functions.append(
                    ConstraintFunction(
                        SignState(
                            index,
                            MapLattice(self.make_map_lattice(current_node.statement))
                        )
                    )
                )
            # self.visit_cfg(current_node.true_successor) while 문에서 무한루프 가능 (처리 필요)
            self.visit_cfg(current_node.false_successor, index + 1)
        elif isinstance(current_node, cfg.Exit):
            return

    def check_fixed_point(self, x1, x2):
        for a, b in zip(x1, x2):
            if a != b:
                return False

        return True

    def init_lattices(self):
        return [Bottom() for _ in range(len(self.constraint_functions))]

    def naive_fixed_point_algorithm(self, f):
        """
        function NaiveFixedPointAlgorithm(f):
            x := ㅗ
            while x ≠ f(x) do
                x := f(x)
            end
            return x
        end
        """
        x = self.init_lattices()

        while not self.check_fixed_point(x, f.execute(x)):
            x = f.execute(x)

        return x