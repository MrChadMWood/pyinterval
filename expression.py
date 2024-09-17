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
    Decade,
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
            raise ValueError(
                f"{__parent.unit.name} cannot be factored by {__unit.name}"
            )
        elif __parent and root_datetime is not None:
            raise ValueError("A root_datetime should be passed with the root.")

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
        self.operations_delta = relativedelta()

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
            raise ValueError(
                f"Cannot access child units before indexing {self.unit.name}."
            )

    def validate_index(self, index):
        """Validate the index value. For lazy chains, not during evaluation."""
        if not self.is_unit:
            current_element = (
                "root" if self.is_root else "scope" if self.is_scope else "unknown-type"
            )
            raise ValueError(f"Can not index a {current_element}. Must be a unit.")

        max_value = self.get_max_index()
        if not (-max_value - 1 <= index < max_value + 1):
            raise ValueError(
                f"{self.unit.name} cannot accept index {index} of {self.parent.unit.name} (max: {max_value - 1})"
            )

    def get_max_index(self):
        """Get max index for the unit."""
        if self.parent and self.parent.unit:
            return self.parent.unit.get_max_index(self.unit.name)
        else:
            raise IndexError(
                f"{self.unit.name} has no parent to fetch its maximum index from."
            )

    def get_scope(self):
        """Get the root scope for an expression."""
        current = self
        if current.is_root:
            raise ValueError("No scope has been defined.")

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
            raise AttributeError("Can only create timedelta from a scope.")
        return self.unit.delta(n)

    def __add__(self, other):
        """Handle addition of timedelta-like objects to create lazy expressions."""
        if self.is_root:
            raise ValueError("Must access a scope property to apply operations.")
        elif isinstance(other, relativedelta):
            # Returns copy of itself, not performing in-place changes
            new_expr = deepcopy(self)
            new_expr.operations_delta += other
            return new_expr
        elif isinstance(other, Expression):
            raise NotImplementedError(
                "Combining and breaking Expression chains is upcoming."
            )
        else:
            raise TypeError(
                f"Unsupported operand type(s) for +: 'Expression' and '{type(other).__name__}'"
            )

    def __radd__(self, other):
        """Right-hand addition, which just calls __add__ for now, while only timedelta supported."""
        return self.__add__(other)

    def __sub__(self, other):
        """Handle subtraction of timedelta-like objects to create lazy expressions."""
        if self.is_root:
            raise ValueError("Must access a scope property to apply operations.")
        elif isinstance(other, relativedelta):
            new_expr = deepcopy(self)
            new_expr.operations_delta -= other
            return new_expr
        elif isinstance(other, Expression):
            raise NotImplementedError(
                "Combining and breaking Expression chains is upcoming."
            )
        else:
            raise TypeError(
                f"Unsupported operand type(s) for -: 'Expression' and '{type(other).__name__}'"
            )

    def __rsub__(self, other):
        """Right-hand subtraction."""
        if self.is_root:
            raise ValueError("Must access a scope property to apply operations.")
        elif isinstance(other, Expression):
            raise NotImplementedError(
                "Combining and breaking Expression chains is upcoming."
            )
        else:
            raise NotImplementedError(
                "Can not subtract a relative time Expression from another object."
            )

    def __call__(self, dt=None, rollover=True, operation_safe=False):
        """Apply the expression to a date. Rollover controls whether to allow excess time to increment parent units."""
        dt = dt if dt is not None else self.get_root().datetime

        if not dt:
            raise ValueError("A datetime object is required.")
        elif isinstance(dt, type(datetime.date)) and not isinstance(
            dt, type(datetime.datetime)
        ):
            # Convert datetime.date to datetime.datetime (default to midnight)
            dt = datetime.datetime.combine(dt, datetime.time.min)
        elif not isinstance(dt, datetime.datetime):
            raise ValueError(f"datetime arg needs to be a datetime, not {type(dt)}")
        elif rollover and operation_safe:
            raise ValueError(
                "The operation_safe flag is only effective when rollover is disabled."
            )
        elif not self.is_scope and self.index is None:
            raise IndexError(
                f"All units must be indexed. {self.unit.name} missing index."
            )

        dt = self._reset_to_root_scope(dt)
        dt = self._apply_intervals(
            dt, rollover_allowed=rollover, operation_safe=operation_safe
        )
        return dt

    def _get_expression_chain(self):
        chain = []
        current = self
        while not current.is_root:
            chain.append(current)
            current = current.parent
        return reversed(chain)

    def _reset_to_root_scope(self, datetime):
        """Set time data in datetime to 0, up to root scope of expression."""
        current_scope = self.get_scope()
        return current_scope.unit.reset_scope(datetime)

    def _reset_to_unit_scope(self, datetime):
        """Set time data in datetime to 0, up to scope of unit."""
        return self.unit.reset_scope(datetime)

    @staticmethod
    def _get_index_delta(interval):
        if interval.index >= 0:
            # 0-based indexing
            adjustment = interval.index + 1
            # Accounts for variance in min possible time (e.g., second: 0, day: 1)
            adjustment -= interval.unit.scope_reset_residual
            return interval.unit.delta(adjustment)
        else:
            # parent delta of 1 + (negative) child delta of index = delta to apply
            return interval.parent.unit.delta(1) + interval.unit.delta(interval.index)

    def _apply_intervals(self, dt, rollover_allowed, operation_safe):
        """Apply all intervals recursively, with or without rollover based on the flag."""

        # Checks if parent unit value is different from provided value
        def check_for_rollover(interval, last_parent_value):
            if last_parent_value != interval.parent.unit.value(dt):
                raise IndexError(
                    f"Rollover occurred for {interval.parent.unit.name} from {last_parent_value}"
                    f" to {interval.parent.unit.value(dt)}."
                )

        # Get expression chain in unit descending order, from scope
        chain = self._get_expression_chain()

        # Iter the expression chain from largest to smallest interval
        for interval in chain:
            # Reset datetime to precision of the current interval
            dt = interval._reset_to_unit_scope(dt)

            if interval.is_scope:
                # Initialize for first evaluation against expression scope
                last_unit_value = interval.unit.value(dt)
                dt += interval.operations_delta
                # Skips unnecessary rollover check
                continue
            else:
                # Increments datetime by index
                delta = self._get_index_delta(interval)
                dt += delta

            if rollover_allowed:
                dt += interval.operations_delta
            elif operation_safe:
                check_for_rollover(interval, last_unit_value)
                dt += interval.operations_delta
                # Resets for next loops rollover check
                last_unit_value = interval.unit.value(dt)
            else:
                dt += interval.operations_delta
                check_for_rollover(interval, last_unit_value)
                # Resets for next loops rollover check
                last_unit_value = interval.unit.value(dt)

        return dt

    def __repr__(self):
        chain = self._get_expression_chain()
        parts = []

        for interval in chain:
            unit_name = interval.unit.name

            index_str = f""
            if interval.index is not None:
                index = interval.index + 1 if interval.index >= 0 else interval.index
                index_str = f"[{index}]"

            interval_str = f"{unit_name}{index_str}"
            if interval.operations_delta:
                interval_str = f"{interval_str} + {interval.operations_delta}"

            parts.append(interval_str)

        return " > ".join(parts)

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
