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
        self.carry_residual_time = self.meta['carry_residual_time']

    def get_max_index(self, child_unit):
        """Get max index for a child unit."""
        return self.max_intervals.get(child_unit)

    def delta(self, value=1):
        """Create a relativedelta."""
        delta_kwargs = {self.relativedelta_kwarg: value * self.relativedelta_multiplier}
        return relativedelta(**delta_kwargs)

    def reset_scope(self, date, replace_kwargs):
        """Reset time data based on granularity of the unit."""
        return date.replace(**replace_kwargs)

class Microsecond(Unit):
    meta = {
        'enum': 0,
        'name': 'Microsecond',
        'relativedelta_kwarg': 'microseconds',
        'relativedelta_multiplier': 1,
        'datetime_kwarg': 'microsecond',
        'parent_class': None,
        'max_intervals': {},
        'carry_residual_time': True
    }

    def reset_scope(self, date):
        microsecond_part = date.microsecond % 1000  # Keep residual microseconds (the last 3 digits)
        new_microsecond_value = (date.microsecond // 1000) * 1000 + microsecond_part
        return super().reset_scope(date, {'microsecond': new_microsecond_value})


class Millisecond(Unit):
    meta = {
        'enum': 0.1,
        'name': 'Millisecond',
        'relativedelta_kwarg': 'microseconds',
        'relativedelta_multiplier': 1000,
        'datetime_kwarg': 'microsecond',
        'parent_class': Microsecond,
        'max_intervals': {Microsecond.meta['name']: 1000},
        'carry_residual_time': True
    }

    def reset_scope(self, date):
        # Reset the microseconds, keep only millisecond portion
        new_microsecond_value = (date.microsecond // 1000) * 1000
        return super().reset_scope(date, {'microsecond': new_microsecond_value})


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
        },
        'carry_residual_time': True
    }

    def reset_scope(self, date):
        # Reset microseconds and milliseconds, keep only centisecond portion
        new_microsecond_value = (date.microsecond // 10000) * 10000
        return super().reset_scope(date, {'microsecond': new_microsecond_value})


class Decisecond(Unit):
    meta = {
        'enum': 0.3,
        'name': 'Decisecond',
        'relativedelta_kwarg': 'microseconds',
        'relativedelta_multiplier': 100000,
        'datetime_kwarg': 'microsecond',
        'parent_class': Centisecond,
        'max_intervals': {
            Microsecond.meta['name']: 100000, 
            Millisecond.meta['name']: 100, 
            Centisecond.meta['name']: 10
        },
        'carry_residual_time': True
    }

    def reset_scope(self, date):
        # Reset microseconds, milliseconds, and centiseconds, keep only decisecond portion
        new_microsecond_value = (date.microsecond // 100000) * 100000
        return super().reset_scope(date, {'microsecond': new_microsecond_value})


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
        },
        'carry_residual_time': True
    }

    def reset_scope(self, date):
        # Reset all microseconds
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
        },
        'carry_residual_time': True
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
        },
        'carry_residual_time': True
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
        },
        'carry_residual_time': False
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
        },
        'carry_residual_time': False
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
        },
        'carry_residual_time': False
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
        },
        'carry_residual_time': False
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
        },
        'carry_residual_time': True
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
        },
        'carry_residual_time': True
    }

    def reset_scope(self, date):
        start_year = (date.year // self.relativedelta_multiplier) * self.relativedelta_multiplier
        return super().reset_scope(date, {'year': start_year, 'month': 1, 'day': 1, 'hour': 0, 'minute': 0, 'second': 0, 'microsecond': 0})