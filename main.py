import openai
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, inspect, text

openai.api_key = '' #write your openai api key

def connect_to_db(db_user, db_password, db_host, db_port, db_name):
    try:
        engine = create_engine(f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
        inspector = inspect(engine)
        return engine, inspector
    except Exception as e:
        st.error(f'Could not connect to the database. Error: {e}')
        st.stop()

def get_db_structure(inspector):
    table_names = inspector.get_table_names()
    db_structure = {}
    for table_name in table_names:
        columns = inspector.get_columns(table_name)
        db_structure[table_name] = {column['name']: column['type'] for column in columns}
    return db_structure

def generate_sql(user_request, db_structure):
    intro = 'You are a helpful assistant. You will complete a task and write the results.'
    prompt = f'Given the database schema, write a SQL query that returns the following information: {user_request}.'
    prompt += f'You only need to write SQL code, do not comment or explain code and do not add any additional info. I need code only. Always use table name in column reference to avoid ambiguity. SQL dialect is postgresql. Only use columns and tables mentioned in the doc below. \n{db_structure}'

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": intro},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def run_sql(code, engine):
    df = pd.read_sql_query(sql=text(code), con=engine.connect())
    return df

def get_user_input():
    with st.sidebar:
        db_host = st.text_input('host', 'localhost')
        db_port = st.text_input('port', '5432')
        db_user = st.text_input('user', 'postgres')
        db_password = st.text_input('password', '111', type='password')
        db_name = st.text_input('database', 'northwind')

        with st.form(key='my_form_to_submit'):
          user_request = st.text_area("Let chatGPT to do SQL for you")
          submit_button = st.form_submit_button(label='Submit')

        if not submit_button or not user_request or not db_host or not db_user or not db_password or not db_name or not db_port:
            st.stop()

        return db_host, db_port, db_user, db_password, db_name, user_request

def main():
    db_host, db_port, db_user, db_password, db_name, user_request = get_user_input()
    engine, inspector = connect_to_db(db_user, db_password, db_host, db_port, db_name)
    db_structure = get_db_structure(inspector)
    code = generate_sql(user_request, db_structure)
    pretty_code = '```sql\n' + code + '\n```'
    code = code.replace('\n', ' ')

    with st.expander("See executed code"):
        st.write(pretty_code)
    with st.expander("See introspected BD structure"):
        st.write(db_structure)

    df = run_sql(code, engine)

    st.write("## The results")
    st.write(df)

if __name__ == "__main__":
    main()
