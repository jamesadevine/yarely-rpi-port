import datetime
import re
import time
from ast import literal_eval
from xml.etree import ElementTree


class ConstraintsError(Exception):
    """Base class for constraints errors."""
    pass


class ConstraintConditionMatchError(ConstraintsError):
    """Base class for errors in checking if a constriant is met."""
    pass


class ConstraintNotImplementedError(NotImplementedError):
    """Base class for Constraints-related 'not implemented' errors"""
    pass


class ConstraintsParserError(ConstraintsError):
    """Base class for constraint parsing errors."""
    pass


class ConstraintConditionError(ConstraintsError):
    """Base class for constraint condition errors."""
    pass


class DateConstraintParserError(ConstraintsParserError):
    """Base class for Constraint parsing errors."""
    pass


class DayOfWeekConstraintParserError(ConstraintsParserError):
    """Base class for Constraint parsing errors."""
    pass


class PreferredDurationParserError(ConstraintsParserError):
    """Base class for preferred duration constraint parsing errors."""
    pass


class PriorityConstraintParserError(ConstraintsParserError):
    """Base class for priority constraint parsing errors."""
    pass


class TimeConstraintParserError(ConstraintsParserError):
    """Base class for time constraint parsing errors."""
    pass


class DOWTimeConstraintParserError(TimeConstraintParserError):
    """Base class for day-of-week time constraint parsing errors."""
    pass


class DateTimeConstraintConditionError(ConstraintsError):
    """Base class for datetime constraint condition errors."""
    pass


class PriorityConstraintConditionError(ConstraintsError):
    """Base class for priority constraint condition errors."""
    pass


class ConstraintsParser:
    """Parse Constraints XML to produce a list of Constraint objects."""
    def __init__(self, constraints_elem):
        """Parse the given etree element and it's children and create a
        new constraint list.

        """
        CONSTRAINT_TAG_CLASS_MAP = {
            'date': DateConstraint,
            'day-of-week': DayOfWeekConstraint,
            'output-constraints': OutputConstraint,
            'playback': PlaybackConstraint,
            'preferred-duration': PreferredDurationConstraint,
            'priority': PriorityConstraint,
            'time': TimeConstraint,
        }

        if constraints_elem.tag != 'constraints':
            msg = "Expected root tag of 'constraints', found {tag}"
            raise ConstraintsParserError(msg.format(tag=constraints_elem.tag))
        self.etree = ElementTree.ElementTree(constraints_elem)
        self.constraints = []

        for constraint_type in constraints_elem:
            cls = Constraint
            if constraint_type.tag == 'scheduling-constraints':
                for scheduling_constraint in constraint_type:
                    cls = SchedulingConstraint
                    try:
                        cls = CONSTRAINT_TAG_CLASS_MAP[
                            scheduling_constraint.tag
                        ]
                    except KeyError:
                        pass                        # FIXME - log a warning
                    self.constraints.append(cls(scheduling_constraint))
            else:
                try:
                    cls = CONSTRAINT_TAG_CLASS_MAP[constraint_type.tag]
                except KeyError:
                    pass                            # FIXME - log a warning
                self.constraints.append(cls(constraint_type))

    def constraints_are_met(self, condition=None, allow_unknowns=True):
        """Checks to see all the parsed constraints are met in the
        specified condition. Default condition is what we know about
        the current condition (i.e. date, time).

        If allow_unknowns is False the method will return False if any
        of the constraints is_met() methods raise a
        ConstraintNotImplementedError (i.e. it is not currently possible
        to tell if this constraint is met. If allow_unknowns is True (the
        default value) all this exceptions will be silently ignored and
        only the implemented is_met() values will be checked.

        """
        # FIXME - recurse_up_tree=True (don't forget the docstring)

        for constraint_met in self.constraints:
            try:
                if not constraint_met.is_met(condition):
                    return False
            except ConstraintNotImplementedError:
                if not allow_unknowns:
                    return False
        return True

    def get_constraints(self):
        """Gets the list of Constraints generated as a result of parsing."""
        return self.constraints


