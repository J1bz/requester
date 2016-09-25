# -*- coding: utf-8 -*-

# --------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2016 Jonathan Labéjof <jonathan.labejof@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# --------------------------------------------------------------------

"""Expression module."""

from __future__ import division

__all__ = ['Expression', 'FuncName', 'Function', 'MetaExpression']

from six import add_metaclass, string_types, PY3

from numbers import Number

from enum import Enum, unique

from .base import BaseElement


@unique
class FuncName(Enum):
    """Default function names which might be supported by drivers."""

    AND = '&'
    OR = '|'
    EQ = '=='
    NE = '!='
    GT = '>'
    GE = '>='
    LT = '<'
    LE = '<='
    ADD = '+'
    SUB = '-'
    DIV = '/'
    MUL = '*'
    POW = '**'
    LIKE = '%'
    NEG = 'neg'
    ABS = 'abs'
    INVERT = '~'
    EXISTS = 'exists'
    GETSLICE = 'getslice'
    SETSLICE = 'setslice'
    DELSLICE = 'delslice'

    # remainders functions are not supported by the Expression methods
    ISNULL = 'isnull'
    BETWEEN = 'between'
    IN = 'in'

    # selection operators  TODO: might be migrated to the Read object...
    HAVING = 'having'
    UNION = 'union'
    INTERSECT = 'intersect'

    # request comparison
    ALL = 'all'
    ANY = 'any'
    SOME = 'some'

    # DB operations
    OPTIMIZE = 'optimize'
    VERSION = 'version'

    # aggregation operations
    AVG = 'avg'
    COUNT = 'count'
    MEAN = 'mean'
    MAX = 'max'
    MIN = 'min'
    SUM = 'sum'

    # string operations
    CONCAT = 'concat'
    LENGTH = 'length'
    REPLACE = 'replace'
    SOUNDEX = 'soundex'
    SUBSTRING = 'substring'
    LEFT = 'left'
    RIGHT = 'right'
    REVERSE = 'reverse'
    TRIM = 'trim'
    LTRIM = 'ltrim'
    RTRIM = 'rtrim'
    LPAD = 'lpad'
    UPPER = 'upper'
    LOWER = 'lower'
    UCASE = 'ucase'
    LCASE = 'lcase'
    LOCATE = 'locate'
    INSTR = 'instr'

    # mathematical operations
    RAND = 'rand'
    ROUND = 'round'
    MD5 = 'md5'

    # datetime operations
    NOW = 'now'
    SEC_TO_TIME = 'sec_to_time'
    DATEDIFF = 'datediff'
    MONTH = 'month'
    YEAR = 'year'

    # additional operations
    CAST = 'cast'
    CONVERT = 'convert'
    GROUPCONCAT = 'groupconcat'

    @staticmethod
    def contains(value):

        result = False

        for member in FuncName.__members__.values():
            if member.value == value:
                result = True
                break

        return result


class MetaExpression(type):
    """Meta class for function."""

    def __getattr__(cls, key):
        """Instanciate a new cls expression for not existing attribute."""

        return cls(key)


