#ifndef DYNIX_NIDA_H
#define DYNIX_NIDA_H

#include "Nida_core.h"
#include "dynix.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef Dynix Nida_List;

#define NIDA_DYNIX_INT 0
#define NIDA_DYNIX_FLOAT 1
#define NIDA_DYNIX_BOOL 2
#define NIDA_DYNIX_STR 3
#define NIDA_DYNIX_PTR 4
#define NIDA_DYNIX_LIST 5

static inline Nida_List *Nida_list_new(void)
{
  return dynix_new();
}

static inline void *_Nida_box_int(int64_t value)
{
  int64_t *boxed = malloc(sizeof(*boxed));
  if (boxed != NULL)
    *boxed = value;
  return boxed;
}

static inline void *_Nida_box_float(double value)
{
  double *boxed = malloc(sizeof(*boxed));
  if (boxed != NULL)
    *boxed = value;
  return boxed;
}

static inline void *_Nida_box_bool(bool value)
{
  bool *boxed = malloc(sizeof(*boxed));
  if (boxed != NULL)
    *boxed = value;
  return boxed;
}

/* Dynix eleman verisini free() ile birakir, bu yuzden string kopyalanir. */
static inline void *_Nida_box_str(Nida_Str value)
{
  return Nida_str_new(value.data).data;
}

#define Nida_list_append(list, value)                                                                                                                                                                                                                                                                                                                                                                                                                         \
  dynix_append_generic((list), _Generic((value), bool: _Nida_box_bool, char: _Nida_box_int, signed char: _Nida_box_int, unsigned char: _Nida_box_int, short: _Nida_box_int, unsigned short: _Nida_box_int, int: _Nida_box_int, unsigned int: _Nida_box_int, long: _Nida_box_int, unsigned long: _Nida_box_int, long long: _Nida_box_int, unsigned long long: _Nida_box_int, float: _Nida_box_float, double: _Nida_box_float, Nida_Str: _Nida_box_str)(value), \
                       _Generic((value),                                                                                                                                                                                                                                                                                                                                                                                                                      \
                           char: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                              \
                           signed char: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                       \
                           unsigned char: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                     \
                           short: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                             \
                           unsigned short: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                    \
                           int: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                               \
                           unsigned int: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                      \
                           long: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                              \
                           unsigned long: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                     \
                           long long: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                         \
                           unsigned long long: NIDA_DYNIX_INT,                                                                                                                                                                                                                                                                                                                                                                                                \
                           bool: NIDA_DYNIX_BOOL,                                                                                                                                                                                                                                                                                                                                                                                                             \
                           float: NIDA_DYNIX_FLOAT,                                                                                                                                                                                                                                                                                                                                                                                                           \
                           double: NIDA_DYNIX_FLOAT,                                                                                                                                                                                                                                                                                                                                                                                                          \
                           Nida_Str: NIDA_DYNIX_STR))

static inline void *Nida_list_get(Nida_List *list, size_t index)
{
  DynixElement *element = dynix_get(list, index);

  return element == NULL ? NULL : element->data;
}

static inline size_t Nida_list_len(Nida_List *list)
{
  return list->len;
}

static inline void Nida_list_free(Nida_List *list)
{
  dynix_free(list);
}

#endif // DYNIX_NIDA_H
