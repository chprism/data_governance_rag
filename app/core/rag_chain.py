"""
RAG chain implementation using langchain and langgraph.
"""
from typing import Dict, List, Any
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import Document
from langgraph.graph import END, StateGraph
from app.core.vector_store import get_vector_store
from app.config.settings import OPENAI_API_KEY


class RAGChain:
    """RAG chain implementation for data governance knowledge base."""
    
    def __init__(self):
        """Initialize the RAG chain."""
        self.vector_store = get_vector_store()
        self.llm = ChatOpenAI(api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo")
        
        self.prompt_template = ChatPromptTemplate.from_template("""
        You are a data governance assistant. Use the following retrieved documents to answer the user's question.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:
        """)
    
    def _retrieve(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant documents from the vector store."""
        query = state["query"]
        try:
            results = self.vector_store.similarity_search(query)
            
            if results:
                context = "\n\n".join([
                    f"Document: {result['filename']}\n{result['content']}"
                    for result in results
                ])
                
                state["context"] = context
                state["retrieved_documents"] = results
            else:
                print("No relevant documents found for the query")
                state["context"] = "No relevant documents found."
                state["retrieved_documents"] = []
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            print("Using empty results for testing purposes")
            state["context"] = "No documents could be retrieved due to an error."
            state["retrieved_documents"] = []
            
        return state
    
    def _generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response using the LLM."""
        prompt = self.prompt_template.format(
            context=state["context"],
            question=state["query"]
        )
        
        try:
            response = self.llm.invoke(prompt)
            state["response"] = response.content
        except Exception as e:
            print(f"Error generating response with LLM: {e}")
            print("Using fallback response generation")
            if state["retrieved_documents"]:
                doc = state["retrieved_documents"][0]
                state["response"] = f"Based on the retrieved document '{doc['filename']}', here is some information: {doc['content'][:500]}..."
            else:
                state["response"] = "I don't have enough information to answer that question. Please try uploading more documents or rephrasing your query."
        
        return state
    
    def build_graph(self) -> StateGraph:
        """Build the RAG graph using langgraph."""
        from typing import TypedDict, List, Dict, Any
        
        class GraphState(TypedDict):
            query: str
            context: str
            retrieved_documents: List[Dict[str, Any]]
            response: str
        
        graph = StateGraph(state_schema=GraphState)
        
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("generate", self._generate)
        
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", END)
        
        graph.set_entry_point("retrieve")
        
        return graph
    
    def query(self, query: str) -> Dict[str, Any]:
        """
        Query the RAG chain.
        
        Args:
            query: User query
            
        Returns:
            Response from the RAG chain
        """
        try:
            graph = self.build_graph()
            chain = graph.compile()
            
            result = chain.invoke({"query": query})
            return result
        except Exception as e:
            print(f"Error in RAG chain query: {e}")
            print("Using fallback response")
            
            return {
                "query": query,
                "response": "I'm sorry, I couldn't process your query due to a technical issue. Please try again later or try uploading more documents.",
                "retrieved_documents": []
            }