class Constraint:
    """Base class for constraints."""
    def __init__(self, etree_elem, valid_comparison_conditions=None):
        """Creates a new Constraint based on the specified etree element."""
        super().__init__()
        self.etree = (
            ElementTree.ElementTree(etree_elem)
            if etree_elem is not None else None
        )
        if valid_comparison_conditions is None:
            valid_comparison_conditions = []
        self.valid_comparison_conditions = valid_comparison_conditions

    def _valid_comparison_condition(self, condition):
        for valid_comparison_condition in self.valid_comparison_conditions:
            if isinstance(condition, valid_comparison_condition):
                return True
        return False

    def _is_met(self, condition=None):
        raise ConstraintNotImplementedError()

    def is_met(self, condition=None):
        """Checks to see if this constraint is met in the specified condition.
        Default condition is what we know about the current condition (i.e.
        date, time).

        """
        if condition and not self._valid_comparison_condition(condition):
            valid_condition_classes = [
                valid_comparison_condition.__class__.__name__
                for valid_comparison_condition
                in self.valid_comparison_conditions
            ]
            valid_condition_classes = ', '.join(valid_condition_classes)
            msg = (
                'It is not valid to compare this constraint against the '
                'specified condition.\nThis object is an instance of '
                '{constraint_class} and can only be compared with the '
                'following condition types: {valid_condition_classes}'
            )
            msg = msg.format(
                constraint_class=self.__class__.__name__,
                valid_condition_classes=valid_condition_classes
            )
            raise ConstraintConditionMatchError(msg)
        return self._is_met(condition)


class OutputConstraint(Constraint):
    """Base class for output constraints."""
    pass


class SchedulingConstraint(Constraint):
    """Base class for scheduling constraints."""
    pass


class PlaybackConstraint(SchedulingConstraint):
    """Constraints that talk about preferred playout duration."""

    ALL_PLAYBACK_ORDERS = ['random', 'inorder', 'reverseorder']
    DEFAULT_PLAYBACK_ORDER = None
    AVOID_CONTEXT_SWITCH_DEFAULT = None
    UNSCALED_RATIO_DEFAULT = None
    _RATIO_REGEXP = '(?P<value>[\d]*\.?[\d]+)(?P<unit>%)?$'

    def __init__(self, etree_elem):
        super().__init__(etree_elem)
        attrib = etree_elem.attrib

        if 'ratio' in attrib:
            match = re.match(self._RATIO_REGEXP, attrib['ratio'])
            if not match:
                self.unscaled_ratio = self.UNSCALED_RATIO_DEFAULT
            match_val = min(max(float(match.group('value')), 0.0), 100)
            self.unscaled_ratio = (
                match_val / 100
                if match.group('unit') == '%' or match_val > 1 else match_val
            )
        else:
            self.unscaled_ratio = self.UNSCALED_RATIO_DEFAULT

        self.order = (
            attrib['order']
            if 'order' in attrib and
               attrib['order'] in self.ALL_PLAYBACK_ORDERS
            else self.DEFAULT_PLAYBACK_ORDER
        )

        try:
            self.avoid_context_switch = literal_eval(
                attrib['avoid-context-switch'].capitalize()
            )
        except (KeyError, ValueError):
            self.avoid_context_switch = self.AVOID_CONTEXT_SWITCH_DEFAULT

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return False
        orders_equal = self.order == other.order
        ratios_equal = self.unscaled_ratio == other.unscaled_ratio
        return orders_equal and ratios_equal

    def get_avoid_context_switch(self):
        """Get the value of avoid_context_switch for this constraint."""
        return self.avoid_context_switch

    def get_order(self):
        """Get any ordering information for this constraint.
        See also PlaybackConstraint.ALL_PLAYBACK_ORDERS.

        """
        return self.order

    def get_unscaled_ratio(self):
        """Get any ratio information for this constraint."""
        return self.unscaled_ratio


class PreferredDurationConstraint(SchedulingConstraint):
    """Constraints that talk about preferred playout duration."""
    def __init__(self, etree_elem):
        super().__init__(etree_elem)

        # Duration is represented as the number of seconds.
        # Note that seconds may be a floating point value.
        self.preferred_duration = float(etree_elem.text)

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return False
        return self.preferred_duration == other.preferred_duration

    def __float__(self):
        return self.preferred_duration

    def __int__(self):
        return int(self.preferred_duration)


