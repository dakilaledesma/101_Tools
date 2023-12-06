import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("101L Grade Visualizer")
canvas_grade_file = st.file_uploader("Upload your Canvas CSV file", type=["csv"], accept_multiple_files=False)
if canvas_grade_file is not None:
    canvas_df = pd.read_csv(canvas_grade_file)

    grading_cols = []
    for col in canvas_df.columns:
        if all([type(canvas_df[col][0]) != str,
                canvas_df[col][0] != np.nan,
                str(canvas_df[col][0]) != "nan",
                "roll call" not in col.lower()]):
            grading_cols.append(col)

    canvas_grade_df = canvas_df[grading_cols]

    sums = []
    for _, row in canvas_grade_df.iterrows():
        sums.append(row.sum())

    canvas_grade_df["sum"] = sums
    canvas_grade_df["PID"] = canvas_df["SIS User ID"]
    canvas_grade_df["Section"] = canvas_df["Section"]

    canvas_grade_df = canvas_grade_df[canvas_grade_df["PID"].notna()]
    canvas_grade_df = canvas_grade_df[~canvas_grade_df['Section'].str.contains(',', na=False)]
    canvas_grade_df = canvas_grade_df.sort_values(by=['Section'])


    sections = canvas_grade_df["Section"].unique()

    cutoffs_col, graph_col = st.columns([0.3, 0.7])

    with cutoffs_col:
        a_cutoff = st.number_input("A cutoff", value=136.0)
        a_minus_cutoff = st.number_input("A- cutoff", value=132.0)
        b_plus_cutoff = st.number_input("B+ cutoff", value=129.0)
        b_cutoff = st.number_input("B cutoff", value=125.0)
        b_minus_cutoff = st.number_input("B- cutoff", value=119.0)
        c_plus_cutoff = st.number_input("C+ cutoff", value=115.5)
        c_cutoff = st.number_input("C cutoff", value=110.0)
        c_minus_cutoff = st.number_input("C- cutoff", value=105.0)
        d_plus_cutoff = st.number_input("D+ cutoff", value=96.0)
        d_cutoff = st.number_input("D cutoff", value=82.5)
        f_cutoff = st.number_input("F cutoff", value=0.0)

    with graph_col:
        graph_container = st.empty()
        graph_container.info("Loading the graph...")

    def count_students(df, grade_ranges):
        counts = {}
        for grade, (lower, upper) in grade_ranges.items():
            counts[grade] = df[(df["sum"] >= lower) & (df["sum"] < upper)].shape[0]
            print(df[(df["sum"] >= lower) & (df["sum"] < upper)].shape)
        return counts


    # Define the grade ranges
    grade_ranges = {
        'A': (a_cutoff, float('inf')),
        'A-': (a_minus_cutoff, a_cutoff),
        'B+': (b_plus_cutoff, a_minus_cutoff),
        'B': (b_cutoff, b_plus_cutoff),
        'B-': (b_minus_cutoff, b_cutoff),
        'C+': (c_plus_cutoff, b_minus_cutoff),
        'C': (c_cutoff, c_plus_cutoff),
        'C-': (c_minus_cutoff, c_cutoff),
        'D+': (d_plus_cutoff, c_minus_cutoff),
        'D': (d_cutoff, d_plus_cutoff),
        'F': (f_cutoff, d_cutoff)
    }

    # Calculate the maximum count across all sections
    max_count = 0
    for section in sections:
        section_df = canvas_grade_df[canvas_grade_df["Section"] == section]
        section_counts = count_students(section_df, grade_ranges)
        max_count = max(max_count, max(section_counts.values()))

    # Create a figure with subplots
    n_sections = len(sections) + 1  # +1 for the combined section
    n_cols = 3
    n_rows = np.ceil(n_sections / n_cols)
    fig, axs = plt.subplots(int(n_rows), n_cols, figsize=(15, 5 * n_rows))
    plt.subplots_adjust(hspace=0.5, wspace=0.3)

    # Plot for all sections combined
    combined_counts = count_students(canvas_grade_df, grade_ranges)
    axs[0, 0].bar(combined_counts.keys(), combined_counts.values())
    axs[0, 0].set_title("All Sections")
    axs[0, 0].set_xlabel("Grade Range")
    axs[0, 0].set_ylabel("Number of Students")

    # Plot for each section
    for idx, section in enumerate(sections, start=1):
        row, col = divmod(idx, n_cols)
        section_df = canvas_grade_df[canvas_grade_df["Section"] == section]
        section_counts = count_students(section_df, grade_ranges)
        axs[row, col].bar(section_counts.keys(), section_counts.values())
        axs[row, col].set_title(f"Section {section}")
        axs[row, col].set_xlabel("Grade Range")
        axs[row, col].set_ylabel("Number of Students")
        axs[row, col].set_ylim([0, max_count])  # Set y-axis limit
    # Hide any unused subplots:
    print(len(sections) + 1, int(n_rows * n_cols))
    for idx in range(len(sections) + 1, int(n_rows * n_cols)):
        row, col = divmod(idx, n_cols)
        axs[row, col].axis('off')

    with graph_col:
        graph_container.empty()
        graph_container.pyplot(fig)


