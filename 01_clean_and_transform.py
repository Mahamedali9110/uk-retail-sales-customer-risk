import pandas as pd

sheets = pd.read_excel('Online Retail.xlsx', sheet_name=None)
df = pd.concat(sheets.values(), ignore_index=True)

print(df.shape)
print(df.head())
print(df.dtypes)

# Missing customer IDs
print("Missing CustomerID:", df['CustomerID'].isna().sum())

# Cancellations (InvoiceNo starting with 'C')
print("Cancellations:", df['InvoiceNo'].astype(str).str.startswith('C').sum())

# Negative quantities
print("Negative quantities:", (df['Quantity'] < 0).sum())

# Zero or negative prices
print("Zero/negative prices:", (df['UnitPrice'] <= 0).sum())

# Exact duplicate rows
print("Duplicate rows:", df.duplicated().sum())


# Drop exact duplicate rows
df = df.drop_duplicates()

# Remove rows with invalid prices
df = df[df['UnitPrice'] > 0]

# Flag cancellations
df['IsCancellation'] = df['InvoiceNo'].astype(str).str.startswith('C')

# Calculate line total (revenue per row)
df['LineTotal'] = (df['Quantity'] * df['UnitPrice']).round(2)

print("Final shape after cleaning:", df.shape)
print(df[['InvoiceNo', 'Quantity', 'UnitPrice', 'LineTotal', 'IsCancellation']].head())


# Build customer summary (only real customers, excluding cancellations)
# Resolve one country per customer (their most frequent country)
customer_country = (
    df[df['CustomerID'].notna()]
    .groupby(['CustomerID', 'Country'])
    .size()
    .reset_index(name='country_count')
    .sort_values(['CustomerID', 'country_count'], ascending=[True, False])
    .drop_duplicates(subset='CustomerID', keep='first')[['CustomerID', 'Country']]
)

customer_summary = (
    df[(df['CustomerID'].notna()) & (~df['IsCancellation'])]
    .groupby('CustomerID')
    .agg(
        num_orders=('InvoiceNo', 'nunique'),
        total_spend=('LineTotal', 'sum'),
        last_order_date=('InvoiceDate', 'max')
    )
    .reset_index()
    .merge(customer_country, on='CustomerID', how='left')
)

def segment(spend):
    if spend > 2000:
        return 'High Value'
    elif spend > 500:
        return 'Mid Value'
    else:
        return 'Low Value'

customer_summary['ValueSegment'] = customer_summary['total_spend'].apply(segment)

print("Customer summary shape:", customer_summary.shape)
print(customer_summary['ValueSegment'].value_counts())

# Export everything
df.to_csv('sales_clean.csv', index=False)
customer_summary.to_csv('customer_summary.csv', index=False)

print("Export complete.")