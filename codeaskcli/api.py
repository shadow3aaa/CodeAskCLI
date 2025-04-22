"""
API调用相关功能 - 支持多种AI服务提供商
"""
import os
import abc
import json
import requests
from typing import List, Dict, Any, Optional, Type


class BaseAIClient(abc.ABC):
    """
    AI API客户端的抽象基类
    所有具体的API客户端实现都应该继承这个类
    """
    
    def __init__(
        self, 
        api_key: str,
        model_name: str,
        temperature: float = 0.3,
        max_tokens: int = 4000,
        verbose: bool = False,
        **kwargs
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose
        self.additional_params = kwargs
    
    @abc.abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        向API发送聊天完成请求并返回生成的文本
        
        Args:
            messages: 包含角色和内容的消息列表
        
        Returns:
            生成的文本响应
        """
        pass
    
    def clean_response(self, response: str) -> str:
        """
        清理API响应
        
        Args:
            response: API返回的原始响应文本
            
        Returns:
            清理后的文本
        """
        result = response.replace("<think>", "").replace("</think>", "").strip()
        result = result.replace("```markdown", "").replace("```", "")
        return result
        
    def _print_verbose(self, title: str, content: Any) -> None:
        """
        在verbose模式下打印信息
        
        Args:
            title: 信息标题
            content: 要打印的内容
        """
        if self.verbose:
            print(f"\n{'='*50}")
            print(f"【{title}】")
            print(f"{'='*50}")
            
            if isinstance(content, list) and content and isinstance(content[0], dict) and "content" in content[0]:
                # 处理消息列表的情况，通常是messages
                for msg in content:
                    role = msg.get("role", "unknown")
                    content_text = msg.get("content", "")
                    print(f"\n【{role.upper()}】")
                    print(f"{content_text}\n")
            elif isinstance(content, dict):
                # 处理字典，以美观的方式打印
                import json
                print(json.dumps(content, ensure_ascii=False, indent=2))
            else:
                # 其他情况直接打印
                print(content)
            
            print(f"{'='*50}\n")


class OpenAIClient(BaseAIClient):
    """OpenAI API客户端实现"""
    
    def __init__(
        self, 
        api_key: str,
        model_name: str = "gpt-3.5-turbo",
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ):
        super().__init__(api_key, model_name, temperature, max_tokens, **kwargs)
        self.base_url = base_url
    
    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """调用OpenAI API获取完成结果"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # 添加可能的额外参数
        data.update({k: v for k, v in self.additional_params.items() 
                   if k in ["top_p", "n", "stream", "presence_penalty", "frequency_penalty"]})
        
        # verbose模式下输出请求内容
        self._print_verbose("OpenAI API请求", messages)
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            
            # verbose模式下输出响应内容
            self._print_verbose("OpenAI API响应", result)
            
            return result
        except Exception as e:
            print(f"OpenAI API调用失败: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"API响应: {response.text}")
            raise


class AnthropicClient(BaseAIClient):
    """Anthropic API客户端实现"""
    
    def __init__(
        self, 
        api_key: str,
        model_name: str = "claude-3-opus-20240229",
        base_url: str = "https://api.anthropic.com/v1",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ):
        super().__init__(api_key, model_name, temperature, max_tokens, **kwargs)
        self.base_url = base_url
    
    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """调用Anthropic API获取完成结果"""
        url = f"{self.base_url}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # 将消息格式从OpenAI格式转换为Anthropic格式
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] in ["user", "assistant"]:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        data = {
            "model": self.model_name,
            "messages": anthropic_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # 添加系统消息（如果有）
        if system_message:
            data["system"] = system_message
        
        # 添加可能的额外参数
        data.update({k: v for k, v in self.additional_params.items() 
                   if k in ["top_p", "top_k", "stop_sequences"]})
        
        # verbose模式下输出请求内容
        self._print_verbose("Anthropic API请求", messages)
        self._print_verbose("Anthropic API请求数据", data)
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()["content"][0]["text"]
            
            # verbose模式下输出响应内容
            self._print_verbose("Anthropic API响应", result)
            
            return result
        except Exception as e:
            print(f"Anthropic API调用失败: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"API响应: {response.text}")
            raise


class AzureOpenAIClient(BaseAIClient):
    """Azure OpenAI API客户端实现"""
    
    def __init__(
        self, 
        api_key: str,
        endpoint: str,
        deployment_name: str,
        api_version: str = "2023-05-15",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ):
        # 在Azure中，deployment_name相当于model_name
        super().__init__(api_key, deployment_name, temperature, max_tokens, **kwargs)
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
    
    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """调用Azure OpenAI API获取完成结果"""
        url = f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        data = {
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # 添加可能的额外参数
        data.update({k: v for k, v in self.additional_params.items() 
                   if k in ["top_p", "n", "stream", "presence_penalty", "frequency_penalty"]})
        
        # verbose模式下输出请求内容
        self._print_verbose("Azure OpenAI API请求", messages)
        self._print_verbose("Azure OpenAI API请求URL", url)
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            
            # verbose模式下输出响应内容
            self._print_verbose("Azure OpenAI API响应", result)
            
            return result
        except Exception as e:
            print(f"Azure OpenAI API调用失败: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"API响应: {response.text}")
            raise


class GeminiClient(BaseAIClient):
    """Google Gemini API客户端实现"""
    
    def __init__(
        self, 
        api_key: str,
        model_name: str = "gemini-pro",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        temperature: float = 0.3,
        max_tokens: int = 4000,
        **kwargs
    ):
        super().__init__(api_key, model_name, temperature, max_tokens, **kwargs)
        self.base_url = base_url
    
    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """调用Google Gemini API获取完成结果"""
        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        
        # 将OpenAI格式的消息转换为Gemini格式
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            if msg["role"] != "system":  # Gemini没有系统消息，我们将其附加到第一个用户消息
                gemini_messages.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        # 如果有系统消息，将其附加到第一个用户消息
        system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
        if system_message and gemini_messages and gemini_messages[0]["role"] == "user":
            gemini_messages[0]["parts"][0]["text"] = f"{system_message}\n\n{gemini_messages[0]['parts'][0]['text']}"
        
        data = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }
        
        # 添加可能的额外参数
        generation_config = data["generationConfig"]
        if "top_p" in self.additional_params:
            generation_config["topP"] = self.additional_params["top_p"]
        if "top_k" in self.additional_params:
            generation_config["topK"] = self.additional_params["top_k"]
        
        # verbose模式下输出请求内容
        self._print_verbose("Google Gemini API请求", messages)
        self._print_verbose("Google Gemini API转换后请求", data)
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            
            # verbose模式下输出响应内容
            self._print_verbose("Google Gemini API响应", result)
            
            return result
        except Exception as e:
            print(f"Google Gemini API调用失败: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"API响应: {response.text}")
            raise


class AIClientFactory:
    """
    AI客户端工厂类，负责创建不同的AI API客户端
    """
    _clients = {
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
        "azure": AzureOpenAIClient,
        "gemini": GeminiClient
    }
    
    @classmethod
    def register_client(cls, name: str, client_class: Type[BaseAIClient]) -> None:
        """
        注册新的AI客户端类
        
        Args:
            name: 客户端名称
            client_class: 客户端类，必须是BaseAIClient的子类
        """
        if not issubclass(client_class, BaseAIClient):
            raise TypeError(f"客户端类必须是BaseAIClient的子类")
        cls._clients[name] = client_class
    
    @classmethod
    def get_client(cls, provider: str, **kwargs) -> BaseAIClient:
        """
        获取指定提供商的AI客户端实例
        
        Args:
            provider: AI提供商名称
            **kwargs: 传递给客户端构造函数的参数
            
        Returns:
            AIClient实例
            
        Raises:
            ValueError: 如果提供商不受支持
        """
        provider = provider.lower()
        if provider not in cls._clients:
            supported = ", ".join(cls._clients.keys())
            raise ValueError(
                f"不支持的AI提供商: {provider}。支持的提供商有: {supported}"
            )
        
        return cls._clients[provider](**kwargs)
    
    @classmethod
    def list_supported_providers(cls) -> List[str]:
        """
        列出所有支持的AI提供商
        
        Returns:
            提供商名称列表
        """
        return list(cls._clients.keys())


# 保留旧的AIApiClient类作为兼容层，实际上是OpenAI客户端的包装
class AIApiClient:
    """
    兼容层，保持向后兼容性
    内部使用OpenAIClient
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "gpt-3.5-turbo", 
        temperature: float = 0.3,
        max_tokens: int = 4000
    ):
        self.client = OpenAIClient(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """调用API获取完成结果"""
        return self.client.chat_completion(messages)
    
    def clean_response(self, response: str) -> str:
        """清理API响应"""
        return self.client.clean_response(response)