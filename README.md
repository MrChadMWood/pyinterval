# Relative Dates Library

This Python library provides intuitive methods for defining relative points in time using a custom protocol. It supports chaining of datetime intervals in a parent-child fashion, abstracted with attributes and indexes. For example: `year.month[2]`.

> **Note**: This library is in its **alpha stage**. Contributions and feedback are welcome!

---

## Features

- **Flexible Interval Expressions**: Define points in time by chaining properties of the `Expression` object and indexing them.
  ```python
  # Second day of the 3rd week of the month, 0-based indexing
  expr = Expression()
  expr.month.week[2].day[1]
  ```

- **Negative Indexing**: Support for negative indices to easily access "last" instances of time units (e.g., the last day of the month).
  ```python
  expr.month.day[-1] # Last day of the month
  ```

- **Rollover Handling**: Control whether units roll over into the next larger unit or strictly validate. Examples provided later in this file.

- **More Time Intervals**: Provides proxies for additional units of time, such as centisecond, decisecond, and decade.
  ```python
  print(
    expr  
    .decade
    .year[0]
    .quarter[0]
    .month[0]
    .week[0]
    .day[0]
    .hour[0]
    .minute[0]
    .second[0]
    .decisecond[0]
    .millisecond[0]
    .microsecond[0]
  )

  Decade > Year > Quarter > Month > Week > Day > Hour > Minute > Second > Decisecond > Millisecond > Microsecond
  ```

- **Lazy Evaluation**: Define relative time objects and evaluate them against a specific `datetime` object later.
  ```python
  # Last day of the month
  last_day_of_month = expr.month.day[-1]

  # Evaluates after recieving a baseline
  last_day_this_month = last_month_day(datime.now())
  print(last_day_this_month)

  2024-09-30 00:00:00
  ```

- **Lazy Chain Validation**: Rough validation is provided during chaining and indexing, but full validation occurs only during evaluation.
  ```python
  expr.month.day[99]

  ----------------------------------------------------------------
  ValueError                                Traceback (most recent call last)
  Cell In[4], line 1
  ----> 1 exp.month.day[99]

  ValueError: Day cannot accept index 99 of Month (max: 34)
  ```

- **Lazy Arithmetic Evaluation**: Add or subtract relative deltas from an `Expression`. The library ensures proper order of operations during evaluation.
  ```python
  some_date = (
      expr.year.month[2].day[0]  # First day of March
      - expr.day.n(1)            # Subtract a day
      - expr.month.n(1)          # Subtract a month
  ).hour[11].minute[44]          # Set hour and minute
  some_date(datetime.now())

  datetime.datetime(2024, 1, 31, 11, 44)
  ```

- **Self-Explanatory String Representations**: The `__repr__` method produces an effective representation of the relative time expression.
  ```python
  print(some_date)

  Year > Month[3] > Day[1] + relativedelta(months=-1, days=-1) > Hour[12] > Minute[45]
  ```

---

## Interval Expression Rules

You can chain intervals together to describe increasingly granular time ranges. For example:

```python
exp = Expression().year.month[2].day[4]  # 5th day of the 3rd month (0-based indexing)
```

The structure consists of 4 main parts: root, root scope, scope units, and indices:

```text
Root().root_scope.scope_unit[index]
```

- **Root**: The `Expression()` object is always the root, encapsulating the logic.
- **Root Scope**: Defines the top-level time unit (e.g., `year`).
- **Scope Unit**: Represents smaller time units (e.g., `month`, `day`).
- **Index**: Represents the position within the scope unit (e.g., `month[2]` refers to the 3rd month).

The root scope cannot be indexed directly. However, you can call a root scope's `n` attribute (e.g., `Expression().quarter.n(1)`) to generate a `timedelta`.

```python
print(exp.quarter.n(2))  # 6 months relative to the current date

relativedelta(months=+6)
```

You can pass a date to a scope unit to evaluate the expression and create an absolute `datetime`.
```python
relative_date = exp.year.quarter[-1].month[1].week[-1].day[5]
absolute_date = relative_date(datetime.now())
print(absolute_date)

2024-11-26 00:00:00
```

---

## Rollover and Validation

By default, invalid dates roll over to the next valid date. For example:
```python
nonleap_date = datetime(2021, 1, 1)
feb_29_expr = Expression().year.month[1].day[28]
feb_29_2021 = feb_29_expr(nonleap_date)
print(feb_29_2021)

2024-03-01 00:00:00
```

To disable this behavior, pass `rollover=False`:
```python
feb_29_2021 = feb_29_expr(nonleap_date, rollover=False)

IndexError: Rollover occurred for Month from 2 to 3.
```

If you want operations to roll over, but not invalid indices, you can pass `operation_safe=True`:
```python
feb_29_2021 = feb_29_expr(nonleap_date, rollover=False, operation_safe=True)

2021-03-01 00:00:00
```

---

## Example Usage

```python
from pyinterval.expression import Expression
from datetime import datetime

exp = Expression()

twelfth_hour = exp.day.hour[11]
print(twelfth_hour)
# Output: Day > Hour[12]

todays_twelfth_hour = twelfth_hour(datetime.now())
print(todays_twelfth_hour)
# Output: 2024-09-13 12:00:00

yesterdays_twelfth_hour = todays_twelfth_hour - exp.day.n(1)
print(yesterdays_twelfth_hour)
# Output: 2024-09-12 12:00:00

next_week = todays_twelfth_hour + exp.week.n(1)
next_weeks_last_day = exp.week.day[-1](next_week)
print(next_weeks_last_day)
# Output: 2024-09-22 00:00:00

precisely_five_millis_before = exp.second(next_weeks_last_day) - exp.millisecond.n(5)
print(precisely_five_millis_before)
# Output: 2024-09-21 23:59:59.995000
```

---

## Roadmap

- **Smart Indexing**: Implement slicing (`[start:stop:step]`) to generate date ranges at specified granularity.
- **Validation**: Add `expression.verify(datetime) -> bool` to check if a datetime matches the expression or falls within the specified range.
- **Timedelta Compatibility**: Allow arithmetic with `timedelta` objects on expression chains (e.g., `chain - timedelta(days=1)`).
- **Dynamic Chain Building**: Provide built-in methods to dynamically create chains, reducing manual effort for constructing expressions.
- **Chain Operators**: Support chaining with the `+` operator and breaking chains with the `-` operator.
- **Advanced Smart Indexing**: Allow `[start:start]` to be expressions and `[:step]` to be a timedelta.
- **Rust Implementation**: Rebuild the library in Rust, with Python bindings.

---
