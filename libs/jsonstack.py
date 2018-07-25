from jsonmerge import merge

class JSONStack:
    """Stack of JSON object that merge with each push"""
    def __init__(self):
        self.stack = []

    def push(self, object):
        base = self.top() if not self.empty() else {}
        merged = merge(base, object)
        self.stack.append(merged)

    def pop(self):
        self.stack.pop()

    def top(self):
        return self.stack[-1]

    def count(self):
        return len(self.stack)

    def empty(self):
        return len(self.stack) == 0

    # stack = JSONStack()
    # stack.push({ "foo": "foo", "bar": "bar" })
    # print stack.top()
    # stack.push({ "bar": "barbar", "baz": "baz" })
    # print stack.top()
    # stack.pop()
    # print stack.top()
