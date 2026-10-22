#pragma once
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

#define DYNIX_START_CHUNK_SIZE 256
#define DYNIX_CHUNK_SHIFT __builtin_ctzll(DYNIX_START_CHUNK_SIZE)
#define DYNIX_CHUNK_MASK (DYNIX_START_CHUNK_SIZE - 1)

typedef struct
{
  void *data;
  size_t type;
} DynixElement;

typedef struct
{
  void **data;
  size_t len;
} DynixChunk;

typedef struct
{
  DynixChunk chunks[64];
  size_t capacity;
  size_t len;
  bool is_raw;
} Dynix;

//
//
//
// Helpers
typedef struct
{
  size_t chunk;
  size_t offset;
} DynixIndex;

DynixIndex dynix_get_chunk_index(size_t index)
{
  if (index == 0)
    return (DynixIndex){
        .chunk = 0,
        .offset = 0};

  size_t x = (index >> DYNIX_CHUNK_SHIFT) + 1;
  size_t chunk = 63 - __builtin_clzll(x);
  size_t start = DYNIX_START_CHUNK_SIZE * ((1ULL << chunk) - 1);

  return (DynixIndex){
      .chunk = chunk,
      .offset = index - start};
}

//
//
//
// Creator
Dynix *dynix_new()
{
  Dynix *dynix = calloc(1, sizeof(Dynix));

  dynix->chunks[0].data = calloc(DYNIX_START_CHUNK_SIZE, sizeof(void *));
  dynix->capacity = DYNIX_START_CHUNK_SIZE;

  dynix->len = 0;
  dynix->is_raw = false;

  return dynix;
}

Dynix *dynix_new_raw()
{
  Dynix *dynix = calloc(1, sizeof(Dynix));

  dynix->chunks[0].data = calloc(DYNIX_START_CHUNK_SIZE, sizeof(void *));
  dynix->capacity = DYNIX_START_CHUNK_SIZE;

  dynix->len = 0;
  dynix->is_raw = true;

  return dynix;
}

//
//
//
// Appender
void dynix_append_raw(Dynix *dynix, void *data)
{
  if (__builtin_expect(!dynix->is_raw, false))
  {
    fprintf(stderr, "dynix_append_raw: dynix is not raw\n");
    abort();
    return;
  }

  DynixIndex index = dynix_get_chunk_index(dynix->len);

  if (__builtin_expect((dynix->len >= dynix->capacity), false))
  {
    size_t chunk_size = DYNIX_START_CHUNK_SIZE << index.chunk;
    dynix->capacity += chunk_size;

    dynix->chunks[index.chunk].data = calloc(chunk_size, sizeof(void *));
  }
  dynix->chunks[index.chunk].data[index.offset] = data;
  dynix->len++;
}

void dynix_append_generic(Dynix *dynix, void *data, size_t type)
{
  if (__builtin_expect(dynix->is_raw, false))
  {
    fprintf(stderr, "dynix_append_raw: dynix is raw\n");
    abort();
    return;
  }

  DynixIndex index = dynix_get_chunk_index(dynix->len);

  if (__builtin_expect((dynix->len >= dynix->capacity), false))
  {
    size_t chunk_size = DYNIX_START_CHUNK_SIZE << index.chunk;
    dynix->capacity += chunk_size;
    dynix->chunks[index.chunk].data = calloc(chunk_size, sizeof(void *));
  }

  DynixElement *element = calloc(1, sizeof(DynixElement));
  element->data = data;
  element->type = type;

  dynix->chunks[index.chunk].data[index.offset] = element;
  dynix->len++;
}

//
//
//
// Getter
void *dynix_get(Dynix *dynix, size_t index)
{
  if (__builtin_expect(index >= dynix->len, false))
  {
    fprintf(stderr, "dynix_get: index out of range\n");
    return NULL;
  }

  DynixIndex dyn_index = dynix_get_chunk_index(index);

  return dynix->chunks[dyn_index.chunk].data[dyn_index.offset];
}

