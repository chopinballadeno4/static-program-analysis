from dataclasses import dataclass, field

from lark import Lark
from pathlib import Path
from common.printer import print_constraints, print_type_parent_relation
from type import tip_constraint as constraint
from ir.tip_ast import get_ast
from type.tip_constraint import ConstraintCollector
from type.tip_unification import UnificationSolver

# /spa 디렉터리 경로
BASE_DIR = Path(__file__).resolve().parent

@dataclass
class TipAnalysis:
    START = 'prog'

    syntax = (BASE_DIR / "syntax" / "tip.lark").read_text(encoding="utf-8")
    program = (BASE_DIR / "example" / "type" / "example7.txt").read_text(encoding="utf-8").split('"""', 1)[0]
    parser: Lark = None
    cst = None
    ast = None
    constraints: list[constraint.TypeEqualityConstraint] = field(init=False)
    record_fields: set[str] = field(init=False)
    type_parent_relation: dict = field(init=False, default_factory=dict)

    def set_parser(self):
        self.parser = Lark(
            self.syntax,
            start = self.START
        )

    def parse_program(self):
        self.cst = self.parser.parse(self.program)


if __name__ == '__main__':
    analyzer = TipAnalysis()

    analyzer.set_parser()
    analyzer.parse_program()
    analyzer.ast = get_ast(analyzer.cst)

    # type analysis ==========
    constraint_collector = ConstraintCollector(analyzer.ast)
    analyzer.constraints = constraint_collector.constraints
    analyzer.record_fields = constraint_collector.record_fields

    unification_solver = UnificationSolver(analyzer.constraints)
    analyzer.type_parent_relation = unification_solver.type_parent_relation

    # 콘솔 출력 ==========
    print_constraints(analyzer.constraints)
    print_type_parent_relation(analyzer.type_parent_relation)