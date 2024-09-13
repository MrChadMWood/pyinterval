---

This library is still in its **alpha stage**. Contributions and feedback are welcome.

---

# Relative Dates Library

This Python library provides intuitive methods for interacting with relative dates, using a custom protocol to describe points in time and intervals with high precision. It supports chaining of date intervals and allows easy manipulation and querying of specific time units.

## Features

- **Flexible Interval Expressions**: Define time intervals by accessing properties of the Expression object and indexing them.
- **Granularity Control**: Break down time into smaller units (microseconds to decades) and chain them together for greater precision.
- **Negative Indexing**: Support for negative indices to easily access "last" instances of time units (e.g., the last day of the month).
- **Rollover Handling**: Control whether units roll over into the next larger unit, or strictly validate intervals.
- **More Timedeltas**: Provides a proxy for several more units of time, such as centisecond, decisecond, and decade.
- **Lazy Evaluation**: Datetime objects can be passed after the relative time object has been defined, evaluating the the precise time relative to the passed datetime.
- **Lazy Chain Validation**: Rough validation is provided during chaining and indexing, but it is not garunteed until evaluation occurs.
- **Lazy Arithmatic Evaluation**: You can add or subtract a relativedelta from an Expression. When evaluated, the Expression class performs the necessary operations on the baseline date while taking care to preserve order of operations.

---

### Interval Expression Rules

You can chain intervals together to describe increasingly granular time ranges. For example:

```python
exp = Expression().year.month[2].day[4]
```

Noting that index is 0-based, this represents the 5th day of the 3rd month of the year. When chaining intervals, it lways follows this scheme:

   `Root().root_scope.scope_unit[index]`

with an arbitrary number of `.scope_unit[index]` in the chain. In the above example, `Expression()` is the Root, while `year` is the root_scope and `month` and `day` are both scope_units.
Each `.scope_unit[index]` can be led by another, further increasing granularity of the expression.

The Root (`Expression()`) can be defined with or without a datetime object as the first argument. Doing so supplies that datetime as a default when evaluating for relative times, meaning a time doesn't need to be passed during evaluation. If you want to override the default or simply use an expression dynamically, pass a datetime object during evaluation as the only argument.

The root_scope defines the scope of your interval chain. As such, it can not be indexed. Only units of the scope can be indexed. You can, however, call the root_scope's `n` attribute (e.g., `Expression().quarter.n(1)`) to generate a timedelta. The first argument must be the number of which to be represented by the timedelta.

The scope_unit divides its parent, the scope. It's called the scope_unit because it, too, can technically be a scope (just not the root_scope). When a unit's property of a smaller unit is accessed, it becomes the immediate scope of that smaller unit. In the above example, that's to say month is the scope of day but still the unit of year. The scope_unit is indexable (0-based, including negative) to specify its index within its parent.

Passing any date returns a datetime object
```python
# Returns second month, fourth day of this year as datetime.
exp(datetime.datetime.now())
```

Negative indexing also works to collect the nth last unit of an interval. For example, the last day of a month:
```python
exp = Expression().month.day[-1]
```

## Rollover and Validations

By default, invalid dates roll over to the next valid date. For example:

```python
exp = Expression().year.month[1].day[29]
feb_30 = exp(datetime.datetime(2024, 1, 1))
print(feb_30)  # 2024-03-01 00:00:00
```

To disable this behavior, pass `rollover=False`:

```python
feb_30 = exp(datetime.datetime(2024, 1, 1), rollover=False)
# Raises: ValueError: day is out of range for month
```

### Handling Variability in Unit Intervals

`Unit.max_intervals` defines the total possible intervals for a unit within its scope. This helps ensure index validation during expression building, but it isn't preceise. Due to the dynamic nature of these intervals, hard validation only occurs at evaluation time. Max intervals should roughly define the maximum number of child units possible for each child unit within a unit. While building an expression chain, the class will make sure you dont exceed these values.

### Example Usages

#### Setup

```python
from pyintervals.expression import Expression
import datetime

exp = Expression()
dt = datetime.datetime(2024, 12, 30, 12, 40, 35, 500000)
```

#### Extracting Components

```python
# Get the year start date
print(exp.year(dt))  # 2024-01-01 00:00:00

# Last week, 5th day of 2nd month
print(exp.year.month[1].week[-1].day[4](dt))  # 2024-02-27 00:00:00

# 5th weekday in the current week
print(exp.week.day[4](dt))  # 2025-01-03 00:00:00

# 4th week's 5th day in the last month of the quarter
print(exp.quarter.month[-1].week[3].day[4](dt))  # 2024-10-26 00:00:00
```

#### More Examples

```
>>> from pyinterval.expression import Expression
>>> from datetime import datetime
>>> exp = Expression()

>>> twelfth_hour = exp.day.hour[11]
>>> print(twelfth_hour)
Day > Hour[12]

>>> todays_twelfth_hour = twelfth_hour(datetime.now())
>>> print(todays_twelfth_hour)
2024-09-13 12:00:00

>>> yesterdays_twelfth_hour = todays_twelfth_hour - exp.day.n(1)
>>> print(yesterdays_twelfth_hour)
2024-09-12 12:00:00

>>> next_week = todays_twelfth_hour + exp.week.n(1)
>>> next_weeks_last_day = exp.week.day[-1](next_week)
>>> print(next_weeks_last_day)
2024-09-22 00:00:00

>>> precisely_five_milli_before = exp.second(next_weeks_last_day) - exp.millisecond.n(5)
>>> print(precisely_five_milli_before)
2024-09-21 23:59:59.995000
```

#### Lazy Arithmetic Evaluation
Here, we add 1 month and 30 minutes, while subtracting a week, from a date that hasn't been evaluated yet.
```
>>> # Get current time
>>> today = datetime.datetime.now()
>>> print(f'{"Right now:":20}', today)
Right now:           2024-09-13 13:15:16.882903

>>> # Time of meeting, which occurs on the 12th hour of the first day of the week
>>> this_meeting = exp.week.day[0].hour[11]
>>> print(f'{"This Meeting:":20}', this_meeting(today))
This Meeting:        2024-09-10 12:00:00

>>> # End of meeting, which occurs at the end of the hour
>>> end_of_this_meeting = this_meeting.minute[58].second[58]
>>> print(f'{"End Of This Meeting:":20}', end_of_this_meeting(today))
End Of This Meeting: 2024-09-10 12:59:59

>>> # Next meeting, which occurs in 1 week less than 1 month + 30 minutes from this meeting
>>> next_meeting = this_meeting + exp.month.n(1) + exp.minute.n(30) - exp.week.n(1)
>>> print(f'{"Next Meeting:":20}', next_meeting(today))
Next Meeting:        2024-10-03 12:30:00

>>> # End of next meeting, which occurs at the same time
>>> end_of_next_meeting = next_meeting.minute[58].second[58]
>>> print(f'{"End Of Next Meeting:":20}', end_of_next_meeting(today))
End Of Next Meeting: 2024-10-03 12:59:59
```

---

## Roadmap

- **Smart Indexing**: Implement slicing (`[start:stop:step]`) to generate date ranges at specified granularity.
- **Validation**: Add `expression.verify(datetime) -> bool` to check if a datetime matches the expression or falls within the specified range.
- **Timedelta Compatibility**: Allow arithmetic with `timedelta` objects on expression chains (e.g., `chain - timedelta(days=1)`).
- **Dynamic Chain Building**: Provide built-in methods to dynamically create chains, reducing manual effort for constructing expressions.
- **Chain Operators**: Support chaining with the `+` operator and breaking chains with the `-` operator.

---