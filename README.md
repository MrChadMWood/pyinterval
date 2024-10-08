# Relative Dates Library

This Python library provides intuitive methods for defining relative points in time using a custom protocol. It supports chaining of datetime intervals in a parent-child fashion, abstracted with attributes and indexes. For example: `year.month[2]`.

> **Note**: This library is in its **alpha stage**. Contributions and feedback are welcome!

---

## Features

<details>
  <summary>Flexible Interval Expressions: Define points in time by chaining properties of the `Expression` object and indexing them.</summary>

  ```python
  # Second day of the 3rd week of the month, 0-based indexing
  expr = Expression()
  expr.month.week[2].day[1]
  ```
</details>

<details>
  <summary>Negative Indexing: Support for negative indices to easily access "last" instances of time units (e.g., the last day of the month).</summary>

  ```python
  expr.month.day[-1] # Last day of the month
  ```
</details>

<details>
  <summary>Rollover Handling: Control whether units roll over into the next larger unit or strictly validate.</summary>

  By default, invalid indices roll over into the parent. For example:
  ```python
  nonleap_date = datetime(2021, 1, 1)
  feb_29_expr = Expression().year.month[1].day[28]
  feb_29_2021 = feb_29_expr(nonleap_date)
  print(feb_29_2021)

  2024-03-01 00:00:00
  ```

  Similarly, with mathmatical operations:
  ```python
  expr = Expression()
  feb_29_expr = expr.year.month[1].day[27] + expr.day.n(1)
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
  feb_29_expr = expr.year.month[1].day[27] + expr.day.n(1)
  feb_29_2021 = feb_29_expr(nonleap_date, rollover=False, operation_safe=True)
  print(feb_29_2021)

  2021-03-01 00:00:00
  ```
</details>

<details>
  <summary>More Time Intervals: Provides proxies for additional units of time, such as centisecond, decisecond, and decade.</summary>

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

  Decade > Year[1] > Quarter[1] > Month[1] > Week[1] > Day[1] > Hour[1] > Minute[1] > Second[1] > Decisecond[1] > Millisecond[1] > Microsecond[1]
  ```
</details>

<details>
  <summary>Lazy Evaluation: Define relative time objects and evaluate them against a specific `datetime` object later.</summary>

  ```python
  # Last day of the month
  last_day_of_month = expr.month.day[-1]

  # Evaluates after recieving a baseline
  last_day_this_month = last_month_day(datime.now())
  print(last_day_this_month)

  2024-09-30 00:00:00
  ```
</details>

<details>
  <summary>Lazy Chain Validation: Rough validation is provided during chaining and indexing, but full validation occurs only during evaluation.</summary>

  ```python
  expr.month.day[99]

  ----------------------------------------------------------------
  ValueError                                Traceback (most recent call last)
  Cell In[4], line 1
  ----> 1 expr.month.day[99]

  ValueError: Day cannot accept index 99 of Month (max: 34)
  ```
</details>

<details>
  <summary>Lazy Arithmetic Evaluation: Add or subtract relative deltas from an `Expression`. The library ensures proper order of operations during evaluation.</summary>

  ```python
  from pyinterval.expression import Expression
  from datetime import datetime
  
  expr = Expression()            # Instantiate the Expression object
  date_expr = expr.year.month[1] # Start with the year and second month
  date_expr += expr.day.n(1)     # Add 1 day to the expression
  date_expr = date_expr.day[27]  # Set the 28th day (0-based, so index 27)
  date_expr -= expr.month.n(1)   # Subtract one month from the expression

  time_expr = (                  # Set the time to 01:01:01.101001
      date_expr
      .hour[0]
      .minute[0]
      .second[0]
      .decisecond[0]
      .millisecond[0]
      .microsecond[0]
  )

  final_expr = time_expr + expr.month.n(1)  # Add one month to the final result

  result = final_expr(datetime(2021, 1 ,1)) # Evaluate the expression with a non-leap year
  print(result)

  result = final_expr(datetime(2024, 1 ,1)) # Evaluate the expression with a leap year
  print(result)

  2021-03-01 01:01:01.101001
  2024-02-29 01:01:01.101001
  ```
</details>

<details>
  <summary>Self-Explanatory String Representations: The `__repr__` method produces an effective representation of the relative time expression.</summary>

  ```python
  print(some_date)

  Year > Month[3] > Day[1] + relativedelta(months=-1, days=-1) > Hour[12] > Minute[45]
  ```
</details>

<details>
  <summary>High Performance: Complex relative dates are evaluated quickly and efficiently.</summary>

  ```python
  %%timeit

  expr = Expression()
  date_expr = expr.year.month[-11]
  date_expr += expr.day.n(59)
  date_expr -= expr.month.n(1634)

  time_expr = (
      date_expr
      .hour[-823]
      .minute[-59]
      .second[-59]
      .decisecond[-9]
      .millisecond[-99]
      .microsecond[-999]
  )

  final_expr = time_expr + expr.month.n(1)

  result1 = final_expr(datetime(2021, 1 ,1)) # Evaluate the expression with a non-leap year
  result2 = final_expr(datetime(2024, 1 ,1)) # Evaluate the expression with a leap year
  assert result1 != result2

  385 μs ± 4.22 μs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)
  ```
</details>

---

## Interval Expression Rules

You can chain intervals together to describe increasingly granular time ranges. For example:

```python
expr = Expression().year.month[2].day[4]  # 5th day of the 3rd month (0-based indexing)
```

The structure consists of 4 main parts: root, root scope, scope units, and indices:

```text
Root().root_scope.scope_unit[index]
```

- **Root**: The `Expression()` object is always the root, encapsulating the logic.
- **Root Scope**: Defines the top-level time unit (e.g., `year`).
- **Scope Unit**: Represents smaller time units (e.g., `month`, `day`).
- **Index**: Represents the position within the parent element (e.g., `year.month[2]` refers to the 3rd month of the year).

The root scope cannot be indexed directly. However, you can call a root scope's `n` attribute (e.g., `Expression().quarter.n(1)`) to generate a `timedelta`.

```python
print(expr.quarter.n(2))  # 6 months relative to the current date

relativedelta(months=+6)
```

You can pass a date to a scope unit to evaluate the expression and create an absolute `datetime`.
```python
relative_date = expr.year.quarter[-1].month[1].week[-1].day[5]
absolute_date = relative_date(datetime.now())
print(absolute_date)

2024-11-26 00:00:00
```

---

## Roadmap

- **Smart Indexing**: Implement slicing (`[start:stop:step]`) to generate date ranges at specified granularity.
- **Validation**: Add `expression.verify(datetime) -> bool` to check if a datetime matches the expression or falls within the specified range.
- **Timedelta Compatibility**: Allow arithmetic with `timedelta` objects on expression chains (e.g., `chain - timedelta(days=1)`).
- **Dynamic Chain Building**: Provide built-in methods to dynamically create chains, reducing manual effort for constructing expressions.
- **Chain Operators**: Support chaining with the `+` operator and breaking chains with the `-` operator.
- **Advanced Smart Indexing**: Allow `[start:stop]` to be expressions and `[:step]` to be a timedelta.
- **Rust Implementation**: Rebuild the library in Rust, with Python bindings.

---
