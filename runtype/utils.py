import inspect
import sys

if sys.version_info < (3, 7):
    # python 3.6 
    from typing import _ForwardRef as ForwardRef
    _orig_eval = ForwardRef._eval_type
elif sys.version_info < (3, 9):
    from typing import ForwardRef
    _orig_eval = ForwardRef._evaluate
else:
    from typing import ForwardRef

if sys.version_info < (3, 9):
    def _evaluate(self, g, l, _):
        return _orig_eval(self, g, l)
    ForwardRef._evaluate = _evaluate



def get_func_signatures(typesystem, f):
    sig = inspect.signature(f)
    typesigs = []
    typesig = []
    for p in sig.parameters.values():
        # if p.kind is p.VAR_KEYWORD or p.kind is p.VAR_POSITIONAL:
        #     raise TypeError("Dispatch doesn't support *args or **kwargs yet")

        t = p.annotation
        if t is sig.empty:
            t = typesystem.default_type
        else:
            # Canonize to detect more collisions on construction, instead of during dispatch
            t = typesystem.canonize_type(t)

        if p.default is not p.empty:
            # From now on, everything is optional
            typesigs.append(list(typesig))

        typesig.append(t)

    typesigs.append(typesig)
    return typesigs
