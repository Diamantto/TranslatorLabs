class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return self.items == []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError(f"Stack is empty: {self.items}")
        return self.items.pop()

    def __str__(self):
        return f"<Stack>: {self.items}"
