from dateutil.relativedelta import relativedelta
import datetime


class Unit:
    """
    Base class for time units. Subclasses represent units of time.
    The `meta` dictionary defines the parameters for each subclass.
    """

    meta = {
        'enum': None,
        'name': None,
        'relativedelta_kwarg': None,
        'relativedelta_multiplier': 1,
        'datetime_kwarg': None,
        'parent_class': None,
        'max_intervals': None
    }

    def __init__(self):
        self.enum = self.meta['enum']
        self.name = self.meta['name']
        self.relativedelta_kwarg = self.meta['relativedelta_kwarg']
        self.relativedelta_multiplier = self.meta['relativedelta_multiplier']
        self.datetime_kwarg = self.meta['datetime_kwarg']
        self.max_intervals = self.meta['max_intervals']

    def get_max_index(self, child_unit):
        """Get max index for a child unit."""
        return self.max_intervals.get(child_unit)

    def delta(self, value=1):
        """Create a relativedelta."""
        delta_kwargs = {self.relativedelta_kwarg: value * self.relativedelta_multiplier}
        return relativedelta(**delta_kwargs)

    def reset_scope(self, date, replace_kwargs=None):
        """Reset time data based on granularity of the unit."""
        replace_kwargs = replace_kwargs or {}
        return date.replace(**replace_kwargs)


# Define the units with specific meta data
class Microsecond(Unit):
    meta = {
        'enum': 0,
        'name': 'Microsecond',
        'relativedelta_kwarg': 'microseconds',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'microsecond',
        'parent_class': None,
        'max_intervals': {}
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'microsecond': 0})


