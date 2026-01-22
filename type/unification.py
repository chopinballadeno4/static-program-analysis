from typing import cast

from .tip_constraint import Type, IntType, PointerType, FunctionType, TypeVar, RecursiveType, \
    StructType, TypeEqualityConstraint, _Type, ConstraintCollector, AbsenceType

"""
* type equality relation
Reflexivity
    - r1 = r1
Symmetry
    - r1 = r2 <=> r2 = r1
Transitivity
    - r1 = r2 ∧ r2 = r3 => r1 = r3
General term equality axiom
    - ↑[x] = ↑[*y] => [x] = [*y]
    - (a) -> int = (int) -> int => a = int
    
* proper type
- integer
- pointer
- function
"""

type_parent_dict = dict()

def unification_main(constraintCollector: ConstraintCollector):
    all_make_set(constraintCollector.unique_constraints)

    for element in constraintCollector.unique_constraints:
        if not unify(element.left, element.right):
            print("type analysis failed ")

    print_parent_info()

def print_parent_info():
    print('\n[parent info]')
    for k, v in type_parent_dict.items():
        print(k, "→", v)

def all_make_set(elements: list[TypeEqualityConstraint]):
    for item in elements:
        makeSet(item.left)
        makeSet(item.right)

def is_type_variable(t: _Type):
    return not isinstance(t, (PointerType, FunctionType, IntType, StructType))

def check_type_constructor(t1: _Type, t2: _Type):
    """
    :param t1:
    :param t2:
    :return: (Boolean, _Type) = (동일 type constructor 유무, 타입 종류)

    type constructors (e.g. ↑, →)
    - ↑ (pointer type) 의 sub terms
        - ↑[type]: type
    - → (function type) 의 sub terms
        - (type1, type2) -> return type3: type1, type2, type3
    - { ... } (record type) 의 sub terms
        - {Id:Type, ... Id:Type}: Id, .. Id
    """
    if isinstance(t1, PointerType) and isinstance(t2, PointerType):
        return True, PointerType
    elif isinstance(t1, FunctionType) and isinstance(t2, FunctionType):
        # arity 가 같을 경우에 같은 constructor
        if len(t1.params) == len(t2.params):
            return True, FunctionType
        else:
            return False, FunctionType
    elif isinstance(t1, StructType) and isinstance(t2, StructType):
        # Id 가 모두 동일할 경우 같은 constructor
        if len(t1.field_map) != len(t2.field_map):
            return False, StructType

        for k1 in t1.field_map.keys():
            if k1 not in t2.field_map:
                return False, StructType

        return True, StructType
    else:
        return False, None

def makeSet(x: _Type):
    """
    procedure MakeSet(x):
        x.parent := x
    end procedure
    """
    if x not in type_parent_dict:
        type_parent_dict[x] = x

def find(x: _Type):
    """
    procedure Find(x):
        if x.parent ≠ x then
            x.parent := Find(x.parent)
        end if
        return x.parent
    end procedure
    """
    parent = type_parent_dict[x]

    if parent is not x:
        type_parent_dict[x] = find(parent)

    return type_parent_dict[x]

def union(x, y):
    """
    procedure Union(x , y):
        xr := Find(x)
        yr := Find(y)
        if xr ≠ yr then
            xr.parent := yr
        end if
    end procedure
    """
    xr = find(x)
    yr = find(y)

    if xr is not yr:
        type_parent_dict[xr] = yr

def unify(x, y):
    """
    procedure Unify(r1, r2):
        R1 = Find(r1)
        R2 = Find(r2)
        if R1 ≠ R2 then
            if R1 and R2 are both type variables then
                Union(R1, R2)
            else if R1 is a type variable and R2 is a proper type then
                Union(R1, R2)
            else if R1 is a proper type and R2 is a type variable then
                Union(R2, R1)
            else if R1 and R2 are proper types with same type constructor then
                Union(R1, R2)
                for each pair of sub-terms r`1 and r`2 of R1 and R2, respectively do
                    Unify(r`1, r`2)
                end for
            else
                unification failure
            end if
        end if
    end procedure
    """
    xr = find(x)
    yr = find(y)

    if xr is not yr:
        if is_type_variable(xr) and is_type_variable(yr):
            union(xr, yr)
        elif is_type_variable(xr) and not is_type_variable(yr):
            union(xr, yr)
        elif not is_type_variable(xr) and is_type_variable(yr):
            union(yr, xr)
        elif not is_type_variable(xr) and not is_type_variable(yr):
            # proper types
            if check_type_constructor(xr, yr)[0]:
                # same type constructor
                union(xr, yr)
                if check_type_constructor(xr, yr)[1] is PointerType:
                    unify(xr.base, yr.base)
                elif check_type_constructor(xr, yr)[1] is FunctionType:
                    for a, b in zip(xr.params, yr.params):
                        unify(a, b)
                elif check_type_constructor(xr, yr)[1] is StructType:
                    # 추후 field 목록 순회하는 것으로 리팩토링 필요
                    for k in xr.field_map:
                        xr_type = xr.field_map[k]
                        yr_type = yr.field_map[k]
                        if isinstance(xr_type, TypeVar) or isinstance(yr_type, TypeVar):
                            continue
                        elif isinstance(xr_type, AbsenceType) and not isinstance(yr_type, AbsenceType):
                            print('[ERROR] type analysis 실패')
                        elif not isinstance(xr_type, AbsenceType) and isinstance(yr_type, AbsenceType):
                            print('[ERROR] type analysis 실패')
                        else:
                            unify(xr_type, yr_type)
                else:
                    print('[ERROR] UNIFY 불가 pointer, function, struct type 모두 아님')
                    return False
            else:
                # proper types with other type constructor
                print('[ERROR] unification 실패')
                return False
        else:
            # 이럴 경우는 없음
            print('[ERROR] unification 실패')
            return False

    return True
