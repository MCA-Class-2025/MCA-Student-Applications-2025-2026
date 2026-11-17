import json
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatMessageResponse, RAGQueryRequest
from app.services.rag_service import RAGEngine
from app.services.ollama_service import OllamaService
from app.utils.deps import get_current_user
from app.utils.exceptions import PrepGeniusException
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["AI Tutor Chat & RAG Engine"])

@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    payload: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = ChatSession(
        title=payload.title or "New Study Session",
        user_id=current_user.id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        message_count=0
    )

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    res = []
    for s in sessions:
        msg_count = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
        res.append(ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            message_count=msg_count
        ))
    return res

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise PrepGeniusException("Chat session not found", status_code=404)

    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return messages

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise PrepGeniusException("Chat session not found", status_code=404)

    db.delete(session)
    db.commit()
    return {"success": True, "message": "Chat session deleted"}

@router.post("/query")
async def rag_query_stream(
    payload: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG Streaming Endpoint:
    1. Fetch user's uploaded documents from SQLite.
    2. Build FAISS vector store & perform semantic search to find top relevant chunks.
    3. Stream answer token-by-token using Ollama Qwen2.5 (with source citations header).
    4. Store user query and assistant response into SQLite ChatMessage history.
    """
    session = db.query(ChatSession).filter(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise PrepGeniusException("Chat session not found", status_code=404)

    # 1. Fetch user documents
    query_builder = db.query(Document).filter(Document.user_id == current_user.id)
    if payload.document_ids:
        query_builder = query_builder.filter(Document.id.in_(payload.document_ids))
    
    user_docs = query_builder.all()

    documents_data = [
        {"doc_id": d.id, "filename": d.filename, "text": d.extracted_text or ""}
        for d in user_docs if d.extracted_text
    ]

    # 2. Build Vector Index & Semantic Search
    index, chunk_metadata, vectorizer = RAGEngine.build_vector_store(documents_data)
    retrieved_chunks = RAGEngine.search_relevant_chunks(payload.query, index, chunk_metadata, vectorizer=vectorizer, top_k=4)

    # 3. Fetch past conversation memory from SQLite
    past_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc()).all()
    conversation_history = [{"role": m.role, "content": m.content} for m in past_msgs]

    # Save User message to SQLite immediately
    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.query)
    db.add(user_msg)
    db.commit()

    # Generator for SSE Streaming
    async def event_generator():
        # First send Citations Header event
        citations_data = [
            {
                "filename": c["filename"],
                "chunk_index": c["chunk_index"],
                "relevance_score": c["relevance_score"],
                "snippet": c["snippet"][:150] + "..."
            } for c in retrieved_chunks
        ]
        yield f"data: {json.dumps({'type': 'citations', 'citations': citations_data})}\n\n"

        full_assistant_response = []
        async for chunk in OllamaService.generate_rag_response_stream(
            query=payload.query,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_history
        ):
            full_assistant_response.append(chunk)
            yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"

        complete_text = "".join(full_assistant_response)

        # Save Assistant message to SQLite
        try:
            db_save = SessionLocal()
            assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=complete_text)
            db_save.add(assistant_msg)
            db_save.commit()
            db_save.close()
        except Exception as e:
            logger.error(f"Failed to save assistant message: {e}")

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
