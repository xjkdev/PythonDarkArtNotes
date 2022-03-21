# MRO

MRO 是 Method resolution order 的缩写，也就是方法解析顺序。

它有什么作用？我们知道 Python 支持继承，让我们看看 MRO 在继承中起了什么作用。

# 单继承
```python
class O(object):
    def foo(self):
        print("Called O.")

class A(O):
    def foo(self):
        print("Called A.")

class B(A):
    pass

class C(O):
    pass

print(A.__mro__) # output: (<class '__main__.A'>, <class '__main__.O'>, <class 'object'>)
A().foo()        # output: Called A.
print(B.__mro__) # output: (<class '__main__.B'>, <class '__main__.A'>, <class '__main__.O'>, <class 'object'>)
B().foo()        # output: Called A.
print(C.__mro__) # output: (<class '__main__.C'>, <class '__main__.O'>, <class 'object'>)
C().foo()        # output: Called O.
```
单继承中，MRO 很好地反应了继承的顺序，因此子类会调用最近的父类方法。

# 多继承
但 Python 同时支持多继承，这就有可能出现一些问题。
```
  O
 / \
A   B
 \ /
  C
```
考虑上图这样的菱形继承关系，O 被 C 间接继承了两次（一次从 A 继承，一次从 B 继承），该如何确定子类向上继承的顺序？

如果直接将 A 的 MRO 与 B 的 MRO 组合，会得到 `(C A O B O object)`。而这样，O 中的方法会覆盖 B 中的方法，这是我们不想看到的。并且 O 出现两次也是我们不想看到的。

或者考虑下面这种更复杂的情况：
```python
class O: pass

class A(O): pass

class B(O): pass

class C(O): pass

class D(O): pass

class E(O): pass

class K1(C, A, B): pass

class K3(A, D): pass

class K2(B, D, E): pass

class Z(K1, K3, K2): pass

print(K1.__mro__)
# (<class '__main__.K1'>, <class '__main__.C'>, <class '__main__.A'>, <class '__main__.B'>, <class '__main__.O'>, <class 'object'>)
print(K2.__mro__)
# (<class '__main__.K2'>, <class '__main__.B'>, <class '__main__.D'>, <class '__main__.E'>, <class '__main__.O'>, <class 'object'>)
print(K3.__mro__)
# (<class '__main__.K3'>, <class '__main__.A'>, <class '__main__.D'>, <class '__main__.O'>, <class 'object'>)
print(Z.__mro__)
# (<class '__main__.Z'>, <class '__main__.K1'>, <class '__main__.C'>, <class '__main__.K3'>, <class '__main__.A'>, <class '__main__.K2'>, <class '__main__.B'>, <class '__main__.D'>, <class '__main__.E'>, <class '__main__.O'>, <class 'object'>)
```
可以看到，MRO 以一种顺序将多继承的顺序变成了一条线性的继承顺序，保证了一个（间接）父类在这个顺序中只出现一次，并且相对继承顺序得到保留，不会出现父类的方法覆盖子类的情况。

这是因为 Python 在继承中，使用了 C3 线性化算法。

## C3 线性化

简单来说，一个好节点是当前节点之后的节点不继承或间接继承此节点。
而如果用一个列表表示继承顺序，则一个好节点只出现在所有父类的继承列表的首项，不出现在任何父类的继承列表的后面部分。

```
L(O)  := [O]                                                // the linearization of O is trivially the singleton list [O], because O has no parents

 L(A)  := [A] + merge(L(O), [O])                             // the linearization of A is A plus the merge of its parents' linearizations with the list of parents...
        = [A] + merge([O], [O])
        = [A, O]                                             // ...which simply prepends A to its single parent's linearization

 L(B)  := [B, O]                                             // linearizations of B, C, D and E are computed similar to that of A
 L(C)  := [C, O]
 L(D)  := [D, O]
 L(E)  := [E, O]

 L(K1) := [K1] + merge(L(C), L(B), L(A), [C, B, A])          // first, find the linearizations of K1's parents, L(C), L(B), and L(A), and merge them with the parent list [C, B, A]
        = [K1] + merge([C, O], [B, O], [A, O], [C, B, A])    // class C is a good candidate for the first merge step, because it only appears as the head of the first and last lists
        = [K1, C] + merge([O], [B, O], [A, O], [B, A])       // class O is not a good candidate for the next merge step, because it also appears in the tails of list 2 and 3; but class B is a good candidate
        = [K1, C, B] + merge([O], [O], [A, O], [A])          // class A is a good candidate; class O still appears in the tail of list 3
        = [K1, C, B, A] + merge([O], [O], [O])               // finally, class O is a valid candidate, which also exhausts all remaining lists
        = [K1, C, B, A, O]

 L(K3) := [K3] + merge(L(A), L(D), [A, D])
        = [K3] + merge([A, O], [D, O], [A, D])               // select A
        = [K3, A] + merge([O], [D, O], [D])                  // fail O, select D
        = [K3, A, D] + merge([O], [O])                       // select O
        = [K3, A, D, O]

 L(K2) := [K2] + merge(L(B), L(D), L(E), [B, D, E])
        = [K2] + merge([B, O], [D, O], [E, O], [B, D, E])    // select B
        = [K2, B] + merge([O], [D, O], [E, O], [D, E])       // fail O, select D
        = [K2, B, D] + merge([O], [O], [E, O], [E])          // fail O, select E
        = [K2, B, D, E] + merge([O], [O], [O])               // select O
        = [K2, B, D, E, O]

 L(Z)  := [Z] + merge(L(K1), L(K3), L(K2), [K1, K3, K2])
        = [Z] + merge([K1, C, B, A, O], [K3, A, D, O], [K2, B, D, E, O], [K1, K3, K2])    // select K1
        = [Z, K1] + merge([C, B, A, O], [K3, A, D, O], [K2, B, D, E, O], [K3, K2])        // select C
        = [Z, K1, C] + merge([B, A, O], [K3, A, D, O], [K2, B, D, E, O], [K3, K2])        // fail B, select K3
        = [Z, K1, C, K3] + merge([B, A, O], [A, D, O], [K2, B, D, E, O], [K2])            // fail B, fail A, select K2
        = [Z, K1, C, K3, K2] + merge([B, A, O], [A, D, O], [B, D, E, O])                  // select B
        = [Z, K1, C, K3, K2, B] + merge([A, O], [A, D, O], [D, E, O])                     // select A
        = [Z, K1, C, K3, K2, B, A] + merge([O], [D, O], [D, E, O])                        // fail O, select D
        = [Z, K1, C, K3, K2, B, A, D] + merge([O], [O], [E, O])                           // fail O, select E
        = [Z, K1, C, K3, K2, B, A, D, E] + merge([O], [O], [O])                           // select O
        = [Z, K1, C, K3, K2, B, A, D, E, O]                                               // done
```
