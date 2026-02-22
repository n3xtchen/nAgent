REACT_PROMPT_TEMPLATE = """你是一个智能助手。你可以通过一系列的思考 (Thought)、行动 (Action) 和观察 (Observation) 来回答问题。

工具列表:
{tools_description}

格式要求:
Question: 需要回答的问题
Thought: 你应该思考目前该做什么
Action: 采取的行动，必须是工具列表中的一个。格式为: tool_name(args)
Observation: 行动的结果
... (这个 Thought/Action/Observation 过程可以重复多次)
Thought: 我现在知道最终答案了
Final Answer: 对原始问题的最终回答

开始!

Question: {user_input}
"""

def format_tools_description(tools):
    return "\n".join([f"- {tool.name}: {tool.description}" for tool in tools])
