def print_constraints(constraints):
    print('[constraints]')
    for c in constraints:
        print(f" - {str(c)}")


def print_type_parent_relation(type_parent_relation):
    print('\n[type parent relation]')
    for k, v in type_parent_relation.items():
        print(f" - {k} → {v}")