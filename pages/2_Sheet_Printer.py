import os
import shutil
import pandas as pd
import numpy as np
from openpyxl.utils.cell import get_column_letter
import streamlit as st

st.set_page_config(layout="wide",
                   page_title="101L Tools - Sheet Printer")

st.title("101L Sheet Printer")

if os.path.isdir("grade_sheets"):
    shutil.rmtree("grade_sheets")

if os.path.exists("grade_sheets.zip"):
    os.remove("grade_sheets.zip")

os.makedirs("grade_sheets")

st.subheader("Upload your Canvas CSV file")
fn = st.file_uploader("Upload your Canvas .CSV file", type=["csv"], accept_multiple_files=False, label_visibility="collapsed")

st.subheader("Upload your ARS XLSX file")
ars_fn = st.file_uploader("Upload your ARS .XLSX file", type=["xlsx"], accept_multiple_files=False, label_visibility="collapsed")

st.subheader("Options")
ars_to_normal_override = st.checkbox("Override ARS grades to the normal if ARS quiz grade column is higher than normal grade column, or if the normal grade column is blank.", value=True)

warning_placeholder = st.empty()

if not fn and not ars_fn:
    warning_placeholder.empty()
    warning_placeholder.warning("Please upload both your Canvas and ARS files above.")
elif not ars_fn:
    warning_placeholder.empty()
    warning_placeholder.warning("Please upload your ARS file above.")
elif not fn:
    warning_placeholder.empty()
    warning_placeholder.warning("Please upload your Canvas file above.")
else:
    grades_df = pd.read_csv(fn, encoding='latin1')
    ars_df = pd.read_excel(ars_fn)

    ars_pid_col = ars_df["PID"]
    sum_columns = []
    for c in grades_df.columns:
        try:
            points_possible = float(grades_df[c][0])
        except ValueError:
            continue

        if all([points_possible != float('nan'),
                points_possible != np.nan,
                str(points_possible) != 'nan']):
            sum_columns.append(c)

    cleaned_grades_list = []
    for _, row in grades_df.iterrows():
        row_dict = {}
        for c in row.keys():
            if c in sum_columns:
                try:
                    row_dict[c] = float(row[c])
                except ValueError:
                    row_dict[c] = 0
            else:
                row_dict[c] = row[c]

        cleaned_grades_list.append(row_dict)

    grades_df = pd.DataFrame.from_dict(cleaned_grades_list)
    grades_df.sort_values(by=["Section", "Student"], inplace=True)
    sum_columns = [c for c in sum_columns if "Roll" not in c]
    sum_indices = [[i, c] for i, c in enumerate(sum_columns)]
    ars_indices = []

    for i, c in sum_indices:
        if "ars" in c.lower():
            ars_indices.append(i)

    ars_idx = []
    for idx, v in enumerate(grades_df["SIS User ID"]):
        if str(v).lower() != 'nan' and int(v) in list(ars_pid_col):
            ars_idx.append(idx)

    sums_df = grades_df[sum_columns]
    sums_row_list = []
    for idx, row in sums_df.iterrows():
        row_keys = list(row.keys())

        if idx in ars_idx or ars_to_normal_override:
            for ars_index in ars_indices:
                if str(row[row_keys[ars_index - 1]]).lower().strip() in ['', "nan",]:
                    row[row_keys[ars_index - 1]] = 0

                if str(row[row_keys[ars_index]]).lower().strip() in ['', "nan"]:
                    row[row_keys[ars_index]] = 0

                if row[row_keys[ars_index]] > row[row_keys[ars_index - 1]]:
                    row[row_keys[ars_index - 1]] = row[row_keys[ars_index]]

        row = {k: row[k] for k in row_keys if "ars" not in k.lower()}
        sums_row_list.append(row)



    sums_df = pd.DataFrame.from_dict(sums_row_list)
    sums_df['Total Points'] = sums_df.sum(axis=1)
    sums_cols = list(sums_df.columns)
    sums_cols.remove("Total Points")

    sums_str_list = []

    grade_cutoffs = {
        'A': 136,
        'A-': 132,
        'B+': 131,
        'B': 125,
        'B-': 119,
        'C+': 115.5,
        'C': 108.5,
        'C-': 105,
        'D+': 96,
        'D': 82.5
    }

    for _, row in sums_df.iterrows():
        row_dict = {}
        for letter_grade, number_grade in grade_cutoffs.items():
            pass
            # if row["Total Points"] > number_grade:
            #     row["Calcd"] = letter_grade
            #     break

        for c in row.keys():
            if str(row[c]).lower() == 'nan':
                row_dict[c] = ''
            else:
                row_dict[c] = str(row[c]).replace('.0', '')

        sums_str_list.append(row_dict)
    sums_df = pd.DataFrame.from_dict(sums_str_list)

    # column_order = ["Student", "Letter", "Calcd", "Total Points", "Section"] + sums_cols
    column_order = ["Student", "Letter", "Total Points", "Section"] + sums_cols

    sums_df["Section"] = grades_df["Section"].values
    sums_df["Student"] = grades_df["Student"].values
    sums_df["Letter"] = [" " for _ in range(len(grades_df))]

    sums_df = sums_df[column_order]
    writer = pd.ExcelWriter(f"grade_sheets/all_calc_printsheet.xlsx")
    workbook = writer.book
    for section in sums_df["Section"].unique():
        include_columns = [c for c in sums_df.columns if "Section" not in c]

        if type(section) == str and all(["nan" not in section,
                                         "and" not in section]):

            section_df = sums_df[sums_df["Section"] == section][include_columns]
            section_df.to_excel(writer, index=False, header=False, startrow=2, sheet_name=section)

            format = workbook.add_format({'bold': True})
            format.set_rotation(90)
            format_title = workbook.add_format({'bold': True, 'font_size': 27})
            format_title.set_center_across()
            format_bold = workbook.add_format({'bold': True})

            last_grade_column = get_column_letter(len(include_columns))
            column_widths = [('A:A', 20),
                             ('B:B', 7),
                             (f'C:{last_grade_column}', 5)]
            for col, width in column_widths:
                writer.sheets[section].set_column(col, width)

            writer.sheets[section].merge_range(f'A1:{last_grade_column}1', section, format_title)
            writer.sheets[section].write(1, 0, include_columns[0], format_bold)
            writer.sheets[section].write(1, 1, include_columns[1], format_bold)
            for i in range(2, len(include_columns)):
                writer.sheets[section].write(1, i, include_columns[i][:40], format)

            writer.sheets[section].set_landscape()
            writer.sheets[section].hide_gridlines(0)
            writer.sheets[section].fit_to_pages(1, 1)

    workbook.close()

    with open("grade_sheets/all_calc_printsheet.xlsx", "rb") as file:
        st.markdown("### Download Formatted Printer Spreadsheet below")
        st.info("Your spreadsheet is ready! Please click the download button below.")
        st.download_button(
            label="Download Formatted Printer Spreadsheet",
            data=file,
            file_name='all_calc_spreadsheet.xlsx',
            mime='text/csv',
        )