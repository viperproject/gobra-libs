"""Module for plotting the results of profile.py."""

import argparse
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from util import file_path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("csv_path", type=program_path, nargs="+", help="CSV files to be analyzed")
    parser.add_argument("--filter_anonymous", action="store_true", required=False,
                        help="filter out anonymous quantifier instantiations like quant-u-17 and k!512.")
    parser.add_argument("--name", type=str, required=False,
                        help="Prefix for the output files.")
    parser.add_argument("--top", type=int, required=False,
                        help="Plot only the top n quantifiers")
    parser.add_argument("--variants", type=str, nargs="+", required=False,
                        help="Names of the variants in the plot (only works with multiple CSV files).")
    parser.add_argument("--qi_size", type=int, nargs=2, required=False, default=[6, 4],
                        help="Size of the quantifier instantiation plot (width height)")
    parser.add_argument("--execution_time_size", type=int, nargs=2, required=False, default=[6, 4],
                        help="Size of the execution time plot (width height)")
    parser.add_argument("--start_at_zero_qi", action="store_true", required=False,
                        help="Start the axis for the number of quantifier instantiations at zero.")
    parser.add_argument("--start_at_zero_execution_time", action="store_true", required=False,
                        help="Start the axis for execution time at zero.")

    return parser.parse_args()


def main():
    """Main function of the plotter."""
    # Parse arguments
    args = parse_args()

    if (args.variants is not None) and (len(args.csv_path) != len(args.variants)):
        raise argparse.ArgumentTypeError(f"Number of variants must match the number of CSV files")

    if len(args.csv_path) == 1:
        plot(args, args.csv_path[0])
    else:
        plot_multiple(args, args.csv_path)


def plot(args, csv_path):
    """Plot a single CSV file."""
    if args.name is None:
        args.name = csv_path.with_suffix("")

    # Read CSV file using pandas.
    df = pd.read_csv(csv_path)

    # Remove "qi-" from column names that start with it.
    df.columns = df.columns.str.replace('qi-', '')

    # Remove columns that start with "quant-u" or "k!".
    if args.filter_anonymous:
        df = df.filter(regex='^(?!quant-u|k!).*$', axis=1)

    # Split the DataFrame into two DataFrames: one with only the 'execution_time' column and one with all other columns.
    execution_time_df = df[['execution_time']]
    qi_df = df.drop(columns=['execution_time'])

    # Determine Top Quantifiers if needed
    if args.top is not None:
        top_quantifiers = qi_df.median(numeric_only=True).nlargest(args.top).index
        qi_df = qi_df.loc[:, list(top_quantifiers)]

    qi_df = qi_df.sort_values(by=qi_df.index[0], ascending=False, axis=1)

    sns.set_theme(rc={'figure.figsize': args.qi_size})

    # Generate plot for quantifier instantiations.
    plt.figure()  # Create a new figure

    if len(df) == 1:
        sns.barplot(qi_df, orient='h')
    else:
        sns.boxplot(qi_df, orient='h')

    if args.start_at_zero_qi:
        plt.xlim(0, None)

    plt.tight_layout()
    plt.savefig((str(args.name) + ".qi.pdf"), dpi=600)
    plt.close()

    # Generate plot for execution time if we have more than one measurement
    sns.set_theme(rc={'figure.figsize': args.execution_time_size})
    if len(df) > 1:
        plt.figure()

        # Calculate median, quartiles, and IQR
        median = execution_time_df['execution_time'].median()
        quartile1 = execution_time_df['execution_time'].quantile(0.25)
        quartile3 = execution_time_df['execution_time'].quantile(0.75)
        iqr = quartile3 - quartile1

        # Identify outliers
        outliers = execution_time_df[(execution_time_df < (quartile1 - 1.5 * iqr)) |
                                     (execution_time_df > (quartile3 + 1.5 * iqr))]

        # Plot histogram
        sns.histplot(execution_time_df)

        # Overlay the median and quartiles using Matplotlib
        plt.axvline(median, color='red', linestyle='--', label='Median')
        plt.axvline(quartile1, color='green', linestyle='--', label='1st Quartile (Q1)')
        plt.axvline(quartile3, color='green', linestyle='--', label='3rd Quartile (Q3)')

        # Plot the outliers as individual points
        plt.scatter(outliers['execution_time'], np.zeros(len(outliers)), color='orange', s=30, label='Outliers')

        plt.title('Histogram of Execution Times with Quartiles and Median')

        if args.start_at_zero_execution_time:
            plt.xlim(0, None)

        plt.xlabel('Execution Time (seconds)', labelpad=15)
        plt.ylabel('Frequency', labelpad=15)
        plt.legend()
        plt.savefig((str(args.name) + ".execution_time.pdf"), dpi=600)
        plt.close()


