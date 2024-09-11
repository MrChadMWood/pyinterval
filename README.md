This library and its repository are still in its alpha stage.

# Intuitive Relative Dates Library

This library provides intuitive methods for interacting with relative dates, following a custom protocol for describing points in time.

## Custom Interval Expression Protocol

Time is segmented into a flat hierarchy of intervals:

```
Microsecond < Second < Minute < ... < Year
```

To express a point in time, you must define a scope, ordinal, and unit:

- **Scope**: The larger time unit (e.g., Year, Month) that gives context to the interval.
- **Ordinal**: A number (positive or negative) specifying the particular instance of the unit within the scope.
- **Unit**: The smaller time unit being measured (e.g., Day, Hour).

These can be represented using dot notation: `Scope.Ordinal.Unit`. For example, `Year.2.Month` indicates the 3rd month of the year.

## Interval Rules

1. **Hierarchical Order**: The `Unit` must always be lower in the hierarchy than its `Scope`.
   - Valid: `Year.2.Month` (Year is larger than Month)
   - Invalid: `Day.2.Year` (Day is smaller than Year)
   
2. **Ordinal Limits**: The `Scope` defines a maximum allowable ordinal value for its `Unit`.  
   (This is a soft limit and may not accurately represent the true total for a Unit in each scope. More details on that later.)
   - Valid: `Year.365.Day` (A year has up to 366 days)
   - Invalid: `Year.999.Day` (Exceeds the number of days in a year)
   
3. **Negative Indexing**: Negative indices are allowed, where `-1` represents the "last" instance, `-2` the second-to-last, and so on.
   - Example: `Year.-1.Month` refers to the last month of the year.

## Chaining Intervals

Intervals can be chained together to define more specific time ranges. Each chain creates a finer level of granularity.

### Example

```
[Year.3.Month, Month.4.Day]
```

This chain represents the 5th day of the 4th month of a year.

### Chaining Rules

1. **Scope-Unit Matching**: For each interval in the chain (after the first), the `Scope` must match the previous interval's `Unit`.
   - Valid: `[Year.3.Month, Month.4.Day]`
   - Invalid: `[Year.3.Month, Week.4.Day]` (Week does not match the prior unit of Month)
   
2. **Arbitrary Length Chains**: Chains can be as long as needed to describe increasingly granular intervals.

### Example Chain

```
[Year.2.Month, Month.3.Week, Week.4.Day, Day.-2.Hour, Hour.2.Minute, Minute.5.Second]
```

This chain specifies:
- The 6th second 
- Of the 3rd minute
- Of the 2nd-last hour
- Of the 5th day
- Of the 4th week
- Of the 3rd month
- Of the year.

## Pythonic Expression of Chains

In this implementation, chains are simplified to reduce redundancy. The chaining follows a structure like:

```python
from pyintervals import Expression

Expression().year.month[2].week[3].day[4].hour[5].minute[2].second[5]
```

The scope starts the chain, followed by the unit in dot notation and `[ordinal]` in bracket notation. After the initial scope (year, in this case), the syntax combines Unit and Scope concepts intuitively. Users do not need to type the month twice to represent `[Year.2.Month, Month.3.Week]`; simply `year.month[2].week[3]` suffices.

### Example Usage

By default, invalid expressions like the following are possible:

```python
>>> feb_30 = Expression(root_datetime=datetime.datetime(2024,1,1)).year.month[1].day[29]
>>> feb_30()
datetime.datetime(2024, 3, 1, 0, 0)
```

The result works because days automatically rollover. To prevent this behavior, pass `rollover=False`:

```python
>>> feb_30 = Expression(root_datetime=datetime.datetime(2024,1,1)).year.month[1].day[29]
>>> feb_30(rollover=False)
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
...
ValueError: day is out of range for month
```

Note: A simple way to get the last day of the month is to use negative indexing.

## Handling Variability in Unit Intervals

`Unit.max_intervals` represents the "total number of intervals that could ever possibly occur in this time frame." It’s used for validation during the lazy building of an expression. Once an expression is called, it is validated completely.

Negative indexing works by dynamically adding and then subtracting the negative index. For example, `Month.-5.Day` would evaluate by adding a month to the date and then subtracting days.

### Simple Use Cases

```python
# Slices the datetime object to specified granularity
>>> Expression().year(datetime.datetime(2024,12,23,5,35,53,29485))
datetime.datetime(2024, 1, 1, 0, 0)

>>> Expression().second(datetime.datetime(2024,12,23,5,35,53,29485))
datetime.datetime(2024, 12, 23, 5, 35, 53)
```

## Roadmap

- Implement smart indexing `[star:stop:step]` to define time ranges. When called, return a list of datetime objects falling within the range, at the granularity specified by the expression.
- Implement `expression.verify(datetime) -> Bool` to determine if a datetime lands within the refined range (with advanced indexing) or exactly matches the interval (up to the interval's defined granularity).
- Implement compatibility with `timedelta` for arithmetic on Expression chains (e.g., chain - timedelta(days=1)). Store it somewhere, on Root? Allow it to be specified on initialization.
- Add a built-in way to dynamically build chains, instead of users trying `Expression.getattr()`.
- Allow chains to be joined with the `+` operator (requiring that the child-most unit matches the scope of the next expression) or broken with the `-` operator (using the child-most unit of the next expression as the breakpoint).