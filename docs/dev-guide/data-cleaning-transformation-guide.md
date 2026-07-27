---
document_type: runbook
status: active
implementation: implemented
scope: data-engineering
authority: explanatory
owner: backend
last_reviewed: 2026-07-27
---

# Data Cleaning & Transformation Guide — Python for Data Engineering

A practical reference for cleaning, exploring, and transforming datasets with **pandas**, **numpy**, and built-in Python tools. Each section includes **what it does**, **why you need it**, and **concrete examples**.

---

## Table of Contents

1. [Exploratory Analysis — Know Your Data](#1-exploratory-analysis--know-your-data)
2. [Handling Missing Values](#2-handling-missing-values)
3. [Duplicates](#3-duplicates)
4. [Column Operations](#4-column-operations)
5. [Row Operations & Filtering](#5-row-operations--filtering)
6. [String Transformations](#6-string-transformations)
7. [Date & Time](#7-date--time)
8. [Applying Functions](#8-applying-functions)
9. [Grouping & Aggregation](#9-grouping--aggregation)
10. [Merging & Concatenating Datasets](#10-merging--concatenating-datasets)
11. [Reshaping: Pivot & Melt](#11-reshaping-pivot--melt)
12. [Encoding Categorical Data](#12-encoding-categorical-data)
13. [Outlier Detection](#13-outlier-detection)
14. [Pipeline: Putting It All Together](#14-pipeline-putting-it-all-together)

---

## 1. Exploratory Analysis — Know Your Data

Before transforming anything, understand what you're working with.

| Method | What it does | Why |
|---|---|---|
| `df.head(n)` | First `n` rows | Quick sanity check |
| `df.tail(n)` | Last `n` rows | Check recent records |
| `df.sample(n)` | Random `n` rows | Spot-check without bias |
| `df.info()` | Column names, non-null count, dtypes | Detect type issues and missing data at a glance |
| `df.describe()` | Summary stats (mean, std, min, quartiles, max) | Understand numeric distributions |
| `df.describe(include='object')` | Stats for non-numeric columns | Frequency, unique count, top value |
| `df.shape` | (rows, columns) | Is the dataset as big as expected? |
| `df.columns` | Column labels | Rename or reorder planning |
| `df.dtypes` | Data types per column | Detect strings where numbers should be |
| `df.nunique()` | Count of unique values per column | Cardinality check — good for categorical columns |
| `df['col'].unique()` | Array of unique values | See every distinct value in a column |
| `df['col'].value_counts()` | Frequency table (sorted) | Detect skewed categories |
| `df['col'].value_counts(normalize=True)` | Proportions instead of counts | Percentage distribution |
| `df.isnull().sum()` | Missing values per column | **First thing to check before cleaning** |
| `df.duplicated().sum()` | Number of duplicate rows | Decide dedup strategy |

```python
import pandas as pd
import numpy as np

df = pd.read_csv('dataset.csv')

# First look
print(df.shape)
print(df.info())
print(df.head(3))

# Quick stats
print(df.describe())
print(df.isnull().sum())

# Categorical exploration
print(df['category'].value_counts())
print(df['category'].nunique())
```

---

## 2. Handling Missing Values

Missing data is **never** random — how you handle it changes your results.

### Detection

```python
df.isnull().sum()                    # Count per column
df.isnull().sum() / len(df) * 100    # Percentage per column
df[df['col'].isnull()]               # Rows where col is null
```

### Options — in order of preference

| Method | Code | When to use |
|---|---|---|
| Drop rows | `df.dropna()` | Loss is acceptable (<5%), missing is truly random |
| Drop column | `df.drop(columns=['col'])` | Column is >70% empty or irrelevant |
| Fill constant | `df.fillna(0)` or `df.fillna('Unknown')` | Missing means "zero" or "not applicable" |
| Forward fill | `df.fillna(method='ffill')` | Time series: carry previous value forward |
| Backward fill | `df.fillna(method='bfill')` | Time series: fill with next value |
| Fill mean/median | `df['col'].fillna(df['col'].median())` | Numeric columns, symmetric distribution |
| Fill mode | `df['col'].fillna(df['col'].mode()[0])` | Categorical columns |
| Interpolation | `df['col'].interpolate()` | Time series with linear trends |

```python
# Strategy: drop if >50% missing, else fill
threshold = len(df) * 0.5
df.dropna(thresh=threshold, axis=1, inplace=True)

# Fill numeric with median
for col in df.select_dtypes(include='number').columns:
    df[col].fillna(df[col].median(), inplace=True)

# Fill categorical with mode
for col in df.select_dtypes(include='object').columns:
    df[col].fillna(df[col].mode()[0], inplace=True)
```

---

## 3. Duplicates

```python
df.duplicated().sum()                   # Count duplicates
df[df.duplicated()]                     # View them
df[df.duplicated(subset=['col1','col2'])]  # Duplicates based on subset
df.drop_duplicates()                    # Remove full-row duplicates
df.drop_duplicates(subset=['col'], keep='first')  # Keep first occurrence
```

**Always inspect before deleting.** Not all duplicates are errors — sometimes they carry different context (timestamps, versions).

---

## 4. Column Operations

### Rename

```python
df.rename(columns={'old_name': 'new_name'}, inplace=True)

# Bulk rename with a mapper
df.columns = ['id', 'name', 'price', 'date']  # Only if order is known
df.rename(columns=str.lower, inplace=True)      # Lowercase all
df.rename(columns=lambda x: x.strip(), inplace=True)  # Strip whitespace
```

### Add columns

```python
# From existing data
df['full_name'] = df['first'] + ' ' + df['last']
df['tax'] = df['price'] * 0.21
df['is_adult'] = df['age'] >= 18  # Boolean column

# With numpy conditions
df['age_group'] = np.where(df['age'] < 18, 'minor', 'adult')

# Multiple conditions
conditions = [
    (df['age'] < 13),
    (df['age'] < 18),
    (df['age'] >= 18)
]
choices = ['child', 'teen', 'adult']
df['age_group'] = np.select(conditions, choices, default='unknown')
```

### Drop columns

```python
df.drop(columns=['col1', 'col2'], inplace=True)
df.drop(columns=df.columns[df.isnull().mean() > 0.7], inplace=True)  # Drop >70% empty
```

### Reorder columns

```python
df = df[['id', 'name', 'price', 'date']]  # Just reassign in desired order
```

---

## 5. Row Operations & Filtering

### Select rows by condition

```python
# Single condition
df[df['age'] > 30]
df[df['name'] == 'Alice']

# Multiple conditions
df[(df['age'] > 30) & (df['city'] == 'Buenos Aires')]
df[(df['age'] < 18) | (df['age'] > 65)]

# Isin — filter by list
df[df['category'].isin(['A', 'B', 'C'])]

# Negation
df[~(df['status'] == 'inactive')]

# String filtering
df[df['name'].str.contains('alice', case=False, na=False)]
df[df['email'].str.endswith('@gmail.com')]
df[df['phone'].str.match(r'\d{3}-\d{4}-\d{4}')]
```

### Loc vs iloc

```python
df.loc[df['age'] > 30, ['name', 'age']]      # Label-based: rows by condition, columns by name
df.iloc[10:20, 0:3]                            # Integer position-based: rows 10-19, cols 0-2
df.loc[df['age'] > 30, 'name'] = 'ADULT'       # Conditional update in-place
```

### Sample rows

```python
df.sample(frac=0.1)          # Random 10% of rows
df.sample(n=100)             # Exactly 100 random rows
df.sample(frac=0.1, random_state=42)  # Reproducible sampling
```

---

## 6. String Transformations

The `.str` accessor unlocks vectorized string operations on whole columns.

```python
# Cleaning whitespace
df['col'] = df['col'].str.strip()
df['col'] = df['col'].str.strip().str.lower()

# Case
df['col'] = df['col'].str.lower()
df['col'] = df['col'].str.upper()
df['col'] = df['col'].str.title()

# Replace substrings
df['col'] = df['col'].str.replace('old', 'new', regex=False)
df['phone'] = df['phone'].str.replace(r'\D', '', regex=True)  # Keep only digits

# Split a column into multiple columns
df[['first_name', 'last_name']] = df['full_name'].str.split(' ', n=1, expand=True)

# Extract with regex
df['year'] = df['date_str'].str.extract(r'(\d{4})', expand=False)

# Check content
df['has_email'] = df['text'].str.contains('@', na=False)

# Length
df['name_length'] = df['name'].str.len()

# Prefix / suffix
df['code'] = 'PREFIX_' + df['id'].astype(str)
df['code'] = df['id'].apply(lambda x: f'PREFIX_{x}')

# Padding
df['id'] = df['id'].astype(str).str.zfill(6)  # '123' -> '000123'
```

---

## 7. Date & Time

```python
# Convert string to datetime
df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
df['date'] = pd.to_datetime(df['date'], errors='coerce')  # Invalid -> NaT

# Extract components
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day
df['weekday'] = df['date'].dt.weekday           # Monday=0, Sunday=6
df['weekday_name'] = df['date'].dt.day_name()    # 'Monday', 'Tuesday'...
df['quarter'] = df['date'].dt.quarter
df['is_weekend'] = df['date'].dt.weekday >= 5

# Time differences
df['days_since'] = (pd.Timestamp('today') - df['date']).dt.days

# Filter by date range
df[df['date'].between('2024-01-01', '2024-12-31')]
df[df['date'].dt.year == 2024]
df[df['date'].dt.month.isin([1, 2, 3])]  # Q1

# Set as index for resampling
df.set_index('date', inplace=True)
df.resample('M').mean()      # Monthly average
df.resample('W').sum()       # Weekly sum
df.resample('Q').agg({'sales': 'sum', 'profit': 'mean'})
```

---

## 8. Applying Functions

### `apply` — row or column-wise

```python
# Column-wise (axis=0, default)
df['price_sqrt'] = df['price'].apply(np.sqrt)

# Row-wise (axis=1)
df['total'] = df.apply(lambda row: row['price'] * row['quantity'], axis=1)

# Multiple columns as input
def categorize(price):
    if price < 10: return 'cheap'
    if price < 50: return 'moderate'
    return 'expensive'

df['price_tier'] = df['price'].apply(categorize)
```

### `map` — value replacement (Series only)

```python
# Dictionary mapping
status_map = {1: 'active', 0: 'inactive', -1: 'unknown'}
df['status_label'] = df['status'].map(status_map)

# Or use replace for partial matches
df['status'] = df['status'].replace({1: 'active', 0: 'inactive'})
```

### `transform` — same as apply but returns same shape (useful in groupby)

```python
df['price_pct'] = df.groupby('category')['price'].transform(lambda x: x / x.sum())
```

---

## 9. Grouping & Aggregation

```python
# Basic groupby
df.groupby('category')['price'].mean()
df.groupby('category')['price'].agg(['mean', 'std', 'min', 'max', 'count'])

# Multiple aggregations per column
df.groupby('category').agg({
    'price': ['mean', 'std'],
    'quantity': 'sum',
    'date': 'first'
})

# Named aggregation (cleaner)
df.groupby('category').agg(
    avg_price=('price', 'mean'),
    total_qty=('quantity', 'sum'),
    first_sale=('date', 'min')
)

# Reset index to flatten
df.groupby('category')['price'].mean().reset_index()

# Multiple group keys
df.groupby(['region', 'category'])['sales'].sum()

# Group and transform (add column without collapsing)
df['sales_pct'] = df.groupby('region')['sales'].transform(lambda x: x / x.sum() * 100)
```

### Aggregation functions cheat sheet

| Function | What |
|---|---|
| `mean()`, `median()`, `std()`, `var()` | Central tendency & spread |
| `min()`, `max()` | Range |
| `sum()`, `prod()` | Totals |
| `count()`, `nunique()` | Frequency |
| `first()`, `last()` | First/last value in group |
| `cumsum()`, `cummax()` | Cumulative operations |

---

## 10. Merging & Concatenating Datasets

### `concat` — stack rows or columns

```python
# Vertically (add rows)
pd.concat([df1, df2], axis=0, ignore_index=True)

# Horizontally (add columns)
pd.concat([df1, df2], axis=1)

# With a key to track origin
pd.concat([df_q1, df_q2], keys=['Q1', 'Q2'])
```

### `merge` — SQL-style joins

```python
# Inner join (only matching keys)
pd.merge(df_orders, df_customers, on='customer_id')

# Left join (keep all orders)
pd.merge(df_orders, df_customers, on='customer_id', how='left')

# Right join
pd.merge(df_orders, df_customers, on='customer_id', how='right')

# Outer join (all records from both)
pd.merge(df_orders, df_customers, on='customer_id', how='outer')

# Different key names
pd.merge(df_orders, df_customers, left_on='cust_id', right_on='id')

# Suffix duplicates
pd.merge(df_orders, df_customers, on='customer_id', suffixes=('_order', '_cust'))
```

### `join` — index-based merge

```python
df_orders.join(df_customers, on='customer_id')  # Requires index match
```

---

## 11. Reshaping: Pivot & Melt

### `melt` — wide to long (columns → rows)

Use when your data has multiple columns that are actually values of a single variable.

```python
# Before: wide format with monthly columns
#   id | name | jan_sales | feb_sales | mar_sales
# After: long format
#   id | name | month | sales

df_long = df.melt(
    id_vars=['id', 'name'],
    value_vars=['jan_sales', 'feb_sales', 'mar_sales'],
    var_name='month',
    value_name='sales'
)
# Then clean the month column
df_long['month'] = df_long['month'].str.replace('_sales', '')
```

### `pivot` — long to wide (rows → columns)

```python
df_wide = df_long.pivot(
    index=['id', 'name'],
    columns='month',
    values='sales'
).reset_index()
```

### `pivot_table` — pivot with aggregation

```python
df.pivot_table(
    values='sales',
    index='region',
    columns='category',
    aggfunc='sum',
    fill_value=0,
    margins=True        # Adds totals row/column
)
```

---

## 12. Encoding Categorical Data

### Label encoding

```python
df['category_code'] = df['category'].astype('category').cat.codes
```

### One-hot encoding

```python
pd.get_dummies(df, columns=['category'], prefix='cat')

# Drop first to avoid multicollinearity
pd.get_dummies(df, columns=['category'], drop_first=True)
```

### Ordinal encoding (manual mapping)

```python
size_map = {'small': 1, 'medium': 2, 'large': 3}
df['size_code'] = df['size'].map(size_map)
```

---

## 13. Outlier Detection

### Z-score method

```python
from scipy import stats

z_scores = np.abs(stats.zscore(df['price']))
df_no_outliers = df[z_scores < 3]  # Keep rows within 3 std devs
```

### IQR method

```python
Q1 = df['price'].quantile(0.25)
Q3 = df['price'].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

df_no_outliers = df[(df['price'] >= lower) & (df['price'] <= upper)]
```

### Capping (winsorizing)

```python
df['price'] = df['price'].clip(lower=lower, upper=upper)
```

---

## 14. Pipeline: Putting It All Together

A real transformation pipeline step by step:

```python
import pandas as pd
import numpy as np

def clean_sales_data(df):
    """Full cleaning and transformation pipeline for sales data."""
    df = df.copy()

    # 1. Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    # 2. Drop fully empty or irrelevant columns
    df.drop(columns=[col for col in df.columns if df[col].isnull().mean() > 0.7],
            inplace=True, errors='ignore')

    # 3. Parse dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df.dropna(subset=['date'], inplace=True)

    # 4. Handle missing numeric values
    for col in df.select_dtypes(include='number').columns:
        df[col].fillna(df[col].median(), inplace=True)

    # 5. Handle missing categorical
    for col in df.select_dtypes(include='object').columns:
        df[col].fillna('Unknown', inplace=True)

    # 6. Remove duplicates
    df.drop_duplicates(inplace=True)

    # 7. Clean strings
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()

    # 8. Feature engineering
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['weekday'] = df['date'].dt.day_name()
    df['revenue'] = df['price'] * df['quantity']
    df['revenue_tier'] = pd.qcut(df['revenue'], q=4, labels=['low', 'medium', 'high', 'premium'])

    # 9. Filter outliers
    Q1 = df['revenue'].quantile(0.25)
    Q3 = df['revenue'].quantile(0.75)
    IQR = Q3 - Q1
    df = df[(df['revenue'] >= Q1 - 1.5 * IQR) & (df['revenue'] <= Q3 + 1.5 * IQR)]

    # 10. Sort and reset
    df.sort_values('date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df

# Usage
# raw = pd.read_csv('sales.csv')
# cleaned = clean_sales_data(raw)
```

---

## Quick Reference — Most Used Methods

| Goal | Method |
|---|---|
| First look at data | `head()`, `info()`, `describe()` |
| Count missing | `isnull().sum()` |
| Drop rows with nulls | `dropna()` |
| Fill nulls | `fillna(value)` |
| Remove duplicates | `drop_duplicates()` |
| Rename columns | `rename(columns={})` |
| Filter rows | `df[condition]` |
| Replace values | `replace()`, `map()` |
| String ops | `.str.lower()`, `.str.split()`, `.str.replace()` |
| Apply function | `apply()`, `applymap()` |
| Group & aggregate | `groupby().agg()` |
| Merge datasets | `merge()`, `concat()` |
| Reshape | `melt()`, `pivot_table()` |
| Date parsing | `pd.to_datetime()` |
| Save output | `to_csv()`, `to_parquet()`, `to_excel()` |

---

> **Pro tip:** Always keep a copy of your raw data. Never transform the original —
> work on a copy (`df = raw.copy()`) or write idempotent pipeline functions.