@add_metaclass(MetaExpression)
class Expression(BaseElement):
    """An expression is a reference to a data set.

    It has a name which is interpreted by drivers.

    Examples:

    - Expression('wheel'): expression named 'wheel'.
    - Expression('car.wheel'): expression 'wheel' from expression 'car'.
    - Expression('wheel', alias='wh'): expression aliased 'wh'.
    """

    __slots__ = ['name'] + BaseElement.__slots__

    def __init__(self, name, *args, **kwargs):
        """
        :param str name: model name.
        """

        super(Expression, self).__init__(*args, **kwargs)

        self.name = name

    def __getattr__(self, key):

        return type(self)('{0}.{1}'.format(self.name, key))

    def __and__(self, other):

        return Function(FuncName.AND)(self, other)

    def __or__(self, other):

        return Function(FuncName.OR)(self, other)

    def _checktype(self, other, *types):

        if not isinstance(other, types + (Expression,)):
            raise TypeError(
                'Wrong type {0}. {1}, Expression expected.'.format(other, types)
            )

    def __mod__(self, other):
        """Regex comparison operator."""

        self._checktype(other, string_types)

        return Function(FuncName.LIKE)(self, other)

    def __gt__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.GT)(self, other)

    def __ge__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.GE)(self, other)

    def __lt__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.LT)(self, other)

    def __le__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.LE)(self, other)

    def __eq__(self, other):

        return Function(FuncName.EQ)(self, other)

    def __ne__(self, other):

        return Function(FuncName.NE)(self, other)

    def __add__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.ADD)(self, other)

    def __sub__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.SUB)(self, other)

    def __mul__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.MUL)(self, other)

    def __div__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.DIV)(self, other)

    def __truediv__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.DIV)(self, other)

    def __invert__(self):

        return Function(FuncName.INVERT)(self)

    def __neg__(self):

        return Function(FuncName.NEG)(self)

    def __abs__(self):

        return Function(FuncName.ABS)(self)

    def __pow__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.POW)(self, other)

    def __radd__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.ADD)(other, self)

    def __rsub__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.SUB)(other, self)

    def __rmul__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.MUL)(other, self)

    def __rdiv__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.DIV)(other, self)

    def __rtruediv__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.DIV)(other, self)

    def __rmod__(self, other):

        self._checktype(other, string_types)

        return Function(FuncName.LIKE)(other, self)

    def __rpow__(self, other):

        self._checktype(other, Number)

        return Function(FuncName.POW)(other, self)

    def __getitem__(self, key):

        if isinstance(key, slice):
            return self.__getslice__(key.start, key.stop, key.step)

        return self.__getattr__(key)

    def __getslice__(self, start, stop, step):

        if start is not None:
            self._checktype(start, Number)

        if stop is not None:
            self._checktype(stop, Number)

        return Function(FuncName.GETSLICE)(self, start, stop, step)

    def __setslice__(self, start, stop, value):

        if start is not None:
            self._checktype(start, Number)

        if stop is not None:
            self._checktype(stop, Number)

        self._checktype(value, list, tuple)

        return Function(FuncName.SETSLICE)(self, start, stop, value)

    def __delslice__(self, start, step):

        if start is not None:
            self._checktype(start, Number)

        if step is not None:
            self._checktype(step, Number)

        return Function(FuncName.DELSLICE)(self, start, step)

    def copy(self, **kwargs):
        """Copy this expression with input kwargs.

        :param dict kwargs: parameters to set in the copy.
        :rtype: self"""

        cls = type(self)

        ckwargs = {}

        for slot in cls.__slots__:
            value = getattr(self, slot)

            if value is not None:

                fvalue = value

                if isinstance(value, Expression):
                    fvalue = value.copy()

                elif isinstance(value, list):

                    fvalue = [
                        item.copy() if isinstance(item, Expression) else item
                    ]

                kwargs[slot] = fvalue

        ckwargs.update(kwargs)

        result = cls(**ckwargs)

        return result

    def __repr__(self):

        return '{0}[{1}]{2}'.format(
            type(self).__name__, self.name,
            ':{0}'.format(self.alias) if self.alias else ''
        )


class Function(Expression):
    """A function is an expression with parameters called 'params'.

    The property 'isfunc' permits to inform if this model is a function or
    not.

    Examples:

    - func = Function('count') => function 'count'.
    - func = Expression('A') < 2 => Function('<')(Expression('A'), 2).
    - func = Function('A', params=[2]) => function A and param equal 2.
    - func = Function('A')(2, 3) => function A from S1 and params 2 and 3.
    """

    def __init__(self, name, params=None, *args, **kwargs):
        """
        :param list params: model params in case of function.
        """

        name = name.value if isinstance(name, FuncName) else name

        super(Function, self).__init__(name=name, *args, **kwargs)

        self.params = params or []

    def __call__(self, *params):
        """Transform this model into a function with parameters.

        If self is OR or AND function

        :param list params: parameters to use."""

        self.params = list(params)

        return self

    def optimize(self):
        """Aggregate AND/OR functions.

        Examples:

        - AND(AND(A, B), C) => AND(A, B, C)
        - OR(OR(A, B), C) => OR(A, B, C)

        :rtype: Function
        :return: this."""

        params = []

        if self.name in (FuncName.AND.value, FuncName.OR.value):

            for param in self.params:

                if isinstance(param, Function):
                    function = param.optimize()

                    if function.name == self.name:
                        params += function.params

                    else:
                        params.append(function)

                else:
                    params.append(param)

        self.params = params

        return self

    def __repr__(self):

        result = super(Function, self).__repr__()

        result += '('

        for param in self.params:

            rparam = repr(param)

            result += '{0},'.format(rparam)

        result += ')'

        return result
