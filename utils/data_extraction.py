def get_nested_attr(obj, attr_path, default=None):
    """
    Safely get a nested attribute or dictionary key using a dot-separated path.
    """
    try:
        parts = attr_path.split('.')
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part, default)
            else:
                obj = getattr(obj, part, default)

            if obj is None:
                return default

        return obj
    except AttributeError:
        return default
    

def get_properties_for_object(obj, list_prop):
    """
    Retrieve specified properties for a single object based on a list of property paths.
    """
    result = {}
    for prop in list_prop:
            result[prop] = get_nested_attr(obj, prop)

    return result

def get_properties_for_list(objects, list_prop):
    """
    Retrieve specified properties for a list of objects.
    """
    results = []
    for obj in objects:
        result = get_properties_for_object(obj, list_prop)
        results.append(result)

    return results


def create_pivot_with_total(df, category):
    """
    Creates a pivot table for the given category, grouping by 'level' and summarizing 'area'.
    Adds a total row at the bottom.
    
    Parameters:
        df (pd.DataFrame): The original DataFrame.
        category (str): The category to filter ("Rooms" or "Areas").
    
    Returns:
        pd.DataFrame: The pivoted DataFrame with totals.
    """
    # Filter based on category
    df_filtered = df[df["category"] == category].reset_index(drop=True)

    # Create the pivot table
    df_pivot = df_filtered.pivot_table(index="level", columns="name", values="area", aggfunc="sum").reset_index()
    
    # Fill NaN values with 0
    df_pivot = df_pivot.fillna(0)

    # Add a new row with the sum of all numeric columns
    df_pivot.loc["Total"] = df_pivot.select_dtypes(include="number").sum()
    df_pivot.loc["Total", "level"] = "Total"  # Set label for the sum row

    return df_pivot

def create_pivot_tables(filter_categories, df):
    table_list = []
    if len(filter_categories) == 2:

        # Explicitly filter based on "Areas" and "Rooms"
        df_rooms = create_pivot_with_total(df, "Rooms")
        table_list.append(df_rooms)

        df_areas = create_pivot_with_total(df, "Areas")
        table_list.append(df_areas)

        return table_list
    else:

        df_pivot_table = create_pivot_with_total(df, filter_categories[0])
        table_list.append(df_pivot_table)
        
        return table_list