from langchain_community.vectorstores import FAISS


def recommend_career(
        vectorstore,
        user_input
):


    retriever = vectorstore.as_retriever(

        search_kwargs={
            "k":5
        }

    )


    results = retriever.invoke(
        user_input
    )


    recommendations = []


    for doc in results:

        recommendations.append(
            doc.page_content
        )


    return recommendations