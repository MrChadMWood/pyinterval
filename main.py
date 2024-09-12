from dateutil.relativedelta import relativedelta
import datetime


class Unit:
    """
    Base class for time units. Subclasses represent units of time.
    This class is not intended to be interacted with directly, nor its subclasses.
    Rather, the Expression class offers a proxy to each subclass. This is the intended entrypoint.
    The Expression class provides abstraction via property and bracket indexing.

    Args:
        enum (int): Unit identifier. Used to compare position in hierarchy.
        name (str): Name of the unit. Used as an id and for __repr__.
        relativedelta_kwarg (str): Keyword for relativedelta. Used for calculating timedelta.
        datetime_kwarg (str): Keyword for datetime operations. Used for compiling datetime objects.
        max_intervals (dict): Max intervals for child units. Used for weak validation.
    """
    def __init__(self, enum, name, relativedelta_kwarg, datetime_kwarg, max_intervals):
        self.enum = enum
        self.name = name
        self.relativedelta_kwarg = relativedelta_kwarg
        self.datetime_kwarg = datetime_kwarg
        self.max_intervals = max_intervals or {}

    def get_max_index(self, child_unit):
        """Get max index for a child unit."""
        return self.max_intervals.get(child_unit)

    def reset_scope(self, date):
        """Remove any time after granularity of self. To be implemented by subclasses"""
        raise NotImplementedError

    def delta(self, value = 1):
        """Create a relativedelta."""
        delta_kwargs = {self.relativedelta_kwarg: value}
        return relativedelta(**delta_kwargs)

class Microsecond(Unit):
    ENUM = 0
    NAME = 'Microsecond'
    RELATIVEDELTA_KWARG = 'microseconds'
    DATETIME_KWARG = 'microsecond'
    MAX_INTERVALS = {}
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        return date.replace(microsecond=0)

class Second(Unit):
    ENUM = 1
    NAME = 'Second'
    RELATIVEDELTA_KWARG = 'seconds'
    DATETIME_KWARG = 'second'
    MAX_INTERVALS = {Microsecond: 1000000}
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        return date.replace(microsecond=0)

class Minute(Unit):
    ENUM = 2
    NAME = 'Minute'
    RELATIVEDELTA_KWARG = 'minutes'
    DATETIME_KWARG = 'minute'
    MAX_INTERVALS = {
        Microsecond.NAME: 60000000, 
        Second.NAME: 60
    }
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        return date.replace(second=0, microsecond=0)

class Hour(Unit):
    ENUM = 3
    NAME = 'Hour'
    RELATIVEDELTA_KWARG = 'hours'
    DATETIME_KWARG = 'hour'
    MAX_INTERVALS = {
        Microsecond.NAME: 3600000000, 
        Second.NAME: 3600, 
        Minute.NAME: 60
    }
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        return date.replace(minute=0, second=0, microsecond=0)

class Day(Unit):
    ENUM = 4
    NAME = 'Day'
    RELATIVEDELTA_KWARG = 'days'
    DATETIME_KWARG = 'day'
    MAX_INTERVALS = {
        Microsecond.NAME: 86400000000, 
        Second.NAME: 86400, 
        Minute.NAME: 1440, 
        Hour.NAME: 24
    }
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        return date.replace(hour=0, minute=0, second=0, microsecond=0)

class Week(Unit):
    ENUM = 5
    NAME = 'Week'
    RELATIVEDELTA_KWARG = 'weeks'
    DATETIME_KWARG = 'day'
    MAX_INTERVALS = {
        Microsecond.NAME: 604800000000, 
        Second.NAME: 604800, 
        Minute.NAME: 10080, 
        Hour.NAME: 168, 
        Day.NAME: 7
    }
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        # Reset to the start of the week (weekday=0 represents Monday)
        # Consider updating to allow different days of week
        start_of_week = date - datetime.timedelta(days=date.weekday())
        return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

