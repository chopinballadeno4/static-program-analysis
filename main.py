from dataclasses import dataclass, field

from lark import Lark, Tree
from pathlib import Path
from common.printer import print_constraints, print_type_parent_relation, print_cfg, print_fixed_point_sign_analysis
from type import tip_constraint as constraint
from ir import tip_ast, tip_cfg
from ir.tip_ast import get_ast
from type.tip_constraint import ConstraintCollector
from type.tip_unification import UnificationSolver
from lattice.tip_lattice import FixedPointSolver
from ir.tip_cfg import GraphBuilder

# /spa 디렉터리 경로
BASE_DIR = Path(__file__).resolve().parent

@dataclass
class TipAnalysis:
    START = 'prog'

    syntax = (BASE_DIR / "syntax" / "tip.lark").read_text(encoding="utf-8")
    program = (BASE_DIR / "example" / "lattice" / "example1.txt").read_text(encoding="utf-8").split('"""', 1)[0]
    parser: Lark = field(init=False, default=None)
    cst: Tree = field(init=False, default=None)
    ast: tip_ast.Program = field(init=False, default=None)
    cfg: tip_cfg._Node = field(init=False, default=None)
    constraints: list[constraint.TypeEqualityConstraint] = field(init=False, default=None)
    record_fields: set[str] = field(init=False, default=None)
    type_parent_relation: dict = field(init=False, default=None)

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
    """
    constraint_collector = ConstraintCollector(analyzer.ast)
    analyzer.constraints = constraint_collector.constraints
    analyzer.record_fields = constraint_collector.record_fields
    print_constraints(analyzer.constraints) # 콘솔 출력

    unification_solver = UnificationSolver(analyzer.constraints, analyzer.record_fields)
    analyzer.type_parent_relation = unification_solver.type_parent_relation
    print_type_parent_relation(analyzer.type_parent_relation) # 콘솔 출력
    """

    # lattice theory ==========
    graph_builder = GraphBuilder(analyzer.ast)
    analyzer.cfg = graph_builder.graph
    print_cfg(analyzer.cfg)

    # Sign analysis ==========
    fixed_point_solver = FixedPointSolver(analyzer.cfg)
    print_fixed_point_sign_analysis(fixed_point_solver.fixed_point)