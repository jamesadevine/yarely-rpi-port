import copy


class StateMachineError(Exception):
    pass


class StateAlreadyDefinedError(StateMachineError):
    def __init__(self, state):
        msg = "The state '{state}' is already defined."
        super().__init__(msg.format(state=state))


class StateNotDefinedError(StateMachineError):
    def __init__(self, state):
        msg = "The state '{state}' is not defined."
        super().__init__(msg.format(state=state))


class TransitionAlreadyDefinedError(StateMachineError):
    def __init__(self, in_state, trigger):
        msg = "The transition in state '{in_state}' given trigger "\
            "'{trigger}' is already defined."
        super().__init__(msg.format(in_state=in_state,
            trigger=trigger))


class InitialStateNotDefinedError(StateMachineError):
    def __init__(self, initial_state):
        msg = "The initial state '{initial_state}' is not defined."
        super().__init__(msg.format(initial_state=initial_state))


class DestinationStateNotDefinedError(StateMachineError):
    def __init__(self, in_state, trigger, destination_state):
        msg = "The destination state '{destination_state}' (reached from "\
            "state '{in_state}' given trigger '{trigger}') is not defined."
        super().__init__(msg.format(in_state=in_state,
            trigger=trigger, destination_state=destination_state))


class UnexpectedTriggerError(StateMachineError):
    def __init__(self, in_state, trigger):
        msg = "The current state '{in_state}' has no transition for the " \
            "trigger '{trigger}'."
        super().__init__(msg.format(in_state=in_state,
            trigger=trigger))


class StateMachineFactory:
    """A factory that can create State Machines.

    Create a factory:
    >>> smf = StateMachineFactory()

    Provide the valid states:
    >>> smf.add_state("Idle")
    >>> smf.add_state("Heating")
    >>> smf.add_state("Cooling")
    >>> smf.add_state("Powered off")

    Provide the transitions:
    >>> smf.add_transition("Idle", "too cold", "Heating")
    >>> smf.add_transition("Idle", "too hot", "Cooling")
    >>> smf.add_transition("Idle", "comfortable", "Idle")
    >>> smf.add_transition("Idle", "power off", "Powered off")
    >>> smf.add_transition("Heating", "too cold", "Heating")
    >>> smf.add_transition("Heating", "too hot", "Idle")
    >>> smf.add_transition("Heating", "comfortable", "Heating")
    >>> smf.add_transition("Heating", "power off", "Powered off")
    >>> smf.add_transition("Cooling", "too cold", "Idle")
    >>> smf.add_transition("Cooling", "too hot", "Cooling")
    >>> smf.add_transition("Cooling", "comfortable", "Cooling")
    >>> smf.add_transition("Cooling", "power off", "Powered off")

    Build a State Machine at the initial state:
    >>> sm = smf.build_state_machine('Idle')

    >>> sm.get_state()
    'Idle'

    Advance between the states:
    >>> sm.advance("too hot")
    >>> sm.get_state()
    'Cooling'
    >>> sm.advance("comfortable")
    >>> sm.get_state()
    'Cooling'
    >>> sm.advance("too cold")
    >>> sm.get_state()
    'Idle'
    >>> sm.advance("power off")
    >>> sm.state_is_terminal()
    True

    """

    def __init__(self, state_machine_factory=None):
        """A factory that allows the programatic construction of a
        state machine and a mechanism to build multiple copies of the
        machine.

        state_machine_factory is an optional instance of StateMachineFactory
        that will be used as initial states and transitions.

        """
        # Dict keyed by in_state => (dict keyed by trigger => nest_state)
        self.__transitions = {}

        if state_machine_factory is not None:
            # We must pass through states twice as add_transition expects both
            # in_state and next_state to be defined already.
            states = state_machine_factory.get_states()
            for state in states:
                self.add_state(state)

            for state in states:
                transitions = state_machine_factory.get_transitions(state)
                for (trigger, next_state) in transitions.items():
                    self.add_transition(state, trigger, next_state)

    def add_state(self, state):
        """Add a state to the machine definition.

        Raises StateAlreadyDefinedError if the state is already defined.

        """
        if state in self.__transitions:
            raise StateAlreadyDefinedError(state)

        self.__transitions[state] = {}

    def add_transition(self, in_state, trigger, next_state):
        """Add a transition from in_state, given trigger, to next_state.

        Raises StateNotDefinedError if either in_state or next_state are not
        defined.

        Raises TransitionAlreadyDefinedError if in_state already has a
        transition for the given trigger.
        """
        if in_state not in self.__transitions:
            raise StateNotDefinedError(in_state)

        if next_state not in self.__transitions:
            raise StateNotDefinedError(next_state)

        if trigger in self.__transitions[in_state]:
            raise TransitionAlreadyDefinedError(in_state, trigger)

        self.__transitions[in_state][trigger] = next_state

    def get_states(self):
        """Return a list of the states in the machine definition."""
        return list(self.__transitions.keys())

    def get_transitions_for_state(self, state):
        """Return a dictionary of (trigger: next_state) mappings for the given
        state"""
        return dict(self.__transitions[state])

    def build_state_machine(self, initial_state, cls=None):
        """Return a StateMachine instance initialised at a particular state.

        initial_state - the initial machine state.
        cls - An optional subclass of StateMachine.

        """

        if cls is None:
            cls = StateMachine
        return cls(self.__transitions, initial_state)


