import unittest

from yarely.frontend.core.helpers.decorators import singleton


class SingletonTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        @singleton
        class SingletonA:
            def __init__(self, flag):
                self.flag = flag

        @singleton
        class SingletonB:
            def __init__(self, flag):
                self.flag = flag

        # singleton_a uses args, whilst singleton_b uses kwargs
        cls._singleton_a_true = SingletonA(True)
        cls._singleton_a_false = SingletonA(False)
        cls._singleton_b_true = SingletonB(flag=True)
        cls._singleton_b_false = SingletonB(flag=False)

    def test_single_instance_per_class(self):
        self.assertIs(self._singleton_a_true, self._singleton_a_false)

    def test_different_classes_have_different_instances(self):
        self.assertIsNot(self._singleton_a_true, self._singleton_b_true)

    def test_first_instance_args_taken(self):
        self.assertIs(self._singleton_a_true.flag, True)

    def test_second_instance_args_ignored(self):
        self.assertIs(self._singleton_a_false.flag, True)

    def test_first_instance_kwargs_taken(self):
        self.assertIs(self._singleton_b_true.flag, True)

    def test_second_instance_kwargs_ignored(self):
        self.assertIs(self._singleton_b_false.flag, True)
