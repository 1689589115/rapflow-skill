"""
LLM Function Call 接入示例
演示如何与大模型工具调用功能集成
注意：此示例包含注释版模板，不需要真实API密钥
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill import RapFlowSkill


def get_available_tools():
    """
    获取可用工具列表（OpenAI格式）
    这个函数应该返回给LLM的工具定义
    """
    skill = RapFlowSkill()
    return [skill.get_function_schema()]


def call_skill_function(function_name: str, arguments: dict) -> dict:
    """
    调用Skill函数
    这个函数应该被LLM的工具调用机制触发
    """
    skill = RapFlowSkill()
    
    if function_name == skill.name:
        return skill.run(arguments)
    else:
        return {
            "success": False,
            "error": f"未知函数: {function_name}"
        }


def simulate_openai_function_call():
    """
    模拟OpenAI Function Call流程（伪代码示例）
    """
    
    # 示例歌词
    lyrics = """
    我唱歌的flow 非常优秀
    这个beat让我忍不住抖
    """
    
    # ============================================
    # 伪代码示例：如何与大模型集成
    # ============================================
    
    # 1. 准备消息（假设使用OpenAI API）
    messages = [
        {"role": "user", "content": f"请分析这段歌词的押韵：{lyrics}"}
    ]
    
    # 2. 获取可用工具
    tools = get_available_tools()
    
    # 3. 发送请求（伪代码）
    # response = openai.ChatCompletion.create(
    #     model="gpt-4",
    #     messages=messages,
    #     tools=tools,
    #     tool_choice="auto"
    # )
    
    # 4. 检查是否需要调用工具
    # if response.choices[0].message.get('tool_calls'):
    #     for tool_call in response.choices[0].message.tool_calls:
    #         function_name = tool_call.function.name
    #         arguments = json.loads(tool_call.function.arguments)
    #         
    #         # 调用Skill
    #         result = call_skill_function(function_name, arguments)
    #         
    #         # 添加工具响应到消息
    #         messages.append({
    #             "role": "tool",
    #             "tool_call_id": tool_call.id,
    #             "content": json.dumps(result, ensure_ascii=False)
    #         })
    #         
    #     # 发送最终请求获取回答
    #     final_response = openai.ChatCompletion.create(
    #         model="gpt-4",
    #         messages=messages
    #     )
    #     return final_response.choices[0].message.content
    
    # 5. 直接调用示例（无需LLM）
    skill = RapFlowSkill()
    result = skill.run({
        "text": lyrics,
        "mode": "auto",
        "mark_breath": True,
        "max_rhyme_level": 4
    })
    
    return result


def simulate_deepseek_function_call():
    """
    模拟DeepSeek Function Call流程（伪代码示例）
    """
    
    # 示例歌词
    lyrics = """
    我唱歌的flow 非常优秀
    这个beat让我忍不住抖
    """
    
    # ============================================
    # 伪代码示例：DeepSeek API集成
    # ============================================
    
    # 1. 准备消息
    messages = [
        {"role": "user", "content": f"分析这段歌词：{lyrics}"}
    ]
    
    # 2. 定义工具（DeepSeek格式与OpenAI兼容）
    tools = [
        {
            "type": "function",
            "function": {
                "name": "rapflow_skill",
                "description": "中文说唱文本分析工具",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "说唱歌词文本"},
                        "mode": {"type": "string", "description": "分析模式"},
                        "mark_breath": {"type": "boolean", "description": "是否添加换气标记"},
                        "max_rhyme_level": {"type": "integer", "description": "最大押韵等级"}
                    },
                    "required": ["text"]
                }
            }
        }
    ]
    
    # 3. 发送请求（伪代码）
    # response = openai.ChatCompletion.create(
    #     model="deepseek-chat",
    #     messages=messages,
    #     tools=tools
    # )
    
    # 4. 处理响应...
    
    # 5. 直接调用示例
    skill = RapFlowSkill()
    result = skill.run({
        "text": lyrics,
        "mode": "auto",
        "mark_breath": True,
        "max_rhyme_level": 4
    })
    
    return result


def main():
    """主函数"""
    print("=" * 60)
    print("RapFlow-Skill - LLM Function Call 接入示例")
    print("=" * 60)
    
    # 显示可用工具
    print("\n1. 可用工具定义:")
    print("-" * 60)
    tools = get_available_tools()
    for tool in tools:
        print(f"\n工具名称: {tool['name']}")
        print(f"描述: {tool['description']}")
        print(f"参数schema:\n{json.dumps(tool['parameters'], ensure_ascii=False, indent=2)}")
    
    # 模拟OpenAI调用
    print("\n" + "=" * 60)
    print("2. 模拟OpenAI Function Call:")
    print("-" * 60)
    result = simulate_openai_function_call()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 模拟DeepSeek调用
    print("\n" + "=" * 60)
    print("3. 模拟DeepSeek Function Call:")
    print("-" * 60)
    result = simulate_deepseek_function_call()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 打印接入说明
    print("\n" + "=" * 60)
    print("接入说明:")
    print("-" * 60)
    print("""
    1. 将 get_available_tools() 返回的工具列表传递给LLM
    2. 当LLM决定调用工具时，会调用 call_skill_function()
    3. call_skill_function() 根据函数名分发到对应的Skill方法
    4. Skill返回的JSON结果会作为工具响应返回给LLM
    5. LLM根据结果生成最终回答
    
    兼容性：
    - OpenAI Chat Completion API（tools参数）
    - DeepSeek API（完全兼容OpenAI格式）
    - 其他支持OpenAI格式的LLM服务
    """)


if __name__ == "__main__":
    main()
    