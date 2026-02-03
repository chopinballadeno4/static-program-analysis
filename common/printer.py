def print_constraints(constraints):
    print('[constraints]')
    for c in constraints:
        print(f" - {str(c)}")


def print_type_parent_relation(type_parent_relation):
    print('\n[type parent relation]')
    for k, v in type_parent_relation.items():
        print(f" - {k} → {v}")

def print_cfg(entry_node):
    print('\n[Control Flow Graph]')
    visited = set()
    node_ids = {}
    node_counter = [0]

    def get_node_id(node):
        if node is None:
            return "None"
        if id(node) not in node_ids:
            node_ids[id(node)] = node_counter[0]
            node_counter[0] += 1
        return node_ids[id(node)]

    def get_node_label(node):
        class_name = node.__class__.__name__
        if class_name == 'Entry':
            return "Entry"
        elif class_name == 'Exit':
            return "Exit"
        elif class_name == 'BranchNode':
            category = "IF" if node.category.name == 'IF' else "WHILE"
            return f"{category}: {node.statement.condition}"
        elif class_name == 'NormalNode':
            return str(node.statement)
        else:
            return "Unknown"

    def traverse(node):
        if node is None or id(node) in visited:
            return
        visited.add(id(node))

        node_id = get_node_id(node)
        label = get_node_label(node)
        class_name = node.__class__.__name__

        if class_name == 'Entry':
            succ_id = get_node_id(node.successor)
            print(f"  [{node_id}] {label}")
            print(f"       └→ successor: [{succ_id}]")
            traverse(node.successor)

        elif class_name == 'Exit':
            pred_ids = [get_node_id(p) for p in node.predecessors]
            print(f"  [{node_id}] {label}")
            print(f"       └← predecessors: {pred_ids}")

        elif class_name == 'BranchNode':
            true_id = get_node_id(node.true_successor)
            false_id = get_node_id(node.false_successor)
            pred_ids = [get_node_id(p) for p in node.predecessors]
            print(f"  [{node_id}] {label}")
            print(f"       ├← predecessors: {pred_ids}")
            print(f"       ├→ true_successor: [{true_id}]")
            print(f"       └→ false_successor: [{false_id}]")
            traverse(node.true_successor)
            traverse(node.false_successor)

        elif class_name == 'NormalNode':
            succ_id = get_node_id(node.successor)
            pred_ids = [get_node_id(p) for p in node.predecessors]
            print(f"  [{node_id}] {label}")
            print(f"       ├← predecessors: {pred_ids}")
            print(f"       └→ successor: [{succ_id}]")
            traverse(node.successor)

    traverse(entry_node)