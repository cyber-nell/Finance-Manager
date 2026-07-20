import sqlite3
import pandas as pd
from google import genai
import streamlit as st


DB = "manager.db"


#insert new row
def insertion(date: str, description: str, category: str, amount: float, type: str):
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()

            category = category.capitalize()
            sql = "INSERT INTO transactions (date,description,category,amount,type) VALUES (?,?,?,?,?)"
           # val = val.split(",")
            #val[3] = float(val[3].strip())
            cursor.execute(sql,(date,description,category,amount,type))
            conn.commit()

#Fetching data
def fetching(wanted_category: str):
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()

            wanted_category = wanted_category.capitalize()

            budget_category_sql = "SELECT allocated_amount FROM budgets WHERE category = ?"

            sql = "SELECT amount FROM transactions WHERE category = ?"

            if(wanted_category.lower() == "all"):
                 df = pd.read_sql_query("SELECT amount FROM transactions", conn)
            else:
                df = pd.read_sql_query("SELECT amount FROM transactions WHERE category = ?", conn, params=(wanted_category,))
            
            if df.empty:
                total = 0.0
            else:
                total = df['amount'].sum()


            #comparing budgeted amount
           # if wanted_category.lower() != "all":
            #    cursor.execute(budget_category_sql,(wanted_category,))
             #   budget_val_list = cursor.fetchall()
            #
             #   if budget_val_list:
              #      allocated_budget = budget_val_list[0][0]
               #     print("Budgeted limit for: £", allocated_budget)
                    
                #    if total > allocated_budget:
                 #       print(" Warning: You have exceeded your budget by £{total - allocated_budget:.2f}!")
                  #  else:
                   #     print("You have £",(allocated_budget - total),"remaining.")

            return total


#AI function calling
client = genai.Client() #Add your own AI API

#schema for insertion function
insertion_declaration = {
    "type": "function",
    "name": "insertion",
    "description": "Inserts a new financial transaction into the database when the user inputs tracking or spending data.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "The date of the transaction (YYYY-MM-DD)"},
            "description": {"type": "string", "description": "What the transaction was for"},
            "category": {"type": "string", "description": "The category (e.g., Food, Rent, Groceries)"},
            "amount": {"type": "number", "description": "The cash amount of the transaction"},
            "type": {"type": "string", "description": "Whether it is an 'income' or 'expense'"}
        },
        "required": ["date", "description", "category", "amount", "type"]
    }
}

# schema for fetching function
fetching_declaration = {
    "type": "function",
    "name": "fetching",
    "description": "Fetches historical total spending or records for a specific budget category.",
    "parameters": {
        "type": "object",
        "properties": {
            "wanted_category": {"type": "string", "description": "The category to pull records for, or 'all' to fetch everything."}
        },
        "required": ["wanted_category"]
    }
}


#App
st.title("Finance Manager")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


#User input
if prompt := st.chat_input("What would you like to do today?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    #Pass the declarations into client
    interaction = client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt,
        tools=[insertion_declaration, fetching_declaration],
    )

    #Choose correct tool
    fc_step = next((s for s in interaction.steps if s.type == "function_call"), None)

    response = ""

    if fc_step.name == "fetching":
        category = fc_step.arguments.get("wanted_category")
        total = fetching(category)
        response_text = f"Executing database search for category: **{category}**\n\n"
        response_text += f"You have spent: **£{total:.2f}**"


    elif fc_step.name == "insertion":
        date = fc_step.arguments.get("date", "2026-07-13") # Fallback to today's date if missing
        description = fc_step.arguments.get("description")
        category = fc_step.arguments.get("category")
        amount = float(fc_step.arguments.get("amount", 0.0))
        tx_type = fc_step.arguments.get("type", "expense") # Default to expense

        insertion(date, description, category, amount, tx_type)
        response_text = f" Added **{description}** (£{amount:.2f}) to your **{category}** transaction history on {date}."
    else:
        response_text = interaction.text

    with st.chat_message("assistant"):
            st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})

#insertion()
#fetching()

