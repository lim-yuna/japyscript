/*
 * JapyScript — C bindings.
 *
 * Public FFI surface of the JapyScript virtual machine.
 */

#ifndef JAPYSCRIPT_BINDINGS_H
#define JAPYSCRIPT_BINDINGS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define JPY_VERSION_MAJOR 0
#define JPY_VERSION_MINOR 3
#define JPY_VERSION_PATCH 0
#define JPY_VERSION_STRING "0.3.0"

typedef enum {
    JPY_OK              = 0,
    JPY_ERR_COMPILE     = 1,
    JPY_ERR_RUNTIME     = 2,
    JPY_ERR_NOT_FOUND   = 3,
    JPY_ERR_TYPE        = 4,
    JPY_ERR_IO          = 5,
    JPY_ERR_OUT_OF_MEM  = 6,
    JPY_ERR_INVALID_ARG = 7,
} jpy_status;

typedef struct jpy_context jpy_context;
typedef struct jpy_value   jpy_value;

jpy_context *jpy_context_new_from_file(const char *path);
jpy_context *jpy_context_new_from_source(const char *source, const char *name);
void jpy_context_free(jpy_context *ctx);

jpy_status jpy_invoke(jpy_context *ctx,
                      const char  *entry,
                      int          argc,
                      jpy_value  **argv,
                      jpy_value  **out);

typedef enum {
    JPY_NULL   = 0,
    JPY_BOOL   = 1,
    JPY_INT    = 2,
    JPY_FLOAT  = 3,
    JPY_STRING = 4,
    JPY_BYTES  = 5,
    JPY_LIST   = 6,
    JPY_DICT   = 7,
    JPY_FUNC   = 8,
} jpy_value_kind;

jpy_value *jpy_null(void);
jpy_value *jpy_bool(int value);
jpy_value *jpy_int(int64_t value);
jpy_value *jpy_float(double value);
jpy_value *jpy_string(const char *utf8, size_t len);
jpy_value *jpy_bytes(const uint8_t *data, size_t len);

void jpy_value_retain(jpy_value *v);
void jpy_value_release(jpy_value *v);

jpy_value_kind jpy_value_type(jpy_value *v);
int            jpy_value_as_bool(jpy_value *v);
int64_t        jpy_value_as_int(jpy_value *v);
double         jpy_value_as_float(jpy_value *v);
const char    *jpy_value_as_string(jpy_value *v, size_t *len);

const char *jpy_last_error(void);
int jpy_last_error_line(void);
int jpy_last_error_column(void);

size_t jpy_collect(jpy_context *ctx);
size_t jpy_live_objects(jpy_context *ctx);

#ifdef __cplusplus
}
#endif

#endif /* JAPYSCRIPT_BINDINGS_H */
