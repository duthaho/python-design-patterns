from typing import Iterator


class Node:
    def __init__(self, value: int, left: "Node" = None, right: "Node" = None) -> None:
        self.value = value
        self.left = left
        self.right = right


class BinaryTree:
    def __init__(self, root: Node) -> None:
        self.root = root

    def __iter__(self) -> "InOrderIterator":
        return InOrderIterator(self.root)

    def pre_order(self) -> Iterator[int]:
        return PreOrderIterator(self.root)

    def post_order(self) -> Iterator[int]:
        return PostOrderIterator(self.root)


class InOrderIterator:
    def __init__(self, root: Node) -> None:
        self.stack: list[Node] = []
        self._push_left(root)

    def _push_left(self, node: Node) -> None:
        while node:
            self.stack.append(node)
            node = node.left

    def __next__(self) -> int:
        if not self.stack:
            raise StopIteration
        node = self.stack.pop()
        value = node.value
        if node.right:
            self._push_left(node.right)
        return value

    def __iter__(self) -> "InOrderIterator":
        return self


class PreOrderIterator:
    def __init__(self, root: Node) -> None:
        self.stack: list[Node] = []
        if root:
            self.stack.append(root)

    def __next__(self) -> int:
        if not self.stack:
            raise StopIteration
        node = self.stack.pop()
        value = node.value
        if node.right:
            self.stack.append(node.right)
        if node.left:
            self.stack.append(node.left)
        return value

    def __iter__(self) -> "PreOrderIterator":
        return self


class PostOrderIterator:
    def __init__(self, root: Node) -> None:
        self.stack1: list[Node] = []
        self.stack2: list[Node] = []
        if root:
            self.stack1.append(root)
            while self.stack1:
                node = self.stack1.pop()
                self.stack2.append(node)
                if node.left:
                    self.stack1.append(node.left)
                if node.right:
                    self.stack1.append(node.right)

    def __next__(self) -> int:
        if not self.stack2:
            raise StopIteration
        node = self.stack2.pop()
        return node.value

    def __iter__(self) -> "PostOrderIterator":
        return self


def client_code(tree: BinaryTree) -> None:
    print("In-order traversal:")
    for value in tree:
        print(value, end=" ")
    print("\nPre-order traversal:")
    for value in tree.pre_order():
        print(value, end=" ")
    print("\nPost-order traversal:")
    for value in tree.post_order():
        print(value, end=" ")
    print()


if __name__ == "__main__":
    # Construct the binary tree
    #         1
    #        / \
    #       2   3
    #      / \   \
    #     4   5   6
    root = Node(1)
    root.left = Node(2, Node(4), Node(5))
    root.right = Node(3, None, Node(6))

    tree = BinaryTree(root)
    client_code(tree)
