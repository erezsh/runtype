import inspect
import contextvars
from contextlib import contextmanager

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
            t = typesystem.to_canonical_type(t)

        if p.default is not p.empty:
            # From now on, everything is optional
            typesigs.append(list(typesig))

        typesig.append(t)

    typesigs.append(typesig)
    return typesigs


class ContextVar:
    def __init__(self, default, name=''):
        self._var = contextvars.ContextVar(name, default=default)

    def get(self):
        return self._var.get()

    @contextmanager
    def __call__(self, value):
        token = self._var.set(value)
        try:
            yield
        finally:
            self._var.reset(token)


def limit_length(s: str, max_length: int | None) -> str:
    """Limit the length of string 's' to 'max_length' characters"""
    if max_length is None or len(s) <= max_length:
        return s
    return s[:max_length//2] + "  ... ...  " + s[-max_length//2:]