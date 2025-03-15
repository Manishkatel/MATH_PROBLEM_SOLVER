import streamlit as st
from langchain.chains import LLMMathChain, LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.agents.agent_types import AgentType
from langchain.agents import Tool, initialize_agent
from langchain.callbacks import StreamlitCallbackHandler
from langchain_groq import ChatGroq

# Set up the Streamlit app
st.set_page_config(page_title="Text to Math Problem Solver and Data Search Assistant", page_icon="🔢")
st.title("MATH PROBLEM SOLVER") 

# API Key input
groq_api_key = st.sidebar.text_input(label="Groq API Key", type="password")

if not groq_api_key:  # Check if API key is provided
    st.warning("Please add your Groq API key to continue.")
    st.stop()

# Initialize the LLM
llm = ChatGroq(model="Gemma2-9b-It", groq_api_key=groq_api_key)

# Wikipedia tool
wikipedia_wrapper = WikipediaAPIWrapper()
wikipedia_tool = Tool(
    name="Wikipedia",
    func=wikipedia_wrapper.run,
    description="A tool for searching Wikipedia to find information on various topics."
)

# Math tool
math_chain = LLMMathChain.from_llm(llm=llm)
calculator = Tool(
    name="Calculator",
    func=math_chain.run,
    description="A tool for answering math-related questions. Only mathematical expressions should be provided."
)

# Reasoning tool
prompt = """
You are an agent tasked with solving users' mathematical questions. Logically arrive at the solution and provide a detailed explanation, displaying it point-wise for the question below.

**Question:** {question}

**Answer:**
"""
prompt_template = PromptTemplate(
    input_variables=["question"],
    template=prompt
)

chain = LLMChain(llm=llm, prompt=prompt_template)

reasoning_tool = Tool(
    name="Reasoning Tool",
    func=chain.run,
    description="A tool for answering logical and reasoning questions."
)

# Initialize the agent
assistant_agent = initialize_agent(
    tools=[wikipedia_tool, calculator, reasoning_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True
)

# Store chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi, I'm a Math chatbot who can answer all your math questions!"}
    ]

# Display previous messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Layout: Question input and Clear Chat button in the same row
col1, col2 = st.columns([4, 1])

with col1:
    question = st.text_area("Enter your question:", "I have 5 bananas and 7 grapes. I eat 2 bananas.")

with col2:
    st.write("")  # Adds some spacing for alignment
    if st.button("🗑️ Clear Chat", type="primary"):
        st.session_state["messages"] = [
            {"role": "assistant", "content": "Hi, I'm a Math chatbot who can answer all your math questions!"}
        ]
        st.rerun()  # Refresh the app to clear chat history

# Answer button below the question input
if st.button("Find my answer"):
    if question:
        with st.spinner("Generating response..."):
            st.session_state.messages.append({"role": "user", "content": question})
            st.chat_message("user").write(question)

            # Use callback handler
            st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
            response = assistant_agent.run({'input': question}, callbacks=[st_cb])

            st.session_state.messages.append({'role': 'assistant', "content": response})
            st.write('### Response:')
            st.success(response)
    else:
        st.warning("Please enter a question.") 


