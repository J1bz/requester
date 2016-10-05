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

"""Driver module."""

try:
    from threading import thread

except ImportError:
    from dummy_threading import Thread


from .transaction import Transaction, State

__all__ = ['Driver']


DEFAULT_EXPLAIN = False  #: default explain value.
DEFAULT_ASYNC = False  #: default async value.


class Driver(object):
    """In charge of accessing to data from a transaction."""

    name = None  # driver name

    def __init__(self, name=None, *args, **kwargs):

        super(Driver, self).__init__(*args, **kwargs)

        if name is not None:
            self.name = name

    def open(self, ctx=None, autocommit=False, cruds=None):
        """open a new transaction.

        :param Context ctx: execution context.
        :param bool autocommit: transaction autocommit property. False by
            default.
        :rtype: Transaction.
        """

        return Transaction(
            driver=self, ctx=ctx, autocommit=autocommit, cruds=cruds
        )

    def process(
            self, transaction,
            explain=DEFAULT_EXPLAIN, async=DEFAULT_ASYNC, callback=None,
            **kwargs
    ):
        """Process input transaction and crud element.

        :param Request transaction: transaction to process.
        :param bool explain: give additional information about the transaction
            execution.
        :param bool async: if True (default False), execute input crud in a
            separated thread.
        :param callable callback: callable function which takes in parameter the
            function result. Commonly used with async equals True.
        :param dict kwargs: additional parameters specific to the driver.
        :return: transaction.
        :rtype: Request
        """

        def process(
                transaction=transaction, explain=explain, callback=callback,
                **kwargs
        ):

            result = self._process(
                transaction=transaction, explain=explain, **kwargs
            )

            if callback is not None:
                callback(result)

            return result

        if transaction.state == State.COMMITTING:
            if async:
                Thread(target=process).start()

            else:
                return process()

    def _process(self, transaction, explain=False, **kwargs):
        """Generic method to override in order to crud input data related to
        transaction and kwargs.

        :param Transaction transaction: transaction to process.
        :param bool explain: give additional information about the transaction
            execution.
        :param dict kwargs: additional parameters specific to the driver.
        :return: transaction.
        :rtype: Request
        """

        raise NotImplementedError()

    def __repr__(self):

        return 'Driver({0})'.format(self.name)

    def __str__(self):

        return repr(self)

    def __getitem__(self, key):

        return self.read(key).ctx[key]

    def __setitem__(self, key, value):

        return self.update(name=key, **value)

    def __delitem__(self, key):

        return self.delete(key)

    def _getcrud(self, cls, **kwargs):

        transaction = self.open(autocommit=True)

        crud = cls(transaction=transcation, **kwargs)

        return crud()

    def create(self, **kwargs):
        """Create creation."""

        return self._getcrud(cls=Create, **kwargs)

    def read(self, **kwargs):
        """Read input expressions.

        :param tuple select: selection fields.
        :param dict kwargs: additional selection parameters (limit, etc.).
        :rtype: Cursor
        """

        return self._getcrud(cls=Read, **kwargs)

    def update(self, **values):
        """Apply input updates.

        :param tuple updates: updates to apply.
        """

        return self._getcrud(cls=Update, **kwargs)

    def delete(self, *names):
        """Delete input deletes.

        :param tuple names: model name to delete.
        :return: number of deleted deletes.
        """

        return self._getcrud(cls=Delete, **kwargs)
