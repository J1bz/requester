# -*- coding: utf-8 -*-

# --------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2016 Jonathan Labéjof <jonathan.labejof@gmail.com>
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

"""Module which specifices a composite of drivers."""

from inspect import getmembers

from b3j0f.schema import Schema, data2schema

from six import iteritems

from .base import Driver
from .utils import getnames
from .ctx import Context
from ..request.consts import FuncName
from ..request.base import BaseElement
from ..request.crud.base import CRUDElement
from ..request.crud.create import Create
from ..request.crud.delete import Delete
from ..request.crud.read import Read
from ..request.crud.update import Update
from ..request.expr import Expression, Function

__all__ = ['DriverComposite']


class DriverComposite(Driver):
    """In charge of distributing a request to several drivers.

    Driver parameters are :

    .. csv-table::

        :header: name, type, description

        - discovery, bool (False), enable driver discovery from queries.
        - many, bool (False), disable multi driver execution for one query.
        - besteffort, bool (False), enable discovery and many.
        - maxdepth, int (3), max depth data search in the driver tree.
        - explain, bool (False), return query information processsing in ctx.
    """

    def __init__(self, drivers, ddriver=None, *args, **kwargs):
        """
        :param list drivers: drivers to use.
        :param Driver ddriver: default driver to use if no driver found.
        """
        super(DriverComposite, self).__init__(*args, **kwargs)

        self.drivers = {}

        for driver in drivers:
            if not isinstance(driver, Schema):
                driver = data2schema(driver, name=driver.name, _force=True)

            self.drivers[driver.name] = driver

        self.ddriver = ddriver

    def getdrivers(self, name, maxdepth=3, discovery=False, many=False):
        """Get a list of drivers corresponding with input model name.

        :param str name: data name to identify such as a driver model.
        :param bool discovery: if True (False by default), try to find drivers
            where name match with driver models.
        :param bool many: if False (default), raise a ValueError if more than
            one driver is found.
        :return: list of couples of driver with model where name match a
            driver/model name.
        :rtype: list
        :raises: ValueError if name is not a standard query name and no driver
            is found.
        """
        result = []

        if name in self.supportedfunctions:
            return result

        names = getnames(name)

        rootname = names[0]

        if discovery:

            tmpelts = []  # list of couple of driver/model.
            elts = []  # list of couple of driver/model.

            for depth in range(maxdepth + 1):

                if elts:
                    tmpelts = []
                    for driver, model in list(elts):
                        if hasattr(model, rootname):
                            tmpelts.append((driver, getattr(model, rootname)))

                        elif isinstance(model, Schema):
                            for mname, submodel in iteritems(
                                model.getschemas()
                            ):
                                tmpelts.append((driver, submodel))

                        else:
                            for name, member in getmembers(model):
                                if name[0] != '_':
                                    tmpelts.append((driver, member))

                    elts = tmpelts

                else:
                    if rootname in self.drivers:
                        result = [self.drivers[rootname]]
                        break

                    elif self.ddriver and self.ddriver.name == rootname:
                        result = [self.ddriver]

                    else:
                        elts = [(item, item) for item in self.drivers.values()]
                        if self.ddriver:
                            elts.append((self.ddriver, self.ddriver))

            if not result:
                if elts:
                    for name in names[1:]:

                        elts = [
                            (elt[0], getattr(elt[1], name)) for elt in elts
                            if hasattr(elt[1], name)
                        ]
                        if not elts:
                            break

                    else:
                        result = elts

        else:
            if rootname in self.drivers:
                result = [self.drivers[rootname]]

            elif self.ddriver is not None and self.ddriver.name == rootname:
                result = [self.ddriver]

            else:
                raise ValueError(
                    '{0} is not handled by {1}'.format(name, self)
                )

        if result:
            if many and len(result) > 1:
                raise ValueError(
                    'Too many drivers found for elt {0}: {1}.'.format(
                        elt, result
                    )
                )

        else:
            raise ValueError('No driver found for processing {0}'.format(name))

        return result

    def _process(self, transaction, **kwargs):

        for crud in transaction.cruds:
            self.processdeeply(elt=crud, transaction=transaction, **kwargs)

        return transaction

    def processdeeply(self, elt, transaction, _elts=None, **kwargs):
        """Parse input elt and return its evaluation."""
        result = elt

        # process specific driver parameters
        discovery = kwargs.get('discovery', False)
        many = kwargs.get('many', False)
        besteffort = kwargs.get('besteffort')
        maxdepth = kwargs.get('maxdepth', 3)

        if besteffort is not None:
            many = discovery = besteffort

        ctx = transaction.ctx

        if elt in ctx:
            result = ctx[elt]

        elif isinstance(elt, BaseElement):
            # get driver and model

            # ddriver case, elt is a crudelement or elt is a standard query
            if isinstance(elt, CRUDElement):
                drivers = []

            else:
                drivers = self.getdrivers(
                    name=elt.name, maxdepth=maxdepth, discovery=discovery,
                    many=many
                )

            # fill elts
            if _elts is None:
                _elts = [[drivers, elt]]

            elif drivers:
                olddrivers = _elts[-1][0]

                if olddrivers is None:
                    _elts[-1][0] = drivers

                elif olddrivers != drivers:
                        _elts.append([drivers, elt])

            children = getchildren(elt)

            isor = isinstance(elt, Function) and elt.name == FuncName.OR.value

            for child in children:

                if isor:
                    ctx = Context(transaction.ctx)
                    ftransaction = transaction.open(ctx=ctx)

                else:
                    ftransaction == transaction

                self.processdeeply(
                    elt=child, transaction=ftransaction, _elts=_elts, **kwargs
                )

                if isor:
                    transaction.ctx.fill(ftransaction.ctx)

            if _elts[-1][1] == elt:

                drivers, _ = _elts.pop()

                if drivers:

                    if isinstance(elt, Expression):
                        crud = Read(query=elt)

                    else:
                        crud = elt

                    crudcopy = crud.copy()

                    threads = []

                    for driver in drivers:
                        updatename(elt=crudcopy, driver=driver)

                        async = kwargs.pop('async', True)

                        ctx[elt] = []

                        def callback(transaction, **kwargs):
                            ctx[elt] += transaction.ctx[crudcopy]

                        thread = transaction.open(
                            driver=driver, cruds=[crudcopy]
                        ).commit(async=async, callback=callback, **kwargs)

                        threads.append(thread)

                    for thread in threads:
                        thread.join()

                    result = ctx[elt]

                else:
                    raise ValueError(
                        'No driver found to process {0}'.format(elt)
                    )

        return result

    def __repr__(self):
        """Driver representation with drivers."""
        return 'CompositeDriver({0}, {1}, {2})'.format(
            self.name, self.drivers, self.ddriver
        )


def getchildren(elt):
    """Get children element from the request tree.

    :param BaseElement elt: element from where get children.
    :rtype: list
    """
    result = []

    if isinstance(elt, Function):

        result = elt.params

    elif isinstance(elt, CRUDElement):

        result.append(elt.query)

        if isinstance(elt, (Create, Update)):

            result.append(elt.name)

            for name, value in iteritems(elt.values):
                result.append(name)
                result.append(value)

        elif isinstance(elt, Read):

            result += elt.select()
            result += elt.groupby()
            result += elt.orderby()
            result.append(elt.join())
            result.append(elt.limit())
            result.append(elt.offset())

        elif isinstance(elt, Delete):

            result += elt.names()

    return result


def updatename(elt, driver):
    """Rename elt in order to be specific to input driver."""
    for slot in elt.__slots__:

        subelt = getattr(elt, slot)

        if isinstance(subelt, Expression):
            if subelt.name.startswith(driver.name):
                subelt.name = subelt.name[len(driver.name) + 1:]

        elif isinstance(subelt, CRUDElement):

            subelt = updatename(elt=subelt, driver=driver)
            setattr(elt, slot, subelt)
