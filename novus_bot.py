import streamlit as st
from PIL import Image, ImageEnhance
import time
import json
import base64

def generate_query_prompt(database, schema, table, columns, user_request):
    return f"""
            Generate an SQL query for the Snowflake database using the following details and rules:
            - Database: {database}
            - Schema: {schema}
            - Table: {table}
            - Columns: {columns} 
            - User Request: {user_request}
            - Additional Context:
            Rules:
            1. Always use explicit JOINs instead of implicit syntax.
            2. Use parameterized queries to prevent SQL injection.
            3. Ensure all SELECT queries have a LIMIT unless otherwise specified by the user.
            4. Avoid using functions that lock the database.
            5. Do not allow any DDL commands like CREATE, DROP, ALTER in the queries.
            6. Enforce the use of specific schemas and tables to restrict access.
            7. Ensure that transactional commands like INSERT, UPDATE, DELETE are not used.
            8. Syntax should be specifically for Snowflake SQL.
            9. The WHERE clause should ALWAYS originate from the SALES_DATA schema.
            10. Only respond with the query, no other context. The response will be executed verbatim.
            11. Do not include a semicolon at the end of the statement.
            12. If using an aggregate function, always add a GROUP BY clause for all relevant columns.
            13. Force the date format as YYYY-MM-DD when working with date fields.
            """
def create_context(user_input):
    TABLE = "REGRESSION_SANDBOX"
    SCHEMA = "NORTHWINDS"
    DATABASE = "PANDATA_DEMO"
    COLUMNS = session.sql("SELECT COLUMN_NAME, DATA_TYPE FROM PANDATA_DEMO.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'NORTHWINDS' AND TABLE_NAME = 'REGRESSION_SANDBOX'").collect()
    COLUMNS_FORMATTED = ", ".join([f"{col['COLUMN_NAME']} ({col['DATA_TYPE']})" for col in COLUMNS])
    st.write(COLUMNS_FORMATTED)
    CONTEXT = generate_query_prompt(DATABASE, SCHEMA, TABLE, COLUMNS_FORMATTED, user_input)
    return CONTEXT

def summarize_data(data):
    data = json.dumps(data.to_dict(orient="records"))
    summary_prompt = f"Provide a concise summary of the following sales data points. Just pick a few interesting insights (like one product doing better than another, etc). This will be written out to streamlit. Make sure the formatting is written like a human. Break things into lines, etc.\n{data}"
    try:
        response = list(session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', '"+query+"')").to_pandas().to_dict(orient='records')[0].values())[0]

        
        return response
    except Exception as e:
        st.error("Failed to generate summary: " + str(e))
        return None

def generate_query(user_input):
    query_string = str(create_context(user_input))
    st.write(query_string)
    query = list(session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', '"+query+"')").to_pandas().to_dict(orient='records')[0].values())[0]       
    if query:
        query = re.sub(r"[;]", '', query)
    else:
        st.warning("No data found for your query.")
    return query

def execute_query(session, query):
    try:
        # Executing the query and fetching results as a DataFrame
        data = session.sql(query).to_pandas()
        return data
    except Exception as e:
        # Log the error and display a friendly message
        st.error(f"Failed to execute query: {str(e)}")
        return pd.DataFrame()  # Return an empty DataFrame

def img_to_base64(image_path):
    """Convert image to base64"""
    with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()


def main():
    """
    Display Streamlit updates and handle the chat interface.
    """
    
    # Inject custom CSS for glowing border effect
    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #330000,
                0 0 10px #660000,
                0 0 15px #990000,
                0 0 20px #CC0000,
                0 0 25px #FF0000,
                0 0 30px #FF3333,
                0 0 35px #FF6666;
            position: relative;
            z-index: -1;
            border-radius: 30px;  /* Rounded corners */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Load and display sidebar image with glowing effect
    img_path = "imgs/novus logo.jpg"
    img_base64 = img_to_base64(img_path)
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    
    app_name="NovAi"
    app_mode="Chat with "+ app_name
    input_display="Ask me about the Loan Account Details"
    
    
    # Sidebar for Mode Selection
    mode = st.sidebar.radio("Select Mode:", options=["Summary Stats",app_mode], index=1)
    st.sidebar.markdown("---")
    
    
    # Handle Chat
    if mode == app_mode:
        chat_input = st.chat_input(input_display)
        
        if chat_input:
            st.write('Here is the query I have attempted to generate!')
            query = generate_query(chat_input)
            st.caption(query)
            data = execute_query(session, query)
            if not data.empty:
                st.write(data)
                st.bar_chart(data)
                st.divider()
    
                # Generate and display summary
                summary = engine.summarize_data(data)
                if summary:
                    st.subheader("Summary of the Data")
                    st.write(summary)
                csv = data.to_csv()
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name='query_results.csv',
                    mime='text/csv')
        
if __name__ == "__main__":
    main()