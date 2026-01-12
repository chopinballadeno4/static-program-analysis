# static-program-analysis

## chapter 2: A Tiny Imperative Programming Language
### 2.1 The Syntax of TIP
### 2.2 Example Programs
### 2.3 Normalization
- *exp -> *id
- exp(exp, ... exp) -> id(id, ... id)
### 2.4 Abstract Syntax Trees
- parse trees (concrete syntax trees, CTSs)
  - source code 를 lexical analysis 후 생성
  - terminal, non-terminal node 모두 존재
  - 프로그램의 문법적 구조
  - 의미 분석하기에는 너무 복잡
- abstract syntax trees (ASTs)
  - 구문 트리에서 의미만 남긴 구조
  - 컴파일러·분석기가 쓰기 위한 의미 구조
### 2.5 Control Flow Graphs

--- 
