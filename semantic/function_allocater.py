class FunctionAllocator:
    __slots__ = ("next_id",)

    def __init__(self):
        self.next_id = 0

    def alloc(self) -> str:
        func_id = self.next_id
        self.next_id += 1
        return f"Nida_Function_{func_id}"
