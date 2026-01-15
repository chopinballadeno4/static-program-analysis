from lark import Lark
from pathlib import Path

from ir.tip_ast import getTransformer, VariableCollector

# /spa 디렉터리 경로
BASE_DIR = Path(__file__).resolve().parent

# /spa/syntax/tip.lark
GRAMMAR_PATH = BASE_DIR / "syntax" / "tip.lark"
grammar = GRAMMAR_PATH.read_text(encoding="utf-8")

# /spa/example/type/example1.txt
EXAMPLE_PATH = BASE_DIR / "example" / "type" / "example3.txt"
text = EXAMPLE_PATH.read_text(encoding="utf-8")
example = text.split('"""', 1)[0]

# parser 생성
tip_parser = Lark(
    grammar,
    start='prog'
)

# transformer 생성
transformer = getTransformer()

if __name__ == '__main__':
    tree = tip_parser.parse(example)
    print('[CST]')
    print(tree.pretty())
    print()

    print('[AST]')
    ast = transformer.transform(tree)
    print(ast)
    print()

    print('[TYPE]')
    collector = VariableCollector("")
    collector.visit(ast)


