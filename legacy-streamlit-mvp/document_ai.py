import PyPDF2
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SKLearnVectorStore # স্ট্যাবল ডাটাবেস
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from groq import Groq
from google import genai

# API Keys Setup
GEMINI_API_KEY = "AIzaSyADIn2MpxC7SiP8rTDVjs9BJl5ZT8hykAA"
GROQ_API_KEY = "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"

# (No PyTorch, No Google API required. Runs native & fast on Mac)
embeddings = FastEmbedEmbeddings()

def extract_text_from_file(uploaded_file):
    text = ""
    if uploaded_file.name.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        text = df.to_string() 
    return text

def build_vector_database(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(text)
    
    # Building DB using SKLearn (as per your setup)
    vector_store = SKLearnVectorStore.from_texts(chunks, embeddings)
    return vector_store

def analyze_report_with_ai(query, vector_store, model_choice="groq"):
    docs = vector_store.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])
    
    prompt = f"""
    You are an Expert Corporate Data Analyst.
    Use ONLY the following context to answer the user's question. 
    If the answer is not present in the context, clearly state: "Information not found in the uploaded report."
    
    Context from Document:
    {context}
    
    User Question: {query}
    """
    
    try:
        if model_choice == "groq":
            client = Groq(api_key=GROQ_API_KEY)
            res = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.2,
            )
            return res.choices[0].message.content
        else:
            client = genai.Client(api_key=GEMINI_API_KEY)
            res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return res.text
    except Exception as e:
        return f"AI Generation Error: {e}"