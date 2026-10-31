# JapyScript Language Specification

**Status:** normative for Batch 1 (lexical grammar and core syntactic forms).

---

## 1. Source files

A JapyScript source file has the extension `.jpy` and is UTF-8 encoded. Line
terminators are `\n`, `\r\n`, or `\r`.

## 2. Lexical structure

### 2.1 Whitespace and indentation

Spaces and tabs are ignored except at the start of a logical line, where they
determine block structure. Indentation is measured in leading spaces. Tabs are
expanded to four spaces before measurement.

A logical line ends at a newline that is not inside a delimiter pair `()`, `[]`,
`{}` and is not escaped by a trailing `\`.

### 2.2 Comments

Line comments begin with `//` and run to end of line.

Block comments begin with `/*` and end with `*/`. Block comments nest.

### 2.3 Identifiers

An identifier begins with a letter or `_` and continues with letters, digits,
and `_`. Unicode letters are permitted.

### 2.4 Keywords

```
def  class  return  if  elif  else  for  while  in  break  continue
try  except  finally  throw  raise  import  from  as  async  await
let  const  var  true  false  null  nullish  and  or  not  is  type
spawn  select  yield  match  case  default
```

### 2.5 Numeric literals

Integer: `[0-9][0-9_]*`, or `0x[0-9a-fA-F_]+`, `0o[0-7_]+`, `0b[01_]+`.

Float: digits with a `.` and optional exponent, or a leading `.` followed by
digits. Suffixes `f` (float32) and `d` (float64) are accepted.

### 2.6 String literals

Single- and double-quoted strings with the standard escapes
`\n \r \t \0 \\ \' \" \xHH \uHHHH`. Raw strings use the `r` prefix.

Interpolated strings use the `f` prefix. Inside an `f`-string, `{expr}` embeds
the value of `expr`.

### 2.7 Operators

```
+  -  *  /  %  **                 arithmetic
==  !=  <  <=  >  >=  is          comparison
&&  ||  !  and  or  not           logic
&  |  ^  ~  <<  >>                bitwise
=  +=  -=  *=  /=  %=  **=        assignment
?  :  ??  ?.                      ternary / nullish / optional chain
=>                                lambda arrow
.  ,  ;  :  ::  (  )  [  ]  {  }  punctuation
```

Precedence follows the published table in `docs/GRAMMAR.md` (batch 2).

## 3. Statements

- Binding: `name = expr`, `let name = expr`, `const NAME = expr`
- Expression statement
- `return [expr]`
- `if` / `elif` / `else`
- `while`
- `for name in iterable`
- `try` / `except [as name]` / `finally`
- `throw expr`
- `import` / `from`
- `class` definition
- `def` definition
- `type` alias
- `spawn` and `await`

## 4. Blocks

A block is a sequence of statements at a strictly greater indentation level
than its header. Braces `{ ... }` may wrap a block for clarity; the indentation
rule still applies inside them.

## 5. Evaluation model

Expressions are evaluated left to right. Short-circuit operators `&&` / `and`
and `||` / `or` do not evaluate the right operand when the left already
determines the result.

Binding of names is lexical. A name resolves to the nearest enclosing scope
that declares it.

## 6. Errors

Runtime errors propagate as values of type `Error`. Uncaught errors abort the
VM with a non-zero exit code and a stack trace that maps bytecode offsets back
to source locations.
