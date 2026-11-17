from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline


def build_qa_chain(vector_db):

    model_name = "google/flan-t5-base"

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        temperature=0.0,
        do_sample=False,
    )

    llm = HuggingFacePipeline(
        pipeline=pipe
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    qa = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_db.as_retriever(
            search_kwargs={
                "k": 5
            }
        ),
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={
            "prompt": None
        },
    )

    return qa