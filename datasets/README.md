# Sample Datasets

This directory contains sample datasets for testing MustaCHE clustering.

## Available Datasets

### 1. simple_2d.csv
- **Points**: 9
- **Dimensions**: 2
- **Clusters**: 3 well-separated groups
- **Labels**: `simple_2d_labels.csv`
- **Use case**: Quick testing and demo

### 2. sample_data.csv
- **Points**: 11
- **Dimensions**: 2
- **Clusters**: 3 groups
- **Labels**: `sample_labels.csv`
- **Use case**: Basic clustering validation

## How to Use

1. Go to MustaCHE home page
2. Click "Choose File" under Dataset
3. Select a `.csv` file from this folder
4. (Optional) Upload corresponding `_labels.csv` for validation metrics
5. Click "Run Clustering"

## Dataset Format

CSV files should contain:
- **No headers**
- **Only numerical values**
- **One row per data point**
- **Comma-separated features**

Example:
```
1.2,3.4
2.1,4.3
5.6,7.8
```

## Labels Format

One label per line, matching the order of data points:
```
0
0
1
```

## Adding Your Own Datasets

You can upload any CSV file with numerical data. MustaCHE will:
- Automatically detect the number of features
- Run HDBSCAN clustering
- Generate interactive visualizations

**Tip**: For best results, use datasets with at least 10-20 points.
