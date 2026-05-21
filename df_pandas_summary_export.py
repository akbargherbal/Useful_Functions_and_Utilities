import pandas as pd
import io
from pathlib import Path


def export_dataframe_summary(
    df,
    output_path="dataframe_summary.txt",
    n_samples=5,
    include_value_counts=True,
    max_unique_show=20,
):
    """
    Export a comprehensive summary of a pandas DataFrame to a text file.

    Parameters:
    -----------
    df : pd.DataFrame
        The DataFrame to summarize
    output_path : str or Path
        Path where the summary file will be saved
    n_samples : int
        Number of sample rows to include (default: 5)
    include_value_counts : bool
        Whether to include value counts for categorical columns (default: True)
    max_unique_show : int
        Maximum number of unique values to show for categorical columns (default: 20)

    Returns:
    --------
    str : Path to the created file
    """

    with open(output_path, "w", encoding="utf-8") as f:
        # Header
        f.write("=" * 80 + "\n")
        f.write("PANDAS DATAFRAME SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        # Basic info
        f.write("BASIC INFORMATION\n")
        f.write("-" * 80 + "\n")
        f.write(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n")
        f.write(
            f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n\n"
        )

        # DataFrame.info()
        f.write("COLUMN INFORMATION\n")
        f.write("-" * 80 + "\n")
        buffer = io.StringIO()
        df.info(buf=buffer, memory_usage="deep")
        f.write(buffer.getvalue())
        f.write("\n")

        # Missing values summary
        missing = df.isnull().sum()
        if missing.sum() > 0:
            f.write("MISSING VALUES\n")
            f.write("-" * 80 + "\n")
            missing_pct = (missing / len(df) * 100).round(2)
            missing_df = pd.DataFrame(
                {
                    "Missing Count": missing[missing > 0],
                    "Percentage": missing_pct[missing > 0],
                }
            ).sort_values("Missing Count", ascending=False)
            f.write(missing_df.to_string())
            f.write("\n\n")
        else:
            f.write("MISSING VALUES: None\n\n")

        # Statistical summary
        f.write("STATISTICAL SUMMARY (Numeric Columns)\n")
        f.write("-" * 80 + "\n")
        if len(df.select_dtypes(include="number").columns) > 0:
            f.write(df.describe().to_string())
            f.write("\n\n")
        else:
            f.write("No numeric columns found.\n\n")

        # Categorical column summary
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        if len(cat_cols) > 0 and include_value_counts:
            f.write("CATEGORICAL COLUMNS SUMMARY\n")
            f.write("-" * 80 + "\n")
            for col in cat_cols:
                n_unique = df[col].nunique()
                f.write(f"\n{col}:\n")
                f.write(f"  Unique values: {n_unique}\n")

                if n_unique <= max_unique_show:
                    f.write(f"  Value counts:\n")
                    value_counts = df[col].value_counts()
                    for val, count in value_counts.items():
                        pct = count / len(df) * 100
                        f.write(f"    {val}: {count} ({pct:.1f}%)\n")
                else:
                    f.write(f"  Top {max_unique_show} values:\n")
                    value_counts = df[col].value_counts().head(max_unique_show)
                    for val, count in value_counts.items():
                        pct = count / len(df) * 100
                        f.write(f"    {val}: {count} ({pct:.1f}%)\n")
            f.write("\n")

        # Sample rows
        f.write(f"SAMPLE ROWS (n={n_samples})\n")
        f.write("-" * 80 + "\n")
        sample = df.sample(n=min(n_samples, len(df)), random_state=42)
        f.write(sample.to_string())
        f.write("\n\n")

        # First few rows
        f.write(f"FIRST {min(3, len(df))} ROWS\n")
        f.write("-" * 80 + "\n")
        f.write(df.head(3).to_string())
        f.write("\n\n")

        # Column list for easy reference
        f.write("COLUMN NAMES LIST\n")
        f.write("-" * 80 + "\n")
        f.write(", ".join(df.columns.tolist()))
        f.write("\n\n")

        f.write("=" * 80 + "\n")
        f.write("END OF SUMMARY\n")
        f.write("=" * 80 + "\n")

    return str(Path(output_path).absolute())


# Example usage
if __name__ == "__main__":
    # Create a sample DataFrame
    sample_data = {
        "id": range(1, 101),
        "name": [f"Person_{i}" for i in range(1, 101)],
        "age": pd.np.random.randint(18, 80, 100),
        "city": pd.np.random.choice(["NYC", "LA", "Chicago", "Houston"], 100),
        "salary": pd.np.random.randint(30000, 150000, 100),
        "department": pd.np.random.choice(["Sales", "Engineering", "Marketing"], 100),
    }
    df = pd.DataFrame(sample_data)

    # Add some missing values
    df.loc[df.sample(10).index, "salary"] = pd.NA

    # Export summary
    output_file = export_dataframe_summary(df, "my_dataframe_summary.txt")
    print(f"Summary exported to: {output_file}")