class StateMachine:
    def __init__(self, transitions, initial_state):
        """Create a state machine that will step through the transitions
        from initial_state.

        transitions - a dictionary of states & transitions from them.
        initial_state - the starting state.

        Raises InitialStateNotDefinedError if initial_state is not defined.

        Raises DestinationStateNotDefinedError if the transition map is
        not complete.

        """

        if initial_state not in transitions:
            raise InitialStateNotDefinedError(initial_state)

        # We take a deepcopy of transitions so that later alterations
        # in the factory cannot affect a live state machine.

        self.__transitions = copy.deepcopy(transitions)
        self.__state = initial_state

        # Belt and braces - the factory will ensure this is ok, but
        # we want to be sure in cases where the factory is not used.
        for state in self.__transitions:
            for trigger in self.__transitions[state]:
                destination_state = self.__transitions[state][trigger]
                if destination_state not in self.__transitions:
                    raise DestinationStateNotDefinedError(
                        state, trigger, destination_state)

        self.__callbacks = {"entering": {}, "leaving": {}}
        self._register_callbacks()

    def get_state(self):
        """Return the current state."""
        return self.__state

    def state_is_terminal(self):
        """True if the current state is terminal (no triggers defined).

        Note that a transition from this state to itself via a trigger
        (a loop) will prevent this state from being terminal.

        """
        return len(self.__transitions[self.__state]) == 0

    def advance(self, trigger):
        """Advance to the next state, given the trigger.

        Raises UnexpectedTriggerError if there is no transition from the
        current state via the provided trigger.

        """
        if trigger not in self.__transitions[self.__state]:
            raise UnexpectedTriggerError(self.__state, trigger)

        previous_state = self.__state
        next_state = self.__transitions[self.__state][trigger]

        self.__callback_leaving(previous_state, next_state, trigger)
        self.__state = next_state
        self.__callback_entering(next_state, previous_state, trigger)

    def _register_callbacks(self):
        """Subclasses can implement this method to register callback methods
        whilst the state machine is being initialised.

        """
        pass

    def register_callback_entering(self, state, callable):
        """Register a callback function to be called when transitioning
        into the supplied state.

        The callback will be called with:
        callable('entering', state, previous_state, trigger)

        """

        self.__register_callback_for_occasion('entering', state, callable)

    def register_callback_leaving(self, state, callable):
        """Register a callback function to be called when transitioning
        from the supplied state.

        The callback will be called with:
        callable('leaving', state, next_state, trigger)

        """

        self.__register_callback_for_occasion('leaving', state, callable)

    def __register_callback_for_occasion(self, occasion, state, callable):
        if state not in self.__callbacks[occasion]:
            self.__callbacks[occasion][state] = []

        self.__callbacks[occasion][state].append(callable)

    def __callback_entering(self, state, previous_state, trigger):
        occasion = 'entering'
        callables = self.__get_callables_for_occasion(occasion, state)
        for callable in callables:
            callable(occasion, state, previous_state, trigger)

    def __callback_leaving(self, state, next_state, trigger):
        occasion = 'leaving'
        callables = self.__get_callables_for_occasion(occasion, state)
        for callable in callables:
            callable(occasion, state, next_state, trigger)

    def __get_callables_for_occasion(self, occasion, state):
        callables = []

        if state in self.__callbacks[occasion]:
            callables.extend(self.__callbacks[occasion][state])

        callback_attr_template = "_callback_{occasion}_{state}"
        callback_attr = callback_attr_template.format(occasion=occasion,
            state=state)

        callback = getattr(self, callback_attr, None)
        if callback is not None:
            callables.append(callback)

        return callables
