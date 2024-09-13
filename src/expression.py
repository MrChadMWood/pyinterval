from dateutil.relativedelta import relativedelta
import datetime
from ._units import (
    Microsecond,
    Millisecond,
    Centisecond,
    Decisecond,
    Second,
    Minute,
    Hour,
    Day,
    Week,
    Month,
    Quarter,
    Year,
    Decade
)

# Expression class to handle chaining and managing units
class Expression:
    """
    Chain and manage units of time.

    Args:

        Optional. Required if datetime not supplied when the expression is evaluated.
            root_datetime (datetime.datetime): Initial datetime.

        Handled automatically, not passed by user.
            __unit (Unit): The Unit in this part of the expression
            __parent (Expression): The parent unit of this part of the expression
    """
    def __init__(self, root_datetime=None, *, __unit=None, __parent=None):
        if __parent and __parent.unit and __parent.unit.enum <= __unit.enum:
            raise ValueError(f'{__parent.unit.name} cannot be factored by {__unit.name}')
        
        # Determining which part of expression `self` is
        self.is_root = self.is_scope = self.is_unit = False
        if not __parent:
            self.is_root = True
        elif __parent.is_root:
            self.is_scope = True
        else:
            self.is_unit = True

        self.unit = __unit
        self.parent = __parent
        self.index = None
        self.datetime = root_datetime

    def __getitem__(self, index):
        """Index the expression."""
        self.validate_index(index)
        self.index = index
        return self

    def validate_scheme(self):
        """Ensure parent unit is indexed before accessing child units."""
        if self.is_root or self.is_scope:
            return
        elif self.index is None:
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

    def n(self, n: int | float):
        if not self.is_scope:
            raise AttributeError('Can only create timedelta from a scope.')
        return self.unit.delta(n)

    def __call__(self, datetime=None, rollover=True):
        """Apply the expression to a date. Rollover controls whether to allow excess time to increment parent units."""
        
        datetime = datetime if datetime is not None else self.get_root().datetime
        if not datetime:
            raise ValueError('A datetime object is required.')

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
        while not current.is_root:
            unit_name = current.unit.name if current.unit else 'Root'
            index_str = f"[{current.index + 1}]" if current.index is not None else ''
            parts.append(f'{unit_name}{index_str}')
            current = current.parent

        return ' > '.join(reversed(parts))

    @property
    def decade(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Decade(), _Expression__parent=self)

    @property
    def year(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Year(), _Expression__parent=self)

    @property
    def quarter(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Quarter(), _Expression__parent=self)

    @property
    def month(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Month(), _Expression__parent=self)

    @property
    def week(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Week(), _Expression__parent=self)

    @property
    def day(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Day(), _Expression__parent=self)

    @property
    def hour(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Hour(), _Expression__parent=self)

    @property
    def minute(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Minute(), _Expression__parent=self)

    @property
    def second(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Second(), _Expression__parent=self)

    @property
    def decisecond(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Decisecond(), _Expression__parent=self)

    @property
    def centisecond(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Centisecond(), _Expression__parent=self)

    @property
    def millisecond(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Millisecond(), _Expression__parent=self)

    @property
    def microsecond(self):
        self.validate_scheme()
        return Expression(_Expression__unit=Microsecond(), _Expression__parent=self)
        