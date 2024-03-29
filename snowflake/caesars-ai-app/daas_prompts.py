import streamlit as st

SCHEMA_PATH = st.secrets.get("SCHEMA_PATH", "DAAS_DEV.DAAS_CORE")
QUALIFIED_TABLE_NAME_GAME_DAY_SUMMARY_FACT = f"{SCHEMA_PATH}.GAME_DAY_SUMMARY_FACT"
TABLE_DESCRIPTION_GAME_DAY_SUMMARY_FACT = """
This table has various metrics for slot machines with game dates of Decemeber 2023. This data is used to calculate
how much machine has earned for the Casino properties, such as Coin In Amount tells you how much amount was inserted in the machine
and handle pulls tells you how many handle was pulled for each machine in specific Casino property using property code
that signifies an Casino Property and machine nbr fields talks about the machine details.

"""

tables = ['GAME_DAY_SUMMARY_FACT']

QUALIFIED_TABLE_NAME_MACHINE_DIM = f"{SCHEMA_PATH}.MACHINE_DIM"
TABLE_DESCRIPTION_MACHINE_DIM = """
This table has various details of machines such as machine number, machine status, machine type and property code. Join this table
with game day summary fact table to get the metrics related to machines.
"""

METADATA_QUERY = f"SELECT VARIABLE_NAME, DEFINITION FROM {SCHEMA_PATH}.MACHINE_FINANCIAL_ENTITY_ATTRIBUTES;"

GEN_SQL = """
You will be acting as an AI Snowflake SQL Expert named Casino.AI.
Your goal is to give correct, executable sql query to users.
You will be replying to users who will be confused if you don't respond in the character of Casino.AI.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.
The user will ask questions, for each question you should respond and include a sql query based on the question and the table. 

{context}

Here are 6 critical rules for the interachtion you must abide:
<rules>
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
3. Text / string where clauses must be fuzzy match e.g ilike %keyword%
4. Make sure to generate a single snowflake sql code, not multiple. 
5. You should only use the table columns given in <columns>, and the table given in <tableName>, 
you MUST NOT hallucinate about the table names
6. DO NOT put numerical at the very front of sql variable.
7. you MUST NOT put <tableName> and use the actual table given in <tableName> in the SQL query.
8. For details regarding machine status and game type, alwasys refer to table daas_dev.daas_core.machine_dim.
</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

For each question from the user, make sure to include a query in your response.

Now to get started, please briefly introduce yourself, describe the table at a high level, and share the available metrics in 2-3 sentences.
Then provide 3 example questions using bullet points.
"""

@st.cache_data(show_spinner="Loading Casino.AI's context...")
def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    print(f'Running context for {table_name}')
    table = table_name.split(".")
    conn = st.connection("snowflake")
    columns = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
        """, show_spinner=False,
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ]
    )

    context = f"""
Here is the table name <tableName> {'.'.join(table)} </tableName>

<tableDescription>{TABLE_DESCRIPTION_GAME_DAY_SUMMARY_FACT}</tableDescription>
<tableDescription>{TABLE_DESCRIPTION_MACHINE_DIM}</tableDescription>

Here are the columns of the {'.'.join(table)}

<columns>\n\n{columns}\n\n</columns>
    """
    if metadata_query:
        metadata = conn.query(metadata_query, show_spinner=False)
        metadata = "\n".join(
            [
                f"- **{metadata['VARIABLE_NAME'][i]}**: {metadata['DEFINITION'][i]}"
                for i in range(len(metadata["VARIABLE_NAME"]))
            ]
        )
        context = context + f"\n\nAvailable variables by VARIABLE_NAME:\n\n{metadata}"
    return context

def get_system_prompt():
    table_contexts = ''
    for tab in tables:
        table_name = f'DAAS_DEV.DAAS_CORE.{tab}'
        table_description=f'TABLE_DESCRIPTION_{tab}'
        print(f'Getting context for {table_name}')
        table_context = get_table_context(
            table_name=table_name,
            table_description=table_description,
            metadata_query=METADATA_QUERY
    
        )
        table_contexts += table_context
    return GEN_SQL.format(context=table_context)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for Casino.AI")
    st.markdown(get_system_prompt())
