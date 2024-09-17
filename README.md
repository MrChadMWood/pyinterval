---

This library is still in its **alpha stage**. Contributions and feedback are welcome.

---

# Relative Dates Library

This Python library provides intuitive methods for defining relative points in time using a custom protocol. It supports chaining of datetime intervals in a sort of parent-child fassion, abstracted with attributes and indexes. For example: `year.month[2]`.

## Features

- **Flexible Interval Expressions**: Define points in time by chaining properties of the `Expression` object and indexing them.
  ```python
  # Second day of the 3rd week of the month, 0-based indexing
  expr = Expression()
  expr.month.week[2].day[1]
  ```

- **Negative Indexing**: Support for negative indices to easily access e.g., "last" instances of time units (e.g., the last day of the month).
  ```python
  # Last day of the month
  expr.month.day[-1]
  ```

- **Rollover Handling**: Control whether units roll over into the next larger unit, or strictly validate. 
  ```python
  # Last day of the month
  expr.month.day[-1]
  ```

- **More Timedeltas**: Provides a proxy for several more units of time, such as centisecond, decisecond, and decade.
  ```python
  # Last day of the month
  expr.month.day[-1]
  ```

- **Lazy Evaluation**: Datetime objects can be passed after the relative time object has been defined, evaluating the the precise time relative to the passed datetime.
  ```python
  # Last day of the month - September 2024
  last_month_day = expr.month.day[-1]
  last_month_day(datetime.datime.now())
  ```
  ```python
    2024-09-30 00:00:00
  ```
  
- **Lazy Chain Validation**: Rough validation is provided during chaining and indexing, but it is not garunteed until evaluation occurs.
  ```python
  # Last day of the month
  expr.month.day[99]
  ```
  ```python
    ---------------------------------------------------------------------------
    ValueError                                Traceback (most recent call last)
    Cell In[4], line 1
    ----> 1 exp.month.day[99]

    ValueError: Day cannot accept index 99 of Month (max: 34)
  ```

- **Lazy Arithmatic Evaluation**: You can add or subtract a relativedelta from an Expression. When evaluated, the Expression class handles performing the necessary operations on the baseline date while taking care to preserve order of operations.
  ```python
  some_complex_datetime = (
    (
        exp.year.month[2].day[0] # First day of March
        - exp.day.n(1) # Subtract a day
        - exp.month.n(1) # Subtract a month
    )
    .hour[11] # Hour 12
    .minute[44] # Minute 45
  )
  some_complex_datetime(datetime.now())
  ```
  ```python
    datetime.datetime(2024, 1, 31, 12, 45)
  ```
- **Self-Explanatory string representations**: The __repr__ method iterates through a chain to produce an effective representation of the relative time.
```python
  some_complex_datetime = (
    (
        exp.year.month[2].day[0] # First day of March
        - exp.day.n(1) # Subtract a day
        - exp.month.n(1) # Subtract a month
    )
    .hour[11] # Hour 12
    .minute[44] # Minute 45
  )
  print(some_complex_datetime)
  ```
  ```python
    Year > Month[3] > Day[1] + relativedelta(months=-1, days=-1) > Hour[12] > Minute[45]
  ```
---

### Interval Expression Rules

You can chain intervals together to describe increasingly granular time ranges. For example:

```python
exp = Expression().year.month[2].day[4]
```
Noting that index is 0-based- this represents any year's 3rd month, 5th day.

The scheme contains 4 unique parts in total, a root, root scope, scope units, and indices.
```python
Root().root_scope.scope_unit[index]
```
with an arbitrary number of `.scope_unit[index]` in the chain. 

- `Expression()` is always the Root of the expression, as its the class encapsulating most of the abstractions and logic for pyinterval.
- In the above example, `year` is the root scope, while `month` and `day` are both scope units. Each `.scope_unit[index]` can be led by another, further increasing granularity of the expression.
- An `[index]` can only by applied to a scope unit. The index represents the *nth* unit out of its parent. In the above example, thats to say `year.month[2].day[4]` represents the 3rd month of its parent, year. While the latter portion, `day[4]` represents the 5th day of its parent, month (whichever month it evaluates to).

