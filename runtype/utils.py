import inspect

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
