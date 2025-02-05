"""This module contains the function's business logic.

Use the automation_context module to wrap your function in an Automate context helper.
"""
import pandas as pd
from datetime import datetime

from pydantic import Field, SecretStr
from speckle_automate import (
    AutomateBase,
    AutomationContext,
    execute_automate_function,
)

from utils.flatten import flatten_base
from utils.data_extraction import get_properties_for_list, create_pivot_tables
from utils.excel_print import print_scheduled_excel


class FunctionInputs(AutomateBase):
    """These are function author-defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    file_name: str = Field(
        title="File Name",
        description="The name of the Excel file.",
    )

    inlcude_areas: bool = Field(
        title="Calculate Areas",
        description="If CHECKED it will calculate the area of all Areas in the model.",
        default= True
    )

    inlcude_rooms: bool = Field(
        title="Calculate Rooms",
        description="If CHECKED it will calculate the area of all Rooms in the model.",
        default= False
    )

    nua_list: str = Field(
        title="NUA (Nett Usable Area)",
        strict= False
    )

    nia_list: str = Field(
        title="NIA (Nett Internal Area)",
        strict= False
    )

    nla_list: str = Field(
        title="NLA (Nett Leasable Area)",
        strict= False
    )

    gia_list: str = Field(
        title="GIA (Gross Internal Area)",
        strict= False
    )

    gea_list: str = Field(
        title="GEA (Gross External Area)",
        strict= False
    )

    gla_list: str = Field(
        title="GLA (Gross Leasable Area)",
        strict= False
    )

    gba_list: str = Field(
        title="GBA (Gross Building Area)",
        strict= False
    )


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """This is an example Speckle Automate function.

    Args:
        automate_context: A context-helper object that carries relevant information
            about the runtime context of this function.
            It gives access to the Speckle project data that triggered this run.
            It also has convenient methods for attaching result data to the Speckle model.
        function_inputs: An instance object matching the defined schema.
    """
    # The context provides a convenient way to receive the triggering version.
    version_root_object = automate_context.receive_version()

    file_name = function_inputs.file_name

    areas_status = function_inputs.inlcude_areas
    rooms_status = function_inputs.inlcude_rooms

    NUA = [prop.strip() for prop in function_inputs.nua_list.split(",")]
    NIA = [prop.strip() for prop in function_inputs.nia_list.split(",")]
    NLA = [prop.strip() for prop in function_inputs.nla_list.split(",")]
    GIA = [prop.strip() for prop in function_inputs.gia_list.split(",")]
    GEA = [prop.strip() for prop in function_inputs.gea_list.split(",")]
    GLA = [prop.strip() for prop in function_inputs.gla_list.split(",")]
    GBA = [prop.strip() for prop in function_inputs.gba_list.split(",")]

    all_objects = list(flatten_base(version_root_object))
    
    filter_categories = []

    if rooms_status:
        filter_categories.append("Rooms")
    if areas_status:
        filter_categories.append("Areas")

    if not filter_categories:
        print("To make calculations you need to select one of the two options or both. Areas or/and Rooms")
        automate_context.mark_run_failed("To make calculations you need to select one of the two options or both. Areas or/and Rooms")
        return

    items = []
    id_lists = []

    for i in all_objects:
        if hasattr(i, "category"):  # Check if the object has the "category" attribute
            if i.category in filter_categories:  # Check if the category matches the filter list
                items.append(i)  # Append the whole object to the items list
                id_lists.append(i.id)
        else:
            continue  # Skip if "category" does not exist

    # List of properties
    list_prop = [
        "category",
        "level.name",
        "properties.Parameters.Instance Parameters.Identity Data.Name.value",
        "properties.Parameters.Instance Parameters.Dimensions.Area.value",
    ]

    try:

        final_properties = get_properties_for_list(items, list_prop)

        # Convert to a DataFrame
        df = pd.DataFrame(final_properties)

        df.columns = ["category","level","name","area"]

        df_pivot_tables = create_pivot_tables(filter_categories, df)

        #NUA = []
        #NIA = ["Café","Café Kitchen","Common"]
        #NLA = ["Café","Café Kitchen","Common","Elevator E1","Level 5 Gross","Live/Work Unit"]

        # Create new DataFrame with grouped sums
        df_grouped = pd.DataFrame({
            "level": df["level"].unique(),  # Ensure all levels are present
            "NUA": sum_group(df, NUA).values,  # Handles empty group
            "NIA": sum_group(df, NIA).values,
            "NLA": sum_group(df, NLA).values,
            "GIA": sum_group(df, GIA).values,
            "GEA": sum_group(df, GEA).values,
            "GLA": sum_group(df, GLA).values,
            "GBA": sum_group(df, GBA).values
        })

        # Add total row
        df_grouped.loc["Total"] = df_grouped.select_dtypes(include="number").sum()
        df_grouped.loc["Total", "level"] = "Total"

        df_pivot_tables.append(df_grouped)

        titles = filter_categories
        titles.append("KPIs")

        scheduled_titles = ["Schedule " + word for word in titles]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        xlsx_filename = f"{file_name}_{timestamp}.xlsx"

        output_file = print_scheduled_excel(df_pivot_tables, scheduled_titles, xlsx_filename)

        automate_context.store_file_result(f"./{output_file}")
        automate_context.mark_run_success("All data sent successfully! Download your file below.")
    except:
        automate_context.mark_run_failed("An error occurred while writing to the file. Ensure that the parameters 'Level,' 'Name,' and 'Area' exist. Additionally, verify that the area/room names are correctly typed and separated by commas.") 


# Function to sum area for each group, ensuring missing levels return 0
def sum_group(df, group):
    if not group:  # If the group is empty, return a series of 0s
        return pd.Series(0, index=df["level"].unique())
    grouped = df[df["name"].isin(group)].groupby("level")["area"].sum()
    return grouped.reindex(df["level"].unique(), fill_value=0)  # Ensure all levels exist, fill missing with 0


# make sure to call the function with the executor
if __name__ == "__main__":
    # NOTE: always pass in the automate function by its reference; do not invoke it!

    # Pass in the function reference with the inputs schema to the executor.
    execute_automate_function(automate_function, FunctionInputs)

    # If the function has no arguments, the executor can handle it like so
    # execute_automate_function(automate_function_without_inputs)
