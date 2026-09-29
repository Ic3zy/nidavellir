TYPE_RANK = {
    "bool": 0,
    "u8": 1,
    "i8": 2,
    "u16": 3,
    "i16": 4,
    "u32": 5,
    "i32": 6,
    "u64": 7,
    "i64": 8,
    "f32": 9,
    "f64": 10,
}


def get_type_rank(target_type) -> int:
    return TYPE_RANK.get(str(target_type), -1)


class int_type(str):
    I64_MIN, I64_MAX = -9_223_372_036_854_775_808, 9_223_372_036_854_775_807
    U64_MAX = 18_446_744_073_709_551_615

    def __new__(cls, min_val: int, max_val: int):
        signed, byte_size = cls._infer_bounds(min_val, max_val)
        prefix = "i" if signed else "u"
        name = f"{prefix}{byte_size * 8}"

        obj = super().__new__(cls, name)
        obj.min_val = min_val
        obj.max_val = max_val
        obj.signed = signed
        obj.byte_size = byte_size
        return obj

    @property
    def rank(self) -> int:
        return TYPE_RANK.get(self, -1)

    @staticmethod
    def _infer_bounds(min_val: int, max_val: int):
        if min_val >= 0:
            if max_val <= 255:
                return False, 1
            if max_val <= 65_535:
                return False, 2
            if max_val <= 4_294_967_295:
                return False, 4
            if max_val <= int_type.U64_MAX:
                return False, 8
        else:
            if min_val >= -128 and max_val <= 127:
                return True, 1
            if min_val >= -32_768 and max_val <= 32_767:
                return True, 2
            if min_val >= -2_147_483_648 and max_val <= 2_147_483_647:
                return True, 4
            if min_val >= int_type.I64_MIN and max_val <= int_type.I64_MAX:
                return True, 8

        raise ValueError("Invalid number range.")


if __name__ == "__main__":
    print(int_type(0, 255))
    print(int_type(-128, 127))
    print(int_type(-32_768, 32_767).rank)
    print(int_type(-2_147_483_648, 2_147_483_647).rank)
