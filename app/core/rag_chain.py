"""
基于langchain和langgraph的RAG链实现。
"""
from typing import Dict, List, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langgraph.graph import END, StateGraph
from app.core.vector_store import get_vector_store
from app.core.deepseek_llm import DeepSeekLLM


class RAGChain:
    """RAG chain implementation for data governance knowledge base."""
    
    def __init__(self):
        """初始化RAG链。"""
        self.vector_store = get_vector_store()
        self.llm = DeepSeekLLM(temperature=0.7, max_tokens=1024)
        
        self.prompt_template = ChatPromptTemplate.from_template("""
        你是一个OceanBase数据库助手。使用以下检索到的文档来回答用户的问题。
        回答要精确、简洁。如果你不知道答案，只需说你不知道，不要尝试编造答案。
        
        重要提示：
        1. 在回答中尽可能包含例子，帮助用户更好地理解概念和操作
        2. 如果检索到的文档中包含例子，请直接使用这些例子
        3. 如果文档中没有例子，请根据检索到的内容生成相关的例子
        4. 例子应该简单明了，与用户问题直接相关
        
        检索到的OceanBase文档内容:
        {context}
        
        问题: {question}
        
        回答:
        """)
    
    def _retrieve(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """从向量存储中检索相关文档。"""
        query = state["query"]
        try:
            results = self.vector_store.similarity_search(query)
            
            if results:
                context = "\n\n".join([
                    f"文档: {result['filename']}\n{result['content']}"
                    for result in results
                ])
                
                state["context"] = context
                state["retrieved_documents"] = results
            else:
                print("未找到与查询相关的文档")
                state["context"] = "未找到相关文档。"
                state["retrieved_documents"] = []
        except Exception as e:
            print(f"检索文档时出错: {e}")
            print("使用空结果进行测试")
            state["context"] = "由于发生错误，无法检索文档。"
            state["retrieved_documents"] = []
            
        return state
    
    def _generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM生成回答。"""
        prompt = self.prompt_template.format(
            context=state["context"],
            question=state["query"]
        )
        
        try:
            response = self.llm.invoke(prompt)
            state["response"] = response
        except Exception as e:
            print(f"使用LLM生成回答时出错: {e}")
            print("使用备用回答生成")
            if state["retrieved_documents"]:
                doc = state["retrieved_documents"][0]
                state["response"] = f"根据检索到的文档 '{doc['filename']}'，以下是一些信息: {doc['content'][:500]}..."
            else:
                state["response"] = "我没有足够的信息来回答这个问题。请尝试上传更多文档或重新表述您的问题。"
        
        return state
    
    def build_graph(self) -> StateGraph:
        """使用langgraph构建RAG图。"""
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
        查询RAG链。
        
        参数:
            query: 用户查询
            
        返回:
            来自RAG链的响应
        """
        try:
            graph = self.build_graph()
            chain = graph.compile()
            
            result = chain.invoke({"query": query})
            return result
        except Exception as e:
            print(f"RAG链查询出错: {e}")
            print("使用备用响应")
            
            return {
                "query": query,
                "response": "很抱歉，由于技术问题，我无法处理您的查询。请稍后再试或尝试上传更多文档。",
                "retrieved_documents": []
            }
