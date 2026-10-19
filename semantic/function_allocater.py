class FunctionAllocator:
    __slots__ = ("next_id", "next_anon_id")

    def __init__(self):
        self.next_id = 0
        self.next_anon_id = 0

    def alloc(self) -> int:
        func_id = self.next_id
        self.next_id += 1
        return func_id

    def name_of(self, func_id: int) -> str:
        return f"Nida_Function_{func_id}"

    def anon(self) -> str:
        name = f"__nida_anon_{self.next_anon_id}"
        self.next_anon_id += 1
        return name
