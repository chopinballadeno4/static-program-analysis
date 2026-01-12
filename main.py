from lark import Lark, Transformer
from pathlib import Path

from ir.tip_ast import getTransformer

# /spa 디렉터리 경로
BASE_DIR = Path(__file__).resolve().parent

# /spa/syntax/tip.lark
GRAMMAR_PATH = BASE_DIR / "syntax" / "tip.lark"
grammar = GRAMMAR_PATH.read_text(encoding="utf-8")

# /spa/example/tip/example1.txt
EXAMPLE_PATH = BASE_DIR / "example" / "tip" / "example20.txt"
example = EXAMPLE_PATH.read_text(encoding="utf-8")

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
    print(transformer.transform(tree))


