# JapyScript Standard Library Reference

The standard library is organised into modules. Each module is written in
JapyScript itself and ships as a compiled `.jpc` file alongside the compiler.
Modules are namespaced with `import <module>`.

Current modules:

| Module          | Purpose                                    |
| --------------- | ------------------------------------------ |
| `string`        | Text manipulation and formatting           |
| `collections`   | Lists, maps, sets, and iteration helpers   |
| `json`          | Encode and decode JSON                     |
| `math`          | Numeric helpers                            |
| `fs`            | Filesystem access                          |
| `http`          | HTTP client and server primitives          |
| `datetime`      | Date and time types                        |
| `regex`         | Regular expressions                        |

---

## `string`

```jpy
import string

string.upper("abc")              // "ABC"
string.lower("ABC")              // "abc"
string.trim("  x  ")             // "x"
string.split("a,b,c", ",")       // ["a", "b", "c"]
string.join(["a", "b"], "-")     // "a-b"
string.starts_with("hello", "he") // true
string.contains("hello", "ell")   // true
string.replace("aaa", "a", "b")   // "bbb"
string.repeat("ab", 3)            // "ababab"
string.reverse("abc")             // "cba"
string.char_at("abc", 1)          // "b"
string.length("abc")              // 3
```

## `collections`

```jpy
import collections

collections.map([1, 2, 3], (x) => x * 2)          // [2, 4, 6]
collections.filter([1, 2, 3], (x) => x > 1)       // [2, 3]
collections.reduce([1, 2, 3], (a, b) => a + b, 0) // 6
collections.range(0, 10, 2)                        // [0, 2, 4, 6, 8]
collections.zip([1, 2], [3, 4])                    // [[1, 3], [2, 4]]
collections.flatten([[1, 2], [3, 4]])              // [1, 2, 3, 4]
collections.unique([1, 1, 2, 3, 3])                // [1, 2, 3]
collections.sort([3, 1, 2])                        // [1, 2, 3]
collections.reverse([1, 2, 3])                     // [3, 2, 1]
collections.sum([1, 2, 3])                         // 6
collections.max([1, 5, 3])                         // 5
collections.min([1, 5, 3])                         // 1
```

## `json`

```jpy
import json

json.encode({"a": 1, "b": [true, null]})    // '{"a":1,"b":[true,null]}'
json.decode('{"a":1}')                       // {"a": 1}
json.pretty({"a": 1}, 2)                     // formatted output
```

## `math`

```jpy
import math

math.abs(-5)          // 5
math.floor(3.7)       // 3
math.ceil(3.2)        // 4
math.round(3.5)       // 4
math.sqrt(16)         // 4.0
math.pow(2, 10)       // 1024
math.min(1, 2, 3)     // 1
math.max(1, 2, 3)     // 3
math.pi               // 3.141592653589793
```

## Module resolution

`import string` loads `stdlib/string.jpc` from the compiler's data directory
or from `japy_modules/` in the current project.

A project's `japy.json` declares dependencies; `jpm install` populates
`japy_modules/`. Module identity is a hash of the module's bytecode, so two
imports of the same module at any depth resolve to the same runtime object.
