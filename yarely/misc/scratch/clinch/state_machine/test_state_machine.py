import doctest
import unittest

import state_machine


def load_tests(load, tests, ignore):
    tests.addTests(doctest.DocTestSuite(state_machine))
    return tests


class StateMachineFactoryTestCase(unittest.TestCase):
    def setUp(self):
        self._smf = state_machine.StateMachineFactory()

    def test_cannot_add_same_state_twice(self):
        self._smf.add_state("State A")
        with self.assertRaises(state_machine.StateAlreadyDefinedError):
            self._smf.add_state("State A")

    def test_adding_transition_requires_in_state_defined(self):
        self._smf.add_state("State B")
        with self.assertRaises(state_machine.StateNotDefinedError):
            self._smf.add_transition(
                'State A', 'Trigger A', 'State B')

    def test_adding_transition_requires_new_state_defined(self):
        self._smf.add_state("State A")
        with self.assertRaises(state_machine.StateNotDefinedError):
            self._smf.add_transition(
                'State A', 'Trigger A', 'State B')

    def test_add_transition_works(self):
        self._smf.add_state("State A")
        self._smf.add_state("State B")
        self._smf.add_transition(
            'State A', 'Trigger A', 'State B')

    def test_cannot_add_same_transition_twice(self):
        self._smf.add_state("State A")
        self._smf.add_state("State B")
        self._smf.add_transition(
            'State A', 'Trigger A', 'State B')
        with self.assertRaises(state_machine.TransitionAlreadyDefinedError):
            self._smf.add_transition(
                'State A', 'Trigger A', 'State B')

    def test_initial_state_must_exist(self):
        self._smf.add_state("State A")
        self._smf.add_state("State B")
        self._smf.add_transition(
            'State A', 'Trigger A', 'State B')
        with self.assertRaises(
                state_machine.InitialStateNotDefinedError):
            self._smf.build_state_machine('State C')


class StateMachineTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._smf = state_machine.StateMachineFactory()
        cls._smf.add_state('State A')
        cls._smf.add_state('State B')
        cls._smf.add_transition('State A', 'Trigger A', 'State B')

    def setUp(self):
        self._sm = self._smf.build_state_machine('State A')

    def test_initial_state_correct(self):
        self.assertEqual(self._sm.get_state(), 'State A')

    def test_advance_fails_on_unexpected_trigger(self):
        with self.assertRaises(state_machine.UnexpectedTriggerError):
            self._sm.advance("Trigger B")

    def test_state_updated_on_advance(self):
        self._sm.advance("Trigger A")
        self.assertEqual(self._sm.get_state(), 'State B')

    def test_final_state_is_terminal(self):
        self._sm.advance("Trigger A")
        self.assertIs(self._sm.state_is_terminal(), True)

    def test_intermediate_state_is_not_terminal(self):
        self.assertIs(self._sm.state_is_terminal(), False)


class StateMachineWithCallbacks(state_machine.StateMachine):
    def _register_callbacks(self):
        super()._register_callbacks()
        self.register_callback_leaving('State A', self.unittest_callback)
        self.register_callback_entering('State B', self.unittest_callback)

    def unittest_callback(self, occasion, state, other_state, trigger):
        if occasion == 'leaving' and state == 'State A':
            self.unittest_left_state_a = True
        elif occasion == 'entering' and state == 'State B':
            self.unittest_entered_state_b = True


class StateMachineWithCallbacksTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._smf = state_machine.StateMachineFactory()
        cls._smf.add_state('State A')
        cls._smf.add_state('State B')
        cls._smf.add_transition('State A', 'Trigger A', 'State B')

    def setUp(self):
        self._sm = self._smf.build_state_machine('State A',
            StateMachineWithCallbacks)
        self._sm.unittest_left_state_a = False
        self._sm.unittest_entered_state_b = False

    def test_handlers(self):
        self._sm.advance("Trigger A")
        self.assertEqual(self._sm.unittest_left_state_a, True)
        self.assertEqual(self._sm.unittest_entered_state_b, True)
