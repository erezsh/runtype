from runtype import multidispatch, multidispatch_final

@multidispatch
def f(a: int):
    pass

@multidispatch
def f(a: str):
    pass

@multidispatch_final
def f(a):
    pass


f(4)