class PriorityConstraint(SchedulingConstraint):
    """Constraints that talk about priority."""

    # These must be listed in priority order (lowest->highest)
    ALL_PRIORITIES = ['lowest', 'low', 'medium', 'high', 'highest']
    DEFAULT_VALUE = ALL_PRIORITIES[2]

    def __init__(self, etree_elem):
        valid_comparison_conditions = [PriorityConstraintCondition]
        super().__init__(etree_elem, valid_comparison_conditions)

        # Attempt to read a priority level from the XML
        # Accept either text or index (text is probably the most common case).
        # E.g.
        #     <priority level="highest"/>
        # Which is equivalent to:
        #     <priority level="4"/>
        if 'level' in etree_elem.attrib:
            if etree_elem.attrib['level'] in self.ALL_PRIORITIES:
                self.priority = etree_elem.attrib['level']
            else:
                try:
                    priority_level = int(etree_elem.attrib['level'])
                    if priority_level < len(self.ALL_PRIORITIES):
                        self.priority = self.ALL_PRIORITIES[priority_level]
                    else:
                        msg = 'Invalid integer priority level:'
                        msg += '"{level}" is out of range'
                        msg = msg.format(level=priority_level)
                except ValueError:
                    msg = 'Unrecognised priority level value: "{level}"'
                    msg = msg.format(level=etree_elem.attrib['level'])
        else:
            msg = 'Expected level attribute, not found: "{xml}"'
            xml_str = ElementTree.tostring(etree_elem, encoding="unicode")
            msg = msg.format(xml=xml_str)
        if not hasattr(self, 'priority'):
            raise PriorityConstraintParserError(msg)

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return False
        return self.priority == other.priority

    def __int__(self):
        return self.ALL_PRIORITIES.index(self.priority)

    def _is_met(self, condition=None):
        """Checks to see if this constraint is met in the specified condition.
        Default condition is what we know about the current condition (not
        currently implemented).

        """
        if condition is None:
            raise ConstraintNotImplementedError()
        return self.priority == condition.data


class TimeConstraint(SchedulingConstraint):
    """Constraints that talk about the time of day."""
    def __init__(self, etree_elem):
        valid_comparison_conditions = [DateTimeConstraintCondition]
        super().__init__(etree_elem, valid_comparison_conditions)
        (self.start_time, self.end_time) = self._parse_etree()

    def _parse_etree(self):
        time_range = self.etree.find('between')
        if time_range is None:
            msg = "Expected 'between' tag, not found."
            raise TimeConstraintParserError(msg)

        between = dict()
        for attr in ('start', 'end'):
            time_string = time_range.get(attr)
            between[attr] = parse_time(time_string)

        return (between['start'], between['end'])

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return False
        starts_equal = self.start_time == other.start_time
        ends_equal = self.end_time == other.end_time
        return starts_equal and ends_equal

    def _is_met(self, condition=None):
        """Checks to see if this constraint is met in the specified condition.
        Default condition is what we know about the current condition (i.e.
        date, time).

        This constraint will be met if the condition time is between
        self.start_time and self.end_time (inclusive).

        """
        condition = (datetime.datetime.now()
                     if condition is None else condition.data)
        condition_time = condition.time()

        has_started = self.start_time <= condition_time
        has_not_ended = self.end_time > condition_time

        return has_started and has_not_ended


def parse_time(time_in):
    """Attempts to convert an unknown time representation to a
    datetime.time object.

     """
    time_in_type = type(time_in)    
    if time_in_type is datetime.time:
        return time_in
    if time_in_type is datetime.datetime:
        return time_in.timetz()
    if time_in_type is str:
        return datetime.datetime.strptime(time_in, '%H:%M:%S').time()

    msg = 'Could not parse time: {time_in}'.format(time_in=time_in)
    raise TimeConstraintParserError(msg)


class DOWTimeConstraint(TimeConstraint):

    def _parse_etree(self):
        if self.etree is None:
            return (datetime.time.min, datetime.time.max)

        between = dict()
        for attr in ('time_start', 'time_end'):
            time_string = self.etree.getroot().get(attr)
            between[attr] = parse_time(time_string)

        if between['time_start'] >= between['time_end']:
            msg = (
                "time_start attribute value must be less than "
                "time_end attribute value"
            )
            raise DOWTimeConstraintParserError(msg)
        return (between['time_start'], between['time_end'])

    def is_met(self, condition=None):
        if self.start_time is None:
            return False
        return super().is_met(condition)


