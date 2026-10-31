# JapyScript Grammar Reference

This document is the normative grammar for JapyScript. It complements
`docs/SPEC.md` (which defines lexical structure) by giving the complete
syntactic production set and the operator precedence table.

Notation: EBNF. `*` means zero or more, `+` means one or more, `?` means
optional, `|` means alternative.

## Top level

```ebnf
program     ::= NEWLINE* statement* EOF
statement   ::= binding
              | expression-stmt
              | return-stmt
              | if-stmt
              | while-stmt
              | for-stmt
              | try-stmt
              | throw-stmt
              | function-def
              | class-def
              | import-stmt
```

## Statements

```ebnf
binding         ::= ( "let" | "const" | "var" ) IDENT "=" expression NEWLINE
                  | IDENT "=" expression NEWLINE

expression-stmt ::= expression NEWLINE

return-stmt     ::= "return" expression? NEWLINE

if-stmt         ::= "if" expression ":" suite
                    ( "elif" expression ":" suite )*
                    ( "else" ":" suite )?

while-stmt      ::= "while" expression ":" suite

for-stmt        ::= "for" IDENT "in" expression ":" suite

try-stmt        ::= "try" ":" suite
                    ( "except" IDENT? ":" suite )?
                    ( "finally" ":" suite )?

throw-stmt      ::= "throw" expression NEWLINE

function-def    ::= "async"? "def" IDENT "(" params? ")" ( "->" type )? ":" suite

class-def       ::= "class" IDENT ( "(" IDENT ( "," IDENT )* ")" )? ":" suite

import-stmt     ::= "import" IDENT ( "." IDENT )*
                  | "from" IDENT "import" ( IDENT | "{" IDENT ( "," IDENT )* "}" )

suite           ::= NEWLINE INDENT statement+ DEDENT
```

## Expressions

```ebnf
expression      ::= logical-or
logical-or      ::= logical-and ( ( "||" | "or" ) logical-and )*
logical-and     ::= comparison  ( ( "&&" | "and" ) comparison )*
comparison      ::= additive    ( ( "==" | "!=" | "<" | "<=" | ">" | ">=" | "is" ) additive )*
additive        ::= multiplicative ( ( "+" | "-" ) multiplicative )*
multiplicative  ::= exponent    ( ( "*" | "/" | "%" ) exponent )*
exponent        ::= unary       ( "**" unary )*
unary           ::= ( "-" | "!" | "not" | "await" ) unary | postfix
postfix         ::= primary ( "(" args? ")" | "." IDENT | "[" expression "]" )*
primary         ::= literal | IDENT | lambda | list-literal | dict-literal | "(" expression ")"

args            ::= expression ( "," expression )*
lambda          ::= "(" params? ")" "=>" expression
list-literal    ::= "[" ( expression ( "," expression )* )? "]"
dict-literal    ::= "{" ( key ":" expression ( "," key ":" expression )* )? "}"
key             ::= STRING | IDENT

literal         ::= NUMBER | STRING | "true" | "false" | "null"
```

## Operator precedence (highest to lowest)

| Level | Operators                | Associativity |
| ----- | ------------------------ | ------------- |
| 1     | `()` `[]` `.`            | left          |
| 2     | `**`                     | right         |
| 3     | `-` (unary) `!` `not` `await` | right    |
| 4     | `*` `/` `%`              | left          |
| 5     | `+` `-`                  | left          |
| 6     | `<` `<=` `>` `>=` `is`   | left          |
| 7     | `==` `!=`                | left          |
| 8     | `&&` `and`               | left          |
| 9     | `\|\|` `or`              | left          |
| 10    | `=` `+=` `-=` etc.       | right         |

## Notes

- Blocks are defined by indentation. Braces `{ ... }` may be used around a
  suite as an explicit alternative, but the indentation rule still applies.
- Statement terminators (`;`) are optional and ignored.
- A newline is significant only at nesting depth zero.
