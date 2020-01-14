import time

from runtype import Dispatch

def add(x, y):
    "Regular version"
    return x + y

dp = Dispatch()

@dp
def dispatched_add(x: int, y: int):
    "Dispatched version"
    return x + y


# A few functions to "confuse" the dispatcher, though it will ignore them
@dp
def dispatched_add(x: str, y: str):
    raise NotImplementedError()

@dp
def dispatched_add(x: int, y: object):
    raise NotImplementedError()

@dp
def dispatched_add(x: object, y: int):
    raise NotImplementedError()



def test_add(f):
    I = J = 1000
    start = time.time()
    for i in range(I):
        for j in range(J):
            assert f(i,j) == i + j
    total = time.time() - start
    print(f"Function {f} ran {I*J} iterations in {total} seconds")
    return total

def test():
    ta = test_add(add)
    td = test_add(dispatched_add)
    print(f"Dispatch is only {(td-ta)/ta} times slower than adding two numbers!")

if __name__ == '__main__':
    test()