class DayOfWeekConstraint(SchedulingConstraint):
    """Constraints that talk about the day of week."""

    def __init__(self, etree_elem):
        valid_comparison_conditions = [DateTimeConstraintCondition]
        super().__init__(etree_elem, valid_comparison_conditions)

        def day_of_week(day_string):
            """Find day number corresponding to day_string (case insensitive).
               Monday/Mon is 0.

            """
            try:
                return time.strptime(day_string, '%A').tm_wday
            except ValueError as e:
                try:
                    return time.strptime(day_string, '%a').tm_wday
                except ValueError:
                    raise e

        # Create an internal representation of start and end time
        # for each day of the week.
        #
        # These are stored in a list with indexes 0 to 6 (Monday is 0).
        self._data = [None] * 7
        for i in range(7):
            self._data[i] = DOWTimeConstraint(etree_elem=None)

        # A day-of-week constraint either contains:
        #   * One child 'between' tag     OR
        #   * Up to seven tags, one per weekday, e.g.
        #         <Sunday time_end="19:59:59" time_start="06:00:00" />

        # Handle a 'between' tag
        between = etree_elem.find("between")
        if between is not None:
            start_day = day_of_week(between.get("start"))
            end_day = day_of_week(between.get("end"))
            if start_day == end_day or start_day < end_day:
                for i in range(start_day):
                    self._data[i].start_time = None
                for i in range(end_day+1, 7):
                    self._data[i].start_time = None
            else:                     # start_day > end_day
                for i in range(end_day+1, start_day):
                    self._data[i].start_time = None
            return

        # Handle weekday tags
        found_weekdays = list()
        unknown_children = list()
        for child in etree_elem:
            try:
                dow_index = day_of_week(child.tag)
            except ValueError:
                unknown_children.append(child.tag)
                continue
            found_weekdays.append(dow_index)
            self._data[dow_index] = DOWTimeConstraint(etree_elem=child)
        dont_show_days = [
            day for day in range(7) if day not in found_weekdays
        ]
        for day in dont_show_days:
            self._data[day].start_time = None

        # Handle no valid children
        if not len(found_weekdays):
            msg = (
                "A day-of-week element should contain either\n"
                "1) Exactly one child tag matching 'between'\n    OR\n"
                "2) Up to seven tags matching names for days of the week "
                "(e.g. 'sunday')\n\n"
            )
            msg += (
                "The following unrecognised child elements were found: "
                "{unknown_children}".format(", ".join(unknown_children))
                if len(unknown_children) else "No child elements found"
            )
            raise DayOfWeekConstraintParserError(msg)

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return False
        for i in range(7):
            if self._data[i] != other._data[i]:
                return False
        return True

    def _is_met(self, condition=None):
        """Checks to see if this constraint is met in the specified condition.
        Default condition is what we know about the current condition (i.e.
        date, time).
        """
        condition = (datetime.datetime.now()
                     if condition is None else condition.data)

        # We use datetime.weekday() to get a number for today -> Mon=0,
        # Sun=6. This is the same format as the time.struct_time created
        # by time.strptime.
        dow = condition.date().weekday()

        return self._data[dow].is_met()


class DateConstraint(SchedulingConstraint):
    """Constraints that talk about a date range."""

    def __init__(self, etree_elem):
        valid_comparison_conditions = [DateTimeConstraintCondition]
        super().__init__(etree_elem, valid_comparison_conditions)

        def date_from_string(date_string):
            """Find date corresponding to date_string."""
            return datetime.date(*time.strptime(date_string, '%Y-%m-%d')[:3])

        date_range = etree_elem.find('between')
        if date_range is None:
            msg = "Expected 'between' tag, not found."
            raise DateConstraintParserError(msg)
        self.start_date = date_from_string(date_range.get('start'))
        self.end_date = date_from_string(date_range.get('end'))

    def __eq__(self, other):
        if (not isinstance(other, self.__class__)):
            return False
        starts_equal = self.start_date == other.start_date
        ends_equal = self.end_date = other.end_date
        return starts_equal and ends_equal

    def _is_met(self, condition=None):
        """Checks to see if this constraint is met in the specified condition.
        Default condition is what we know about the current condition (i.e.
        date, time).

        This constraint will be met if the condition date is between
        self.start_date and self.end_date (inclusive).

        """
        condition = (datetime.datetime.now()
                     if condition is None else condition.data)
        condition_date = condition.date()

        has_started = condition_date >= self.start_date
        has_not_ended = condition_date <= self.end_date

        return has_started and has_not_ended