class Millisecond(Unit):
    meta = {
        'enum': 0.1,
        'name': 'Millisecond',
        'relativedelta_kwarg': 'microseconds',
        'relativedelta_multiplier': 1000,
        'datetime_kwarg': 'microsecond',
        'parent_class': Microsecond,
        'max_intervals': {Microsecond.meta['name']: 1000}
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'microsecond': (date.microsecond // self.relativedelta_multiplier) * self.relativedelta_multiplier})


class Centisecond(Unit):
    meta = {
        'enum': 0.2,
        'name': 'Centisecond',
        'relativedelta_kwarg': 'microseconds',
        'relativedelta_multiplier': 10000,
        'datetime_kwarg': 'microsecond',
        'parent_class': Millisecond,
        'max_intervals': {
            Microsecond.meta['name']: 10000, 
            Millisecond.meta['name']: 10
        }
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'microsecond': (date.microsecond // self.relativedelta_multiplier) * self.relativedelta_multiplier})


class Decisecond(Unit):
    meta = {
        'enum': 0.3,
        'name': 'Decisecond',
        'relativedelta_kwarg': 'milliseconds',
        'relativedelta_multiplier': 100000,
        'datetime_kwarg': 'microsecond',
        'parent_class': Centisecond,
        'max_intervals': {
            Microsecond.meta['name']: 100000, 
            Millisecond.meta['name']: 100, 
            Centisecond.meta['name']: 10
        }
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'microsecond': (date.microsecond // self.relativedelta_multiplier) * self.relativedelta_multiplier})


class Second(Unit):
    meta = {
        'enum': 1,
        'name': 'Second',
        'relativedelta_kwarg': 'seconds',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'second',
        'parent_class': Decisecond,
        'max_intervals': {
            Microsecond.meta['name']: 1000000,
            Millisecond.meta['name']: 1000,
            Centisecond.meta['name']: 100,
            Decisecond.meta['name']: 10
        }
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'microsecond': 0})


class Minute(Unit):
    meta = {
        'enum': 2,
        'name': 'Minute',
        'relativedelta_kwarg': 'minutes',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'minute',
        'parent_class': Second,
        'max_intervals': {
            Microsecond.meta['name']: 60000000,
            Millisecond.meta['name']: 60000,
            Centisecond.meta['name']: 6000,
            Decisecond.meta['name']: 600,
            Second.meta['name']: 60
        }
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'second': 0, 'microsecond': 0})


class Hour(Unit):
    meta = {
        'enum': 3,
        'name': 'Hour',
        'relativedelta_kwarg': 'hours',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'hour',
        'parent_class': Minute,
        'max_intervals': {
            Microsecond.meta['name']: 3600000000,
            Millisecond.meta['name']: 3600000,
            Centisecond.meta['name']: 360000,
            Decisecond.meta['name']: 36000,
            Second.meta['name']: 3600,
            Minute.meta['name']: 60
        }
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'minute': 0, 'second': 0, 'microsecond': 0})


class Day(Unit):
    meta = {
        'enum': 4,
        'name': 'Day',
        'relativedelta_kwarg': 'days',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'day',
        'parent_class': Hour,
        'max_intervals': {
            Microsecond.meta['name']: 86400000000,
            Millisecond.meta['name']: 86400000,
            Centisecond.meta['name']: 8640000,
            Decisecond.meta['name']: 864000,
            Second.meta['name']: 86400,
            Minute.meta['name']: 1440,
            Hour.meta['name']: 24
        }
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0})


class Week(Unit):
    meta = {
        'enum': 5,
        'name': 'Week',
        'relativedelta_kwarg': 'weeks',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'day',
        'parent_class': Day,
        'max_intervals': {
            Microsecond.meta['name']: 604800000000,
            Millisecond.meta['name']: 604800000,
            Centisecond.meta['name']: 60480000,
            Decisecond.meta['name']: 6048000,
            Second.meta['name']: 604800,
            Minute.meta['name']: 10080,
            Hour.meta['name']: 168,
            Day.meta['name']: 7
        }
    }

    def reset_scope(self, date):
        # Reset to the start of the week (Monday)
        start_of_week = date - datetime.timedelta(days=date.weekday())
        return super().reset_scope(start_of_week, {'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0})


class Month(Unit):
    meta = {
        'enum': 6,
        'name': 'Month',
        'relativedelta_kwarg': 'months',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'month',
        'parent_class': Week,
        'max_intervals': {
            Microsecond.meta['name']: 3024000000000,
            Millisecond.meta['name']: 3024000000,
            Centisecond.meta['name']: 302400000,
            Decisecond.meta['name']: 30240000,
            Second.meta['name']: 3024000,
            Minute.meta['name']: 50400,
            Hour.meta['name']: 840,
            Day.meta['name']: 35,
            Week.meta['name']: 5
        }
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'day': 1, 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0})


class Quarter(Unit):
    meta = {
        'enum': 7,
        'name': 'Quarter',
        'relativedelta_kwarg': 'months',
        'relativedelta_multiplier': 3,
        'datetime_kwarg': 'month',
        'parent_class': Month,
        'max_intervals': {
            Microsecond.meta['name']: 8467200000000,
            Millisecond.meta['name']: 8467200000,
            Centisecond.meta['name']: 846720000,
            Decisecond.meta['name']: 84672000,
            Second.meta['name']: 8467200,
            Minute.meta['name']: 141120,
            Hour.meta['name']: 2352,
            Day.meta['name']: 98,
            Week.meta['name']: 14,
            Month.meta['name']: 3
        }
    }

    def reset_scope(self, date):
        start_month = self.relativedelta_multiplier * ((date.month - 1) // self.relativedelta_multiplier) + 1
        return super().reset_scope(date, {'month': start_month, 'day': 1, 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0})


class Year(Unit):
    meta = {
        'enum': 8,
        'name': 'Year',
        'relativedelta_kwarg': 'years',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'year',
        'parent_class': Quarter,
        'max_intervals': {
            Microsecond.meta['name']: 32054400000000,
            Millisecond.meta['name']: 32054400000,
            Centisecond.meta['name']: 3205440000,
            Decisecond.meta['name']: 320544000,
            Second.meta['name']: 32054400,
            Minute.meta['name']: 534240,
            Hour.meta['name']: 8904,
            Day.meta['name']: 366,
            Week.meta['name']: 53,
            Month.meta['name']: 12,
            Quarter.meta['name']: 4
        }
    }

    def reset_scope(self, date):
        return super().reset_scope(date, {'month': 1, 'day': 1, 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0})


class Decade(Unit):
    meta = {
        'enum': 9,
        'name': 'Decade',
        'relativedelta_kwarg': 'years',
        'relativedelta_multiplier': 10,
        'datetime_kwarg': 'year',
        'parent_class': Year,
        'max_intervals': {
            Microsecond.meta['name']: 320544000000000,
            Millisecond.meta['name']: 320544000000,
            Centisecond.meta['name']: 32054400000,
            Decisecond.meta['name']: 3205440000,
            Second.meta['name']: 320544000,
            Minute.meta['name']: 5342400,
            Hour.meta['name']: 89040,
            Day.meta['name']: 3710,
            Week.meta['name']: 530,
            Month.meta['name']: 120,
            Quarter.meta['name']: 40,
            Year.meta['name']: 10 
        }
    }

    def reset_scope(self, date):
        start_year = (date.year // self.relativedelta_multiplier) * self.relativedelta_multiplier
        return super().reset_scope(date, {'year': start_year, 'month': 1, 'day': 1, 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0})

# Expression class to handle chaining and managing units
class Expression:
    """
    Chain and manage units.

    Example usage:
        ```
        today = someday = datetime.datetime.now()
        
        # Get the current week, Monday 
        this_monday_exp = Expression(today).week.day[0]
        this_monday_exp()
        
        # Get a weekday dynamically
        exp = Expression()
        some_monday_exp = exp.week.day[0]
        some_monday = some_monday_exp(someday)
        
        # Add some time
        some_monday + exp.decade(n=1)
        
        # Subtract some time
        some_monday - exp.centisecond(n=20)
        
        # Get more granular
        more_granular_exp = exp.day.hour[-4].second[573].millisecond[-12].microsecond[5]
        more_granular_time = more_granular_exp(some_monday)
        ```

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

    def __call__(self, datetime=None, n=None, rollover=True):
        """Apply the expression to a date. Rollover controls whether to allow excess time to increment parent units.
        If called on a scope with n, it generates a timedelta with value=n matching the scope.
        """
        
        datetime = datetime if datetime is not None else self.get_root().datetime

        if not datetime and not self.is_scope:
            # Requires a datetime when evaluating a relative expression
            raise ValueError('A datetime object is required when evaluating an expression.')
        elif n is None and isinstance(datetime, int):
            # Catches accidental use of n as a positional, inadvertently assigning to datetime.
            raise ValueError('The `n` kwarg is required when generating a timedelta.')
        elif n is not None and self.is_scope:
            # When generating a relativedelta
            return self.unit.delta(n)
        else:
            # When evaluating relative expressions
            datetime = self._reset_to_scope(datetime)
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
    def decade(self):
        self.validate_scheme()
        return Expression(unit=Decade(), parent=self)

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

    @property
    def decisecond(self):
        self.validate_scheme()
        return Expression(unit=Decisecond(), parent=self)

    @property
    def centisecond(self):
        self.validate_scheme()
        return Expression(unit=Centisecond(), parent=self)

    @property
    def millisecond(self):
        self.validate_scheme()
        return Expression(unit=Millisecond(), parent=self)

    @property
    def microsecond(self):
        self.validate_scheme()
        return Expression(unit=Microsecond(), parent=self)
        