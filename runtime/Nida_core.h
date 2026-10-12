#ifndef NIDA_CORE_H
#define NIDA_CORE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define NIDA_NONE_ADDR ((void *)(uintptr_t)0xDEADBEEFCAFE0000ULL)
static const void *Nida_None = NIDA_NONE_ADDR;

typedef struct
{
  char *data;
  size_t length;
} Nida_Str;

static inline Nida_Str Nida_str_new(const char *cstr)
{
  Nida_Str s;
  s.length = cstr ? strlen(cstr) : 0;
  s.data = cstr ? strdup(cstr) : NULL;
  return s;
}

static inline Nida_Str Nida_str_from_literal(const char *cstr)
{
  Nida_Str s;
  s.length = cstr ? strlen(cstr) : 0;
  s.data = (char *)cstr;
  return s;
}

static inline void Nida_str_free(Nida_Str *s)
{
  if (s && s->data && (void *)s->data != NIDA_NONE_ADDR)
  {
    free(s->data);
    s->data = NULL;
    s->length = 0;
  }
}

static inline Nida_Str Nida_str_concat(Nida_Str a, Nida_Str b)
{
  Nida_Str s;
  s.length = a.length + b.length;
  s.data = malloc(s.length + 1);
  if (s.data)
  {
    memcpy(s.data, a.data, a.length);
    memcpy(s.data + a.length, b.data, b.length);
    s.data[s.length] = '\0';
  }
  return s;
}

static inline bool Nida_str_eq(Nida_Str a, Nida_Str b)
{
  if (a.length != b.length)
    return false;
  if (a.data == b.data)
    return true;
  if (!a.data || !b.data)
    return false;
  return strcmp(a.data, b.data) == 0;
}

#endif // NIDA_CORE_H