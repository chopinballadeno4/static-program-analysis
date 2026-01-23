"""
Reflexivity
    - r1 = r1
Symmetry
    - r1 = r2 <=> r2 = r1
Transitivity
    - r1 = r2 ∧ r2 = r3 => r1 = r3
General term equality axiom
    - ↑[x] = ↑[*y] => [x] = [*y]
    - (a) -> int = (int) -> int => a = int
"""
from dataclasses import dataclass, field
from common.exceptions import TypeAnalysisException
from . import tip_constraint as constraint

@dataclass
class UnificationSolver:
    target_constraints: list[constraint.TypeEqualityConstraint]

    type_parent_relation: dict = field(init=False, default_factory=dict)
    unique_constraints: list[constraint.TypeEqualityConstraint] = field(init=False, default_factory=list)

    def __post_init__(self):
        # constraint 중 중복 제거
        self.set_unique_constraints()
        self.all_make_set(self.unique_constraints)

        for element in self.unique_constraints:
            self.unify(element.left, element.right)

    def set_unique_constraints(self):
        if len(self.target_constraints) > 0:
            self.unique_constraints = []
            for c in self.target_constraints:
                if c not in self.unique_constraints:
                    self.unique_constraints.append(c)

    def is_type_variable(self, t: constraint._Type):
        """

        :param t:
        :return:
        """
        return not isinstance(t, (constraint.PointerType, constraint.FunctionType, constraint.IntType, constraint.StructType))

    def check_type_constructor(self, t1: constraint._Type, t2: constraint._Type):
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
        if isinstance(t1, constraint.PointerType) and isinstance(t2, constraint.PointerType):
            return True, constraint.PointerType
        elif isinstance(t1, constraint.FunctionType) and isinstance(t2, constraint.FunctionType):
            # arity 가 같을 경우에 같은 constructor
            if len(t1.params) == len(t2.params):
                return True, constraint.FunctionType
            else:
                return False, constraint.FunctionType
        elif isinstance(t1, constraint.StructType) and isinstance(t2, constraint.StructType):
            # Id 가 모두 동일할 경우 같은 constructor
            if len(t1.field_map) != len(t2.field_map):
                return False, constraint.StructType

            for k1 in t1.field_map.keys():
                if k1 not in t2.field_map:
                    return False, constraint.StructType

            return True, constraint.StructType
        else:
            raise TypeAnalysisException("hihi")

    def all_make_set(self, elements: list[constraint.TypeEqualityConstraint]):
        for item in elements:
            self.makeSet(item.left)
            self.makeSet(item.right)

    def makeSet(self, x: constraint._Type):
        """
        procedure MakeSet(x):
            x.parent := x
        end procedure
        """
        if x not in self.type_parent_relation:
            self.type_parent_relation[x] = x

    def find(self, x: constraint._Type):
        """
        procedure Find(x):
            if x.parent ≠ x then
                x.parent := Find(x.parent)
            end if
            return x.parent
        end procedure
        """
        parent = self.type_parent_relation[x]

        if parent is not x:
            self.type_parent_relation[x] = self.find(parent)

        return self.type_parent_relation[x]

    def union(self, x, y):
        """
        procedure Union(x , y):
            xr := Find(x)
            yr := Find(y)
            if xr ≠ yr then
                xr.parent := yr
            end if
        end procedure
        """
        xr = self.find(x)
        yr = self.find(y)

        if xr is not yr:
            self.type_parent_relation[xr] = yr

    def unify(self, x, y):
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
        xr = self.find(x)
        yr = self.find(y)

        if xr is not yr:
            if self.is_type_variable(xr) and self.is_type_variable(yr):
                self.union(xr, yr)
            elif self.is_type_variable(xr) and not self.is_type_variable(yr):
                self.union(xr, yr)
            elif not self.is_type_variable(xr) and self.is_type_variable(yr):
                self.union(yr, xr)
            elif not self.is_type_variable(xr) and not self.is_type_variable(yr):
                if self.check_type_constructor(xr, yr)[0]:
                    # proper types same type constructor
                    self.union(xr, yr)

                    if self.check_type_constructor(xr, yr)[1] is constraint.PointerType:
                        self.unify(xr.base, yr.base)
                    elif self.check_type_constructor(xr, yr)[1] is constraint.FunctionType:
                        for a, b in zip(xr.params, yr.params):
                            self.unify(a, b)
                    elif self.check_type_constructor(xr, yr)[1] is constraint.StructType:
                        # 추후 field 목록 순회하는 것으로 리팩토링 필요
                        for k in xr.field_map:
                            xr_type = xr.field_map[k]
                            yr_type = yr.field_map[k]
                            if isinstance(xr_type, constraint.TypeVar) or isinstance(yr_type, constraint.TypeVar):
                                continue
                            elif (isinstance(xr_type, constraint.AbsenceType) and not isinstance(yr_type, constraint.AbsenceType))\
                                    or (not isinstance(xr_type, constraint.AbsenceType) and isinstance(yr_type, constraint.AbsenceType)):
                                raise TypeAnalysisException("unification 실패")
                            else:
                                self.unify(xr_type, yr_type)
                else:
                    # proper types with other type constructor
                    raise TypeAnalysisException("unification 실패")
                    #return False

        return True