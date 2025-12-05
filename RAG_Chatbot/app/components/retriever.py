from langchain_classic.chains import ConversationalRetrievalChain 
from langchain_core.prompts import PromptTemplate

from app.components.llm import load_llm
from app.components.vector_store import load_vector_store

from app.config.config import HUGGINGFACE_REPO_ID,HF_TOKEN
from app.common.logger import get_logger
from app.common.custom_exception import CustomException


logger = get_logger(__name__)

CUSTOM_PROMPT_TEMPLATE = """ 
You are a highly specialized medical assistant. Your final answer MUST only use the information provided in the context below.
Answer the question in 2-3 lines maximum. If the context does not contain the answer, state that you cannot find the information.

Context:
{context}

Question:
{question}

Answer:
"""

def set_custom_prompt():
    return PromptTemplate(template=CUSTOM_PROMPT_TEMPLATE, input_variables=["context" , "question"])

def create_qa_chain():
    try:
        logger.info("Loading vector store for context")
        db = load_vector_store()

        if db is None:
            raise CustomException("Vector store not present or empty")

        llm = load_llm(huggingface_repo_id=HUGGINGFACE_REPO_ID , hf_token=HF_TOKEN )

        if llm is None:
            raise CustomException("LLM not loaded")

        condense_question_llm = llm 

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=db.as_retriever(search_kwargs={'k': 3}), 
            condense_question_llm=condense_question_llm, 
            combine_docs_chain_kwargs={"prompt": set_custom_prompt()}, 
            chain_type="stuff",
            return_source_documents=False,
        )

        logger.info("Successfully created the QA chain")
        return qa_chain
    
    except Exception as e:
        error_message = CustomException("Failed to make a QA chain", e)
        logger.error(str(error_message))
        raise error_message