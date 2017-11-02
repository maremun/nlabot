#   encoding: utf-8
#   checker.py

from collections import Callable
from functools import wraps
from io import StringIO
from traceback import print_exc


class IChecker(object):
    """
    :param notebook:
    :type object:
    """

    def __init__(self, notebook, *args, **kwargs):
        self.nb = notebook

    def __call__(self):
        return self.check()

    def check(self):
        raise NotImplemented('Child of IChecker object must implement this.')

    def is_callable(self, name):
        if not hasattr(self.nb, name):
            return False
        attr = getattr(self.nb, name)
        if not isinstance(attr, Callable):
            return False
        return True

    def make_report(self, name):
        report = {
            'task': name,
            'exists': self.is_callable(name),
            'pass': []
        }
        return report


class TestChecker(IChecker):

    def __init__(self, module):
        super(TestChecker, self).__init__(module)

    def check(self):
        results = [
            self.check_foo(),
            self.check_bar(),
            self.check_zoo(),
        ]
        return results

    foo_cases = [(None, 42)]
    bar_cases = [(2, 4), (3, 9), (5, 25)]
    zoo_cases = [(2, 4), (3, 9), (4, 42)]

    def check_dec(name, cases=None):
        def wrap(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                report = args[0].make_report(name)
                if cases is None:
                    report['pass'] = [0]  # no cases provided
                else:
                    report['pass'] = [0] * len(cases)
                if not report['exists']:
                    return report
                try:
                    for i, (argument, result) in enumerate(cases):
                        if argument is None:
                            if result == f(*args, **kwargs)():
                                report['pass'][i] = 1
                        else:
                            if result == f(*args, **kwargs)(argument):
                                report['pass'][i] = 1
                except Exception as e:
                    fout = StringIO()
                    print_exc(file=fout)
                    report['exc_info'] = fout.getvalue()
                    fout.close()
                finally:
                    return report

            return wrapper
        return wrap

    @check_dec('foo', foo_cases)
    def check_foo(self):
        return self.nb.foo

    @check_dec('bar', bar_cases)
    def check_bar(self):
        return self.nb.bar

    @check_dec('zoo', zoo_cases)
    def check_zoo(self):
        return self.nb.zoo