class Month(Unit):
    ENUM = 6
    NAME = 'Month'
    RELATIVEDELTA_KWARG = 'months'
    DATETIME_KWARG = 'month'
    MAX_INTERVALS = {
        Microsecond.NAME: 2678400000000, 
        Second.NAME: 2592000, 
        Minute.NAME: 43200, 
        Hour.NAME: 720, 
        Day.NAME: 31, 
        Week.NAME: 5
    }
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

class Quarter(Unit):
    ENUM = 7
    NAME = 'Quarter'
    RELATIVEDELTA_KWARG = 'months'
    DATETIME_KWARG = 'month'
    MAX_INTERVALS = {
        Microsecond.NAME: 7776000000000, 
        Second.NAME: 7776000, 
        Minute.NAME: 129600, 
        Hour.NAME: 2160, 
        Day.NAME: 90, 
        Week.NAME: 14, 
        Month.NAME: 3
    }
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        start_month = 3 * ((date.month - 1) // 3) + 1
        return date.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)

class Year(Unit):
    ENUM = 8
    NAME = 'Year'
    RELATIVEDELTA_KWARG = 'years'
    DATETIME_KWARG = 'year'
    MAX_INTERVALS = {
        Microsecond.NAME: 31622400000000, 
        Second.NAME: 31536000, 
        Minute.NAME: 525600, 
        Hour.NAME: 8760, 
        Day.NAME: 366, 
        Week.NAME: 52, 
        Month.NAME: 12,
        Quarter.NAME: 4
    }
    def __init__(self):
        super().__init__(self.ENUM, self.NAME, self.RELATIVEDELTA_KWARG, self.DATETIME_KWARG, self.MAX_INTERVALS)

    def reset_scope(self, date):
        return date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


