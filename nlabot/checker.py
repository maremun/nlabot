#   encoding: utf-8
#   checker.py

from collections import Callable
from io import StringIO
from sys import exc_info
from traceback import print_exc, print_exception


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
        foo_cases = [(None, 42)]
        bar_cases = [(2, 4), (3, 9), (5, 25)]
        zoo_cases = [(2, 4), (3, 9), (4, 42)]

        results = [
            self.test('foo', foo_cases),
            self.test('bar', bar_cases),
            self.test('zoo', zoo_cases),
        ]
        return results

    def test(self, name, cases):
        report = self.make_report(name)
        if cases is None:
            report['pass'] = [0]  # no cases provided
        else:
            report['pass'] = [0] * len(cases)
        if not report['exists']:
            return report

        func = getattr(self.nb, name)
        try:
            for i, (argument, result) in enumerate(cases):
                if argument is None:
                    if result == func():
                        report['pass'][i] = 1
                else:
                    if result == func(argument):
                        report['pass'][i] = 1
        except MemoryError as e:
            fout = StringIO()
            print_exception(*exc_info()[:2], None, file=fout)
            report['mem'] = fout.getvalue()
            fout.close()
        except Exception as e:
            fout = StringIO()
            print_exc(file=fout)
            report['exc_info'] = fout.getvalue()
            fout.close()
        finally:
            return report
