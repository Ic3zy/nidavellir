import unittest
from type_systems.types import (
    IntType,
    FloatType,
    StringType,
    BoolType,
    DynamicType,
    NoneType,
    Infinity,
    TYPE_RANK,
    get_type_rank,
)


class TestTypeSystem(unittest.TestCase):
    def test_u8_bounds(self):
        t = IntType(0, 255)
        self.assertFalse(t.signed)
        self.assertEqual(t.byte_size, 1)
        self.assertEqual(str(t), "u8")
        self.assertEqual(t.rank, 1)
        self.assertEqual(t, "u8")

    def test_i8_bounds(self):
        t = IntType(-128, 127)
        self.assertTrue(t.signed)
        self.assertEqual(t.byte_size, 1)
        self.assertEqual(str(t), "i8")
        self.assertEqual(t.rank, 2)
        self.assertEqual(t, "i8")

    def test_u16_bounds(self):
        t = IntType(0, 65535)
        self.assertFalse(t.signed)
        self.assertEqual(t.byte_size, 2)
        self.assertEqual(str(t), "u16")

    def test_i32_bounds(self):
        t = IntType(-100000, 500000)
        self.assertTrue(t.signed)
        self.assertEqual(t.byte_size, 4)
        self.assertEqual(str(t), "i32")

    def test_direct_construction(self):
        t = IntType(signed=True, byte_size=4)
        self.assertTrue(t.signed)
        self.assertEqual(t.byte_size, 4)
        self.assertEqual(str(t), "i32")

    def test_type_equality(self):
        t1 = IntType(0, 255)
        t2 = IntType(signed=False, byte_size=1)
        self.assertEqual(t1, t2)
        self.assertEqual(t1, "u8")

    def test_infinity_and_ranks(self):
        self.assertEqual(get_type_rank("u8"), 1)
        self.assertEqual(get_type_rank("f64"), 10)
        self.assertIn("Nida_Infinity", repr(Infinity()))


if __name__ == "__main__":
    unittest.main()
