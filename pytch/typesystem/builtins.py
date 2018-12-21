from pytch.containers import PMap, PVector
from .types import BaseTy, FunctionTy, Ty, TyVar, UniversalTy

ERR_TY = BaseTy(name="<error>")
"""Error type.

Produced when there is a typechecking error, in order to prevent cascading
failure messages.
"""


NONE_TY = BaseTy(name="None")
"""None type, corresponding to Python's `None` value."""


VOID_TY = BaseTy(name="<void>")
"""Void type.

Denotes the lack of a value. The Python runtime has no concept of "void":
functions which don't `return` anything implicitly return `None`.

However, there are some cases where it would be dangerous to allow the user
to return `None` implicitly. For example, implicitly assigning `None` to
`foo` here was probably not intended:

```
let foo =
  if cond()
  then "some value"
```
"""


INT_TY = BaseTy(name="int")
"""Integer type, corresponding to Python's `int` type."""


def _make_print() -> FunctionTy:
    quantifier_ty = TyVar(name="T")
    domain: PVector[Ty] = PVector(
        [UniversalTy(quantifier_ty=quantifier_ty, ty=quantifier_ty)]
    )
    codomain = NONE_TY
    return FunctionTy(domain=domain, codomain=codomain)


# TODO: add the Python builtins to the global scope.
GLOBAL_SCOPE: PMap[str, Ty] = PMap({"print": _make_print()})
