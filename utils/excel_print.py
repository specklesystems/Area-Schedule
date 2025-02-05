import pandas as pd
import seaborn as sns
import matplotlib.colors as mcolors

def print_scheduled_excel(df_pivot_tables, scheduled_titles, output_file):

    # Get a color palette from Seaborn
    palette = sns.color_palette("Set2", n_colors=20)  # Get 20 colors from the "Set2" palette

    # Convert colors to hex format
    hex_colors = [mcolors.to_hex(color) for color in palette]  # Correct conversion

    # Create an Excel writer
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        start_row = 3  # Initial row position
        last_rows = []  # Store last rows of each DataFrame
        df_names = []  # Store column names for each DataFrame

        for i, (df, title) in enumerate(zip(df_pivot_tables, scheduled_titles)):
            df.to_excel(writer, sheet_name="Sheet1", startrow=start_row, index=False)

            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets["Sheet1"]

            # Create a format for the title (18pt font, bold, centered)
            title_format = workbook.add_format({
                "bold": True,
                "font_size": 18,
                "align": "center",
                "valign": "vcenter"
            })

            # Merge first two columns (A and B) for the title
            worksheet.merge_range(start_row-1, 0, start_row-3, 3, title, title_format)

            # Define border format for all cells
            border_format = workbook.add_format({"border": 1})

            # Apply a different color to each header using the Seaborn palette
            for col_num, col_name in enumerate(df.columns):
                color = hex_colors[col_num % len(hex_colors)]  # Cycle through colors if needed
                header_format = workbook.add_format({
                    "bold": True,
                    "bg_color": color,  # Color from Seaborn palette
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter"
                })
                worksheet.write(start_row, col_num, col_name, header_format)  # Apply only header format

            # Apply border format to all data cells
            num_rows, num_cols = df.shape
            for row in range(start_row + 1, start_row + num_rows + 1):  # +1 to skip header
                for col in range(num_cols):
                    worksheet.write(row, col, df.iloc[row - start_row - 1, col], border_format)

            # Store last row for bar chart
            last_rows.append(df.iloc[-1].values)  # Store last row values
            df_names.append(list(df.columns))  # Store column names

            start_row += len(df) + 6  # Move the start row for the next DataFrame

        # Insert Bar Charts Below the DataFrames
        chart_start_row = start_row + 2  # Leave some space after last DataFrame

        for i, (last_row, col_names, title) in enumerate(zip(last_rows, df_names, scheduled_titles)):
            chart = workbook.add_chart({"type": "column"})  # Create a bar chart

            # Add data for the last row as a series in the chart
            for col_idx, col_name in enumerate(col_names):
                chart.add_series({
                    "name": col_name,  # Column name as label
                    "categories": [worksheet.name, chart_start_row, 0, chart_start_row, len(col_names) - 1],  # X-axis
                    "values": [worksheet.name, chart_start_row + 1, col_idx, chart_start_row + 1, col_idx],  # Y-axis
                    "fill": {"color": hex_colors[col_idx % len(hex_colors)]}  # Bar color
                })

            # Set chart title and axes labels
            chart.set_title({"name": f"{title}"})
            chart.set_x_axis({"name": "Columns"})
            chart.set_y_axis({"name": "Value"})

            # **Set chart size (increase width and height)**
            chart.set_size({"width": 800, "height": 400})  # Adjust size as needed

            # Insert data for the chart in the worksheet
            worksheet.write_row(chart_start_row, 0, col_names)  # Column names (X-axis)
            worksheet.write_row(chart_start_row + 1, 0, last_row)  # Last row values (Y-axis)

            # Insert chart into worksheet
            worksheet.insert_chart(chart_start_row + 3, 0, chart)

            # Move to the next chart position
            chart_start_row += 25  # Add spacing for the next chart

    return output_file