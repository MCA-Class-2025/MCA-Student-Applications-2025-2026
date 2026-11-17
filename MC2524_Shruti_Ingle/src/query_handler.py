from langchain_community.tools import DuckDuckGoSearchRun

search_tool = DuckDuckGoSearchRun()


def ask_chatbot(qa_chain, question):
    response = qa_chain.invoke({"question": question})
    answer = response["answer"].strip()

    if "[NOT_FOUND]" in answer or answer == "":
        web_result = search_tool.run(question)

        return (
            "**Information not found in uploaded documents.**\n\n"
            "**Web Search Result:**\n"
            f"{web_result}"
        )

    return answer