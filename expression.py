from dateutil.relativedelta import relativedelta
import datetime
from copy import deepcopy
from .src._units import (
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
        elif __parent and root_datetime is not None:
            raise ValueError('A root_datetime should be passed with the root.')
        
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
        self.delta_queue = []

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
        if not self.is_unit:
            current_element = 'root' if self.is_root else 'scope' if self.is_scope else 'unknown-type'
            raise ValueError(f'Can not index a {current_element}. Must be a unit.')

        max_value = self.get_max_index()
        if not (-max_value - 1 <= index < max_value + 1):
            raise ValueError(f"{self.unit.name} cannot accept index {index} of {self.parent.unit.name} (max: {max_value - 1})")

    def get_max_index(self):
        """Get max index for the unit."""
        if self.parent and self.parent.unit:
            return self.parent.unit.get_max_index(self.unit.name)
        else:
            raise IndexError(f'{self.unit.name} has no parent to fetch its maximum index from.')

    def get_scope(self):
        """Get the root scope for an expression."""
        current = self
        if current.is_root:
            raise ValueError('No scope has been defined.')

        while not current.is_scope:
            current = current.parent

        return current

    def get_root(self):
        """Get the root object for an expression."""
        current = self
        while not current.is_root:
            current = current.parent
        return current

    def n(self, n: int | float):
        if not self.is_scope:
            raise AttributeError('Can only create timedelta from a scope.')
        return self.unit.delta(n)

    def __add__(self, other):
        """Handle addition of timedelta-like objects to create lazy expressions."""
        if isinstance(other, relativedelta):
            # Returns copy of itself, not performing in-place changes
            new_expr = deepcopy(self)
            new_expr.delta_queue.append(other)
            return new_expr
        elif isinstance(other, Expression):
            raise NotImplementedError('Combining and breaking Expression chains is upcoming.')
        else:
            raise TypeError(f"Unsupported operand type(s) for +: 'Expression' and '{type(other).__name__}'")

    def __radd__(self, other):
        """Right-hand addition, which just calls __add__ for now, while only timedelta supported."""
        return self.__add__(other)

    def __sub__(self, other):
        """Handle subtraction of timedelta-like objects to create lazy expressions."""
        if isinstance(other, relativedelta):
            # Negate the relativedelta to handle subtraction as addition of a negative
            # Prevents need of maintaining an additional queue for seperate operation types
            negated_delta = -other
            new_expr = deepcopy(self)
            new_expr.delta_queue.append(negated_delta)
            return new_expr
        elif isinstance(other, Expression):
            raise NotImplementedError('Combining and breaking Expression chains is upcoming.')
        else:
            raise TypeError(f"Unsupported operand type(s) for -: 'Expression' and '{type(other).__name__}'")

    def __rsub__(self, other):
        """Right-hand subtraction."""
        if isinstance(other, Expression):
            raise NotImplementedError('Combining and breaking Expression chains is upcoming.')
        else:
            raise NotImplementedError('Can not subtract a relative time Expression from another object.')

    def apply_deltas(self, dt):
        """Apply all deltas in the queue to the given datetime."""
        for delta in self.delta_queue:
            dt += delta
        return dt

    def __call__(self, dt=None, rollover=True):
        """Apply the expression to a date. Rollover controls whether to allow excess time to increment parent units."""    
        dt = dt if dt is not None else self.get_root().datetime

        if not dt:
            raise ValueError('A datetime object is required.')
        elif isinstance(dt, type(datetime.date)) and not isinstance(dt, type(datetime.datetime)):
            # Convert datetime.date to datetime.datetime (default to midnight)
            dt = datetime.datetime.combine(dt, datetime.time.min)
        elif not isinstance(dt, datetime.datetime):
            raise ValueError(f'datetime arg needs to be a datetime, not {type(dt)}')
            
        dt = self._reset_to_root_scope(dt)
        if rollover:
            dt = self._apply_intervals_with_rollover(dt)
        else:
            dt = self._apply_intervals_without_rollover(dt)

        return dt

    def _reset_to_root_scope(self, datetime):
        """Set time data in datetime to 0, up to root scope of expression."""
        current_scope = self.get_scope()
        return current_scope.unit.reset_scope(datetime)

    def _reset_to_unit_scope(self, datetime):
        """Set time data in datetime to 0, up to scope of unit."""
        return self.unit.reset_scope(datetime)

    def _apply_intervals_with_rollover(self, datetime):
        """Apply all intervals (year, quarter, month, etc.) recursively with default rollover behavior.
        
        TODO: Performance can be improved here. It should be possible to logically determine which
        explicit_deltas need to be ignored, rather than applying all and resetting scope for each unit.

        Any explicit_delta that defines a value for a unit which is smaller than the current AND is also 
        part of the expression chain, should be able to be safely ignored. Adding the remaining deltas should
        provide the same result.
        """
        adjustments = {} # Relies of preservation of insertion order.
        current = self
        while not current.is_scope:
            unit = current.unit.name
            adjustments[unit] = {'reset_scope_func': current.parent._reset_to_unit_scope}

            if current.index >= 0:
                adj_timedelta = current.unit.delta(current.index + 1)   
            else:
                # parent delta of 1 + (negative) child delta of index = delta to apply
                adj_timedelta = current.parent.unit.delta(1) + current.unit.delta(current.index)
            
            adjustments[unit].update({
                'index_delta': adj_timedelta,
                'explicit_deltas': current.delta_queue
            })
            
            current = current.parent

        # Applied in reverse order to preserve logic
        for adj in reversed(adjustments):
            adjustment = adjustments[adj]
            # Resets scope at each unit, allowing [index] to override
            # any prior arithmetic operations
            datetime = adjustment['reset_scope_func'](datetime)
            datetime += adjustment['index_delta']
            # Applies any new arithmetic operations
            for delta in adjustment['explicit_deltas']:
                datetime += delta

        return datetime

    def _apply_intervals_without_rollover(self, _datetime):
        """Apply intervals without allowing rollover."""
        def _build_adjustments(dt):
            return {
                'year': dt.year,
                'month': dt.month,
                'day': dt.day,
                'hour': dt.hour,
                'minute': dt.minute,
                'second': dt.second,
                'microsecond': dt.microsecond
            }

        adjustments = _build_adjustments(_datetime)
        current = self

        while not current.is_scope:
            current_adjustment = current.unit.datetime_kwarg

            # Validations
            if current_adjustment not in adjustments:
                raise ValueError(f"Invalid unit '{current_adjustment}' in expression.")
            elif current.delta_queue:
                raise NotImplementedError('Can not perform arithmetic without rollover yet.')
            
            # Handling for 0-based indexing
            if current.index >= 0:
                adjustments[current_adjustment] = current.index + 1
            else:
                # Move the datetime to the parent boundary and add one
                boundary_date = current.parent.unit.reset_scope(_datetime)
                boundary_date += current.parent.unit.delta( current.parent.index)
                # Then add the correct amount from the (negative) child unit
                serrogate_date = boundary_date + current.unit.delta(current.index)
                # Extract its value and add to the adjustments
                adjustments[current_adjustment] = getattr(serrogate_date, current_adjustment)
            
            # Extend adjustments by any lazy-evaluated arithmetic
            current = current.parent

        # Try to construct the date without rollover
        try:
            dt = datetime.datetime(**adjustments)
        except ValueError as e:
            raise ValueError(f"Invalid date when applying adjustments: {str(e)}")
        else:
            return dt

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
        