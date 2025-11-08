# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import pandas as pd
import requests

# Write directly to the app
st.title("🥤 Customize Your Smoothie! 🥤")
st.write(
    """Choose the fruits you want in your custom Smoothie!
    """
)

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

cnx = st.connection("snowflake")
session = cnx.session()

# Pull FRUIT_NAME and SEARCH_ON from Snowflake
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert to pandas for easy lookup
pd_df = my_dataframe.to_pandas()

# Show dataframe temporarily (optional debugging)
# st.dataframe(pd_df)
# st.stop()

# Multiselect uses FRUIT_NAME visible to user
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'],
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # Lookup the SEARCH_ON value for API
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]

        st.write('The search value for', fruit_chosen, 'is', search_on, '.')

        st.subheader(f"{fruit_chosen} Nutrition Information")

        smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)

    # Insert order into Snowflake
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string.strip()}', '{name_on_order}')
    """

    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered, {name_on_order}!", icon='✅')
