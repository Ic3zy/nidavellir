class NodeIdAllocator:
    __slots__ = ("next_id",)

    def __init__(self):
        self.next_id = 0

    def alloc(self) -> int:
        node_id = self.next_id
        self.next_id += 1
        return node_id

    def name_of(self, node_id: int) -> str:
        return f"Nida_Annon_{node_id}"

    def anon(self) -> str:
        return self.name_of(self.alloc())