# Expression class to handle chaining and managing units
class Expression:
    """
    Chain and manage units.

    Example usage:
        exp = Expression()
        
        # Get the current week, Monday 
        this_monday = exp(today).week.day[0]

    Args:
        Optional. Required if datetime not supplied when the expression is evaluated.
            root_datetime (datetime.datetime): Initial datetime.
        Handled automatically, not passed by user.
            unit (Unit): The Unit in this part of the expression
            parent (Expression): The parent unit of this part of the expression
    """
    def __init__(self, root_datetime=None, unit=None, parent=None):
        is_scope = False
        if parent and parent.unit:
            if parent.unit.enum <= unit.enum:
                raise ValueError(f'{parent.unit.name} cannot be factored by {unit.name}')
        elif unit:
            is_scope = True
        else:
            is_scope = None

        self.unit = unit
        self.parent = parent
        self.index = None
        self.is_scope = is_scope
        self.datetime = root_datetime

    def __getitem__(self, index):
        """Index the expression."""
        self.validate_index(index)
        self.index = index
        return self

    def validate_scheme(self):
        """Ensure parent unit is indexed before accessing child units."""
        if self.is_scope is None:
            return
        elif not self.is_scope and self.index is None:
            raise ValueError(f"Cannot access child units before indexing {self.unit.name}.")

    def validate_index(self, index):
        """Validate the index value. For lazy chains, not during evaluation."""
        if index is None or self.parent is None:
            return
        max_value = self.get_max_index()
        if not (-max_value - 1 <= index < max_value + 1):
            raise ValueError(f"{self.unit.name} cannot accept index {index} of {self.parent.unit.name} (max: {max_value - 1})")

    def get_max_index(self):
        """Get max index for the unit."""
        if self.parent and self.parent.unit:
            return self.parent.unit.get_max_index(self.unit.name)
        else:
            raise IndexError('Cannot index a scope.')

    def get_scope(self):
        """Get the root scope for an expression."""
        scope = self
        while scope.is_scope == False:
            scope = scope.parent
        if scope.is_scope == None:
            raise ValueError('No scope has been defined.')
        return scope

    def get_root(self):
        """Get the root object for an expression."""
        scope = self
        while scope.is_scope != None:
            scope = scope.parent
        return scope

    def __call__(self, datetime=None, rollover=True):
        """Apply the expression to a date. Rollover controls whether to allow excess time to increment parent units."""
        datetime = datetime or self.get_root().datetime
        if not datetime:
            raise ValueError('A datetime object is required.')
        
        if self.is_scope: # When generating a relativedelta
            raise NotImplementedError('Initializing scopes for timedeltas is upcoming.')
        else: # When evaluating relative expressions
            datetime = self._reset_to_scope(dadatetimee)
            if rollover:
                datetime = self._apply_intervals_with_rollover(datetime)
            else:
                datetime = self._apply_intervals_without_rollover(datetime)
        return datetime

    def _reset_to_scope(self, datetime):
        """Set time data in datetime to 0, up to scope of expression."""
        current_scope = self.get_scope()
        return current_scope.unit.reset_scope(datetime)

    def _apply_intervals_with_rollover(self, datetime):
        """Apply all intervals (year, quarter, month, etc.) recursively with default rollover behavior."""
        adjustments = []
        current = self
        while not current.is_scope:
            if current.index >= 0:
                adjustments.append(current.unit.delta(current.index))        
            else:
                # parent delta of 1 + (negative) child delta of index = delta to apply
                adjustments.append(current.parent.unit.delta(1) + current.unit.delta(current.index))
            current = current.parent

        # Applied in reverse order to preserve logic
        for adjustment in reversed(adjustments):
            datetime += adjustment
            
        return datetime

    def _apply_intervals_without_rollover(self, _datetime):
        """Apply intervals without allowing rollover."""
        adjustments = {
            'year': _datetime.year,
            'month': _datetime.month,
            'day': _datetime.day,
            'hour': _datetime.hour,
            'minute': _datetime.minute,
            'second': _datetime.second,
            'microsecond': _datetime.microsecond
        }

        current = self
        while not current.is_scope:
            current_adjustment = current.unit.datetime_kwarg
            if current_adjustment not in adjustments:
                raise ValueError(f"Invalid unit '{current_adjustment}' in expression.")
                
            if current.index >= 0:
                adjustments[current_adjustment] += current.index
            else:
                # Move the datetime to the parent boundary and add one
                boundary_date = current.parent.unit.reset_scope(_datetime)
                boundary_date += current.parent.unit.delta( current.parent.index + 1)
                # Then add the correct amount from the (negative) child unit
                serrogate_date = boundary_date + current.unit.delta(current.index)
                # Extract its value and add to the adjustments
                adjustments[current_adjustment] = getattr(serrogate_date, current_adjustment)
                
            current = current.parent

        # Try to construct the date without rollover
        try:
            return datetime.datetime(**adjustments)
        except ValueError as e:
            raise ValueError(f"Invalid date when applying adjustments: {str(e)}")

    def __repr__(self):
        parts = []
        current = self

        # Traverse up the chain to build the representation
        while current:
            unit_name = current.unit.name if current.unit else 'Root'
            index_str = f"[{current.index + 1}]" if current.index is not None else ''
            parts.append(f'{unit_name}{index_str}')
            if current.is_scope:
                current = None
            else:
                current = current.parent

        return ' > '.join(reversed(parts))

    @property
    def year(self):
        self.validate_scheme()
        return Expression(unit=Year(), parent=self)

    @property
    def quarter(self):
        self.validate_scheme()
        return Expression(unit=Quarter(), parent=self)

    @property
    def month(self):
        self.validate_scheme()
        return Expression(unit=Month(), parent=self)

    @property
    def week(self):
        self.validate_scheme()
        return Expression(unit=Week(), parent=self)

    @property
    def day(self):
        self.validate_scheme()
        return Expression(unit=Day(), parent=self)

    @property
    def hour(self):
        self.validate_scheme()
        return Expression(unit=Hour(), parent=self)

    @property
    def minute(self):
        self.validate_scheme()
        return Expression(unit=Minute(), parent=self)

    @property
    def second(self):
        self.validate_scheme()
        return Expression(unit=Second(), parent=self)