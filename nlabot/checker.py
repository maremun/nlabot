#   encoding: utf-8
#   checker.py

from collections import Callable


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

    def check_foo(self):
        report = self.make_report('foo')

        if not report['exists']:
            return report

        try:
            res = self.nb.foo()
            if res == 42:
                report['pass'].append(1)
            else:
                report['pass'].append(0)
        except Exception as e:
            report['exc_info'] = str(e)  # FIXME
        finally:
            return report

    def check_bar(self):
        report = self.make_report('bar')

        if not report['exists']:
            return report

        try:
            cases = [
                (2,  4),
                (3,  9),
                (5, 25),
            ]

            for argument, result in cases:
                if result == self.nb.bar(argument):
                    report['pass'].append(1)
                else:
                    report['pass'].append(0)
        except Exception as e:
            report['exc_info'] = str(e)  # FIXME
        finally:
            return report

    def check_zoo(self):
        report = self.make_report('zoo')

        if not report['exists']:
            return report

        try:
            cases = [
                (2,  4),
                (3,  9),
                (5, 42),
            ]

            for argument, result in cases:
                if result == self.nb.zoo(argument):
                    report['pass'].append(1)
                else:
                    report['pass'].append(0)

        except Exception as e:
            report['exc_info'] = str(e)  # FIXME
        finally:
            return report
