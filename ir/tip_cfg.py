# succ(v) = successor
# pred(v) = predecessor
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto

from ir import tip_ast as ast

class BranchCategory(Enum):
    IF = auto()
    WHILE = auto()

class _Node:
    pass

@dataclass
class NormalNode(_Node):
    statement: ast._Statement
    predecessors: list[_Node] = field(default_factory=list)
    successor: _Node = field(init=False, default=None)

@dataclass
class BranchNode(_Node):
    # condition: ast._Expression
    statement: ast._Statement
    category: BranchCategory # IF, WHILE
    predecessors: list[_Node] = field(default_factory=list)
    true_successor: _Node = field(init=False, default=None)
    false_successor: _Node = field(init=False, default=None)

@dataclass
class Entry(_Node):
    successor: _Node = field(init=False, default=None)

@dataclass
class Exit(_Node):
    predecessors: list[_Node] = field(default_factory=list)

@dataclass
class GraphBuilder:
    target_ast: ast._Ast

    graph: _Node = field(init=False, default=None)
    head: _Node = field(init=False, default=None)

    def __post_init__(self):
        self.start_Program(self.target_ast)

    def start_Program(self, node: ast.Program):
        """
        Fun, ... Fun
        """
        for fun in node.functions:
            if fun.name.name == 'main':
                self.visit_function(fun)
                # graph 에 exit node 추가

    def visit_function(self, node: ast.Function):
        # Id ( Id, ... Id ) { [ var id, ... Id ] stm return exp; }
        function_statements = []

        function_statements.extend(node.statements)
        function_statements.append(node.return_statement)

        statement_list = self.make_statement_node(function_statements)

        # 함수 실행
        if node.name.name == 'main':
            self.graph = Entry()
            self.head = self.graph
            self.head.successor = statement_list[0]
            statement_list.append(Exit())

        self.run_function(statement_list, Exit())

    def run_function(self, statement_nodes: list[_Node], exit_node: _Node):
        """
        (prev) -> (node) -> (succ)
        1. prev 의 succ 에 node 지정
        2. node 의 prev 에 prev 추가
        3. node 의 succ 에 succ 지정
        """
        for i in range(len(statement_nodes)):
            node = statement_nodes[i]

            if i == len(statement_nodes) - 1:
                if isinstance(node, BranchNode) and node.category == BranchCategory.IF:
                    node.predecessors.append(self.head)  # 2
                    self.head = node

                    if node.statement.false_statements is None:
                        # IF: if ( Exp ) { Stm }
                        # condition: True
                        true_statement_node = self.make_statement_node(node.statement.true_statements)
                        if len(true_statement_node) > 0:
                            node.true_successor = true_statement_node[0]
                            self.run_function(
                                true_statement_node,
                                exit_node
                            )
                        else:
                            node.true_successor = exit_node
                        # condition: False
                        node.false_successor = exit_node # 3
                        self.head = node # head 변경
                    elif node.statement.false_statements is not None:
                        # IF: if ( Exp ) { Stm } else { Stm }
                        # condition: True
                        true_statement_node = self.make_statement_node(node.statement.true_statements)
                        if len(true_statement_node) > 0:
                            node.true_successor = true_statement_node[0]
                            self.run_function(
                                true_statement_node,
                                exit_node
                            )
                        else:
                            node.true_successor = exit_node
                        # condition: False
                        self.head = node # false 수행 전 head 변경

                        false_statement_node = self.make_statement_node(node.statement.false_statements)
                        if len(false_statement_node) > 0:
                            node.false_successor = false_statement_node[0]
                            self.run_function(
                                false_statement_node,
                                exit_node
                            )
                        else:
                            node.false_successor = exit_node
                        self.head = node # head 변경
                elif isinstance(node, BranchNode) and node.category == BranchCategory.WHILE:
                    # WHILE: while ( Exp ) { Stm }
                    node.predecessors.append(self.head)  # 2
                    self.head = node

                    # condition: True
                    statement_node = self.make_statement_node(node.statement.statements)
                    if len(statement_node) > 0:
                        node.true_successor = statement_node[0]
                        self.run_function(
                            statement_node,
                            node
                        )
                    else:
                        node.true_successor = node
                    # condition: False
                    node.false_successor = exit_node  # 3
                    self.head = node # head 변경
                elif isinstance(node, Exit):
                    node.predecessors.append(self.head)  # 2
                    self.head = node  # head 변경
                else:
                    # is not IF | WHILE
                    node.predecessors.append(self.head)  # 2
                    node.successor = exit_node  # 3
                    self.head = node  # head 변경
            else:
                if isinstance(node, BranchNode) and node.category == BranchCategory.IF:
                    node.predecessors.append(self.head)  # 2
                    self.head = node

                    if node.statement.false_statements is None:
                        # IF: if ( Exp ) { Stm }
                        # condition: True
                        true_statement_node = self.make_statement_node(node.statement.true_statements)
                        if len(true_statement_node) > 0:
                            node.true_successor = true_statement_node[0]
                            self.run_function(
                                true_statement_node,
                                statement_nodes[i + 1]
                            )
                        else:
                            node.true_successor = statement_nodes[i + 1]
                        # condition: False
                        node.false_successor = statement_nodes[i + 1]  # 3
                        self.head = node  # head 변경
                    elif node.statement.false_statements is not None:
                        # IF: if ( Exp ) { Stm } else { Stm }
                        # condition: True
                        true_statement_node = self.make_statement_node(node.statement.true_statements)
                        if len(true_statement_node) > 0:
                            node.true_successor = true_statement_node[0]
                            self.run_function(
                                true_statement_node,
                                statement_nodes[i + 1]
                            )
                        else:
                            node.true_successor = statement_nodes[i + 1]
                        # condition: False
                        self.head = node  # false 수행 전 head 변경

                        false_statement_node = self.make_statement_node(node.statement.false_statements)
                        if len(false_statement_node) > 0:
                            node.false_successor = false_statement_node[0]
                            self.run_function(
                                false_statement_node,
                                statement_nodes[i + 1]
                            )
                        else:
                            node.false_successor = statement_nodes[i + 1]
                        self.head = node  # head 변경
                elif isinstance(node, BranchNode) and node.category == BranchCategory.WHILE:
                    # WHILE: while ( Exp ) { Stm }
                    node.predecessors.append(self.head)  # 2
                    self.head = node

                    # condition: True
                    statement_node = self.make_statement_node(node.statement.statements)
                    if len(statement_node) > 0:
                        node.true_successor = statement_node[0]
                        self.run_function(
                            statement_node,
                            node
                        )
                    else:
                        node.true_successor = node
                    # condition: False
                    node.false_successor = statement_nodes[i + 1]  # 3
                    self.head = node  # head 변경
                else:
                    # is not IF | WHILE
                    node.predecessors.append(self.head)  # 2
                    node.successor = statement_nodes[i + 1]  # 3
                    self.head = node  # head 변경


    def make_statement_node(self, statements: list[ast._Statement]):
        # statement list 를 받아서 statement node list 를 반환한다.
        statement_nodes = []

        if isinstance(statements, list):
            for stmt in statements:
                if isinstance(stmt, ast.If):
                    # IF: If ( Exp ) { Stm } [ else { Stm } ]
                    statement_nodes.append(
                        BranchNode(stmt, BranchCategory.IF)
                    )
                elif isinstance(stmt, ast.While):
                    # WHILE: while ( Exp) { Stm }
                    statement_nodes.append(
                        BranchNode(stmt, BranchCategory.WHILE)
                    )
                else:
                    # OTHER
                    statement_nodes.append(
                        NormalNode(stmt)
                    )
        else:
            if isinstance(statements, ast.If):
                # IF: If ( Exp ) { Stm } [ else { Stm } ]
                statement_nodes.append(
                    BranchNode(statements, BranchCategory.IF)
                )
            elif isinstance(statements, ast.While):
                # WHILE: while ( Exp) { Stm }
                statement_nodes.append(
                    BranchNode(statements, BranchCategory.WHILE)
                )
            else:
                # OTHER
                statement_nodes.append(
                    NormalNode(statements)
                )

        return statement_nodes