//
//
//
// Search
// o(n)
bool dynix_exists(Dynix *dynix, void *data)
{
  if (dynix->is_raw)
  {
    // raw search
    for (size_t i = 0; i < dynix->len; i++)
    {
      DynixIndex index = dynix_get_chunk_index(i);
      void *dyn_data = dynix->chunks[index.chunk].data[index.offset];

      if (dyn_data == data)
        return true;
    }
  }
  else
  {
    // generic search
    for (size_t i = 0; i < dynix->len; i++)
    {
      DynixIndex index = dynix_get_chunk_index(i);
      DynixElement *element = dynix->chunks[index.chunk].data[index.offset];

      if (element->data == data)
        return true;
    }
  }
  return false;
}

//
//
//
//
// Removers
// o(n)
void dynix_remove(Dynix *dynix, size_t index)
{
  if (__builtin_expect(index >= dynix->len, false))
  {
    fprintf(stderr, "dynix_remove: index out of range\n");
    return;
  }
  for (size_t i = index; i < dynix->len - 1; i++)
  {
    DynixIndex source_index = dynix_get_chunk_index(i + 1);
    DynixIndex target_index = dynix_get_chunk_index(i);

    dynix->chunks[target_index.chunk].data[target_index.offset] =
        dynix->chunks[source_index.chunk].data[source_index.offset];
  }
  dynix->len -= 1;
}

void dynix_delete(Dynix *dynix, size_t index)
{
  void *data = dynix_get(dynix, index);
  dynix_remove(dynix, index);
  free(data);
}

void *dynix_pop(Dynix *dynix, size_t index)
{
  void *data = dynix_get(dynix, index);
  dynix_remove(dynix, index);
  return data;
}

//
//
//
// Free
void dynix_free(Dynix *dynix)
{
  bool is_raw = dynix->is_raw;
  size_t last_freed_chunk = 0;
  for (size_t i = 0; i < dynix->len; i++)
  {
    DynixIndex index = dynix_get_chunk_index(i);
    if (is_raw)
      free(dynix->chunks[index.chunk].data[index.offset]);

    else
    {
      DynixElement *element = dynix->chunks[index.chunk].data[index.offset];
      free(element->data);
      free(element);
    }
    if (index.chunk != last_freed_chunk)
    {
      free(dynix->chunks[index.chunk].data);
      last_freed_chunk = index.chunk;
    }
  }

  free(dynix);
}

// this method does not free the data, but only the DynixElement struct
void dynix_soft_free(Dynix *dynix)
{
  bool is_raw = dynix->is_raw;

  if (!is_raw)
  {
    size_t last_freed_chunk = 0;
    for (size_t i = 0; i < dynix->len; i++)
    {
      DynixIndex index = dynix_get_chunk_index(i);

      DynixElement *element = dynix->chunks[index.chunk].data[index.offset];
      free(element);
      if (index.chunk != last_freed_chunk)
      {
        free(dynix->chunks[index.chunk].data);
        last_freed_chunk = index.chunk;
      }
    }
  }
  free(dynix);
}

void dynix_safe_free(Dynix *dynix)
{
  bool is_raw = dynix->is_raw;
  Dynix *freed_ptrs = dynix_new_raw();
  size_t last_freed_chunk = 0;

  for (size_t i = 0; i < dynix->len; i++)
  {
    DynixIndex index = dynix_get_chunk_index(i);
    if (is_raw)
    {
      void *ptr = dynix->chunks[index.chunk].data[index.offset];
      if (dynix_exists(freed_ptrs, ptr))
        continue;

      dynix_append_raw(freed_ptrs, ptr);
    }
    else
    {
      DynixElement *element = dynix->chunks[index.chunk].data[index.offset];
      void *ptr = element->data;
      if (!dynix_exists(freed_ptrs, ptr))
      {
        free(element->data);
        dynix_append_raw(freed_ptrs, ptr);
      }
      free(element);
    }

    if (index.chunk != last_freed_chunk)
    {
      free(dynix->chunks[index.chunk].data);
      last_freed_chunk = index.chunk;
    }
  }
  dynix_soft_free(freed_ptrs);
  free(dynix);
}