The Root (`Expression()`) can be defined with or without a datetime object as the first argument. Doing so supplies that datetime as a default when evaluating for relative times, meaning a time doesn't need to be passed during evaluation. If you want to override the default or simply use an expression dynamically, pass a datetime object during evaluation as the only argument.

The root scope defines the scope of your interval chain. As such, it can not be indexed. Only units of the scope can be indexed. You can, however, call a root scope's `n` attribute (e.g., `Expression().quarter.n(1)`) to generate a timedelta. The first argument must be the number of which to be represented by the timedelta.
```python
print(exp.quarter.n(2))
```
```python
  relativedelta(months=+6)
```

Passing any date to a scope unit will evaluate the expression and create an absolute datetime.
```python
relative_date = exp.year.quarter[-1].month[1].week[-1].day[5]
absolute_date = relative_date(datetime.now())
print(absolute_date)
```
```python
  2024-11-26 00:00:00
```

## Rollover and Validations

By default, invalid dates roll over to the next valid date. For example:
```python
# 2021 - non leap year
nonleap_date = datetime(2021, 1, 1)

any_feb_29 = Expression().year.month[1].day[28]
feb_29_2021 = any_feb_29(date)
print(feb_29_2021)
```
```python
  2024-03-01 00:00:00
```

This also works with lazily evaluated mathmatical operations:
```
nonleap_date = datetime(2021, 1, 1)
expr = Expression()

any_feb_29 = expr.year.month[1].day[27] + expr.day.n(1)
feb_29_2021 = any_feb_29(date)
```
```python
  2024-03-01 00:00:00
```

To disable this behavior, pass `rollover=False`:
```python
feb_29_2021 = any_feb_29(date, rollover=False)
```
```python
  IndexError: Rollover occurred for Month from 2 to 3.
```

If you wanted operations to rollover, but not invalid indices, you can also pass `operation_safe=True`:
```python
feb_29_2021 = any_feb_29(date, rollover=False, operation_safe=True)
```
```python
  2021-03-01 00:00:00
```

#### More Examples

```python
from pyinterval.expression import Expression
from datetime import datetime
exp = Expression()

twelfth_hour = exp.day.hour[11]
print(twelfth_hour)
  Day > Hour[12]

todays_twelfth_hour = twelfth_hour(datetime.now())
print(todays_twelfth_hour)
  2024-09-13 12:00:00

yesterdays_twelfth_hour = todays_twelfth_hour - exp.day.n(1)
print(yesterdays_twelfth_hour)
  2024-09-12 12:00:00

next_week = todays_twelfth_hour + exp.week.n(1)
next_weeks_last_day = exp.week.day[-1](next_week)
print(next_weeks_last_day)
  2024-09-22 00:00:00

precisely_five_milli_before = exp.second(next_weeks_last_day) - exp.millisecond.n(5)
print(precisely_five_milli_before)
  2024-09-21 23:59:59.995000
```

---

## Roadmap

- **Smart Indexing**: Implement slicing (`[start:stop:step]`) to generate date ranges at specified granularity.
- **Validation**: Add `expression.verify(datetime) -> bool` to check if a datetime matches the expression or falls within the specified range.
- **Timedelta Compatibility**: Allow arithmetic with `timedelta` objects on expression chains (e.g., `chain - timedelta(days=1)`).
- **Dynamic Chain Building**: Provide built-in methods to dynamically create chains, reducing manual effort for constructing expressions.
- **Chain Operators**: Support chaining with the `+` operator and breaking chains with the `-` operator.
- **Advanced Smart Indexing**: To define a custom time interval, allow `[start:start]` to be Expressions, and `[:step]` to be a timedelta.
- **Rebuild in Rust**: Rebuild this in Rust. Allow use of the Rust version via Python.
---