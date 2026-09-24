#include "../printer.h"

int main()
{
  _Nida_print_a4(15, "test", true, "🚀", false);
  _Nida_print_a4("a", "b", "c", "d", false, true);
  _Nida_print_a2("e", "f", true, false);

  return 0;
}