def plot_multiple(args, csv_paths):
    """Plot multiple CSV files on the same graph."""
    # Default value for variant name
    if args.variants is None:
        args.variants = [csv_path.stem.split("-")[0] for csv_path in csv_paths]

    # Load csv files and set the variant name
    # Note that zip won't ignore extra elements in the longer list since they have the same length (checked in main)
    dfs = []
    for csv_path, variant in zip(csv_paths, args.variants):
        df = pd.read_csv(csv_path)
        df['Variant'] = variant
        dfs.append(df)

    # Remove "qi-" from column names that start with it.
    for df in dfs:
        df.columns = df.columns.str.replace('qi-', '')

    if args.filter_anonymous:
        # Remove columns that start with "quant-u" or "k!".
        dfs = [df.filter(regex='^(?!quant-u|k!).*$', axis=1) for df in dfs]

    # Split the DataFrames into two DataFrames: one with only the 'execution_time' column and one with all other
    # columns.
    execution_time_dfs = [df[['execution_time']] for df in dfs]
    qi_dfs = [df.drop(columns=['execution_time']) for df in dfs]

    if args.top is not None:
        # Determine Top Quantifiers for Each DataFrame
        top_quantifiers_sets = []
        for df in qi_dfs:
            top_quantifiers = df.median(numeric_only=True).nlargest(args.top).index
            top_quantifiers_sets.append(set(top_quantifiers))

        # Take the Union of Top Quantifiers
        union_top_quantifiers = set.union(*top_quantifiers_sets)

        # Filter Each DataFrame on the Union of Top Quantifiers
        qi_dfs_filtered = []
        for df in qi_dfs:
            # Keep 'Variant' column and any quantifier in the union of top quantifiers
            columns_to_keep = ['Variant'] + list(union_top_quantifiers.intersection(df.columns))
            qi_dfs_filtered.append(df.loc[:, columns_to_keep])

        # Now qi_dfs_filtered contains the DataFrames filtered to include only the union of top quantifiers
        qi_dfs = qi_dfs_filtered

    # Sort each DataFrame in qi_dfs by the median number of instantiations
    sorted_qi_dfs = []
    for df in qi_dfs:
        # Calculate the median of each column
        medians = df.median(numeric_only=True).sort_values(ascending=False)
        # Sort the DataFrame based on the calculated medians
        sorted_df = df.loc[:, df.columns.intersection(['Variant']).append(medians.index)]
        sorted_qi_dfs.append(sorted_df)

    # Now, sorted_qi_dfs contains the sorted DataFrames
    qi_dfs = sorted_qi_dfs

    # Combine the DataFrames into a single DataFrame for plotting
    qi_cdf = pd.concat(qi_dfs)
    qi_mdf = qi_cdf.melt(id_vars="Variant", var_name="quantifier", value_name="instantiations")

    sns.set_theme(rc={'figure.figsize': args.qi_size})
    plt.figure()

    if len(qi_dfs[0]) == 1:
        sns.barplot(x='instantiations', y='quantifier', hue='Variant', data=qi_mdf, orient="h")
    else:
        sns.boxplot(x='instantiations', y='quantifier', hue='Variant', data=qi_mdf, orient="h")

    if args.start_at_zero_qi:
        plt.xlim(0, None)

    plt.xlabel('Number of Instantiations', labelpad=15)
    plt.ylabel('Quantifier', labelpad=15)
    plt.tight_layout()

    if args.name is None:
        args.name = "multi"

    plt.savefig(f"{args.name}.qi.pdf", dpi=600)
    plt.close()

    sns.set_theme(rc={'figure.figsize': args.execution_time_size})

    # Combine DataFrames and rename the columns to the variant names
    execution_time_cdf = pd.concat(execution_time_dfs, axis=1)
    execution_time_cdf.columns = args.variants

    plt.figure()

    sns.boxplot(execution_time_cdf)

    if args.start_at_zero_execution_time:
        plt.ylim(0, None)
    plt.xlabel('Variant', labelpad=15)
    plt.ylabel('Execution time (s)', labelpad=15)

    plt.tight_layout()
    plt.savefig(f"{args.name}.execution_time.pdf", dpi=600)
    plt.close()


def program_path(string):
    """Checks that the string is a valid path to a CSV file."""
    path = file_path(string)
    if path.suffix != ".csv":
        raise argparse.ArgumentTypeError(f"Wrong suffix: {path} is not a valid path to a CSV file")

    return path


if __name__ == '__main__':
    main()