class ConstraintCondition():
    """Base class for constraint conditions."""
    def __init__(self, data):
        """Creates a new ConstraintCondition."""
        super().__init__()
        self.data = data


class DateTimeConstraintCondition(ConstraintCondition):
    """ConstraintCondition that represents a specific moment in time."""

    STR_FORMAT = '%Y-%m-%d %H:%M:%S'

    def __init__(self, data):
        """Creates a new DateTimeConstraintCondition."""
        if isinstance(data, str):
            try:
                data = datetime.datetime.fromtimestamp(float(data))
            except ValueError:
                try:
                    data = datetime.datetime.strptime(data, self.STR_FORMAT)
                except ValueError as e:
                    msg = ('Could not parse condition string to date (format '
                           'is YYYY-MM-DD HH:MM:SS): {data}')
                    msg = msg.format(data=data)
                    raise DateTimeConstraintConditionError(msg) from e

        elif isinstance(data, (list, tuple)):
            msg = ('Could not parse data to date, expected (datetime.date, '
                   'datetime.time) or (year, month, day, hour, minute, '
                   'second, [microsecond], [tzinfo]), found {data!r}')
            msg = msg.format(data=data)
            datalen = len(data)
            if datalen is 2:
                try:
                    data = datetime.datetime.combine(data[0], data[1])
                except TypeError as e:
                    msg = ('Could not parse data to date, expected '
                           '(datetime.date, datetime.time), found {data!r}')
                    msg = msg.format(data=data)
                    raise DateTimeConstraintConditionError(msg) from e
            elif datalen < 6 or datalen > 8:
                raise DateTimeConstraintConditionError(msg)
            elif datalen is 6:
                (year, month, day, hour, minute, second) = data
                try:
                    data = datetime.datetime(
                        year, month, day, hour, minute, second
                    )
                except ValueError as e:
                    raise DateTimeConstraintConditionError(msg) from e
            elif datalen is 7:
                (year, month, day, hour, minute, second, microsecond) = data
                try:
                    data = datetime.datetime(
                        year, month, day, hour, minute, second, microsecond
                    )
                except ValueError as e:
                    raise DateTimeConstraintConditionError(msg) from e
            elif datalen is 8:
                (year, month, day, hour, minute, second, microsecond,
                 tzinfo) = data
                try:
                    data = datetime.datetime(
                        year, month, day, hour, minute, second, microsecond,
                        tzinfo
                    )
                except ValueError as e:
                    raise DateTimeConstraintConditionError(msg) from e

        elif isinstance(data, (int, float)):
            data = datetime.datetime.fromtimestamp(data)

        elif isinstance(data, datetime.datetime):
            pass

        else:
            msg = "Couldn't parse data to datetime: {data}".format(data=data)
            DateTimeConstraintConditionError(msg)

        super().__init__(data)


class PriorityConstraintCondition(ConstraintCondition):
    """ConstraintCondition that represents a specific priority level."""
    def __init__(self, data):
        """Creates a new PriorityConstraintCondition."""
        if isinstance(data, int):
            try:
                data = PriorityConstraint.ALL_PRIORITIES[data]
            except IndexError as e:
                msg = 'Priority level out of range: {data}'.format(data=data)
                raise PriorityConstraintConditionError(msg) from e

        msg = "Couldn't parse data to priority level: {data}"
        msg = msg.format(data=data)
        try:
            tmp = data.lower()
        except AttributeError as e:
            raise PriorityConstraintConditionError(msg) from e
        if tmp.lower() in PriorityConstraint.ALL_PRIORITIES:
            data = tmp
        else:
            raise PriorityConstraintConditionError(msg)

        super().__init__(data)

    def __str__(self):
        return 'PriorityConstraintCondition(level={})'.format(self.data)
