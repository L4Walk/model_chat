from openai import AzureOpenAI
import logging
import time
from models.model_config import ModelConfig

# Initialize logger
logger = logging.getLogger(__name__)

def get_azure_client(model_config):
    """Initialize Azure OpenAI client with model configuration"""
    if not model_config or model_config.model_type != 'azure':
        raise ValueError('无效的Azure模型配置')
    
    return AzureOpenAI(
        api_key=model_config.get_api_key(),
        api_version='2024-02-15-preview',
        base_url=f"{model_config.api_base}/openai/deployments/{model_config.model_name}"
    )

def get_chat_response(model_config, messages):
    """Get response from Azure OpenAI API for chat completion.
    
    Args:
        model_config (ModelConfig): 模型配置信息
        messages (list): 对话消息列表
        
    Returns:
        generator: 生成器对象，用于流式输出回复内容
        
    Raises:
        Exception: 当API调用失败时抛出异常
    """
    try:
        client = get_azure_client(model_config)
        
        # 创建聊天完成请求
        completion = client.chat.completions.create(
            model=model_config.model_name,
            messages=messages,
            stream=True,  # 启用流式输出
            **model_config.get_parameters()  # 使用配置中的其他参数
        )
        
        # 流式输出回复内容
        for chunk in completion:
            if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"获取回复失败: {str(e)}")
        raise e

def init_default_model():
    """Initialize default Azure OpenAI model configuration"""
    try:
        # 检查是否已存在默认配置
        if not ModelConfig.query.filter_by(name='Azure GPT-4').first():
            default_config = ModelConfig(
                name='Azure GPT-4',
                model_type='azure',
                api_key='e04b6f423e7647bfb83a3b3e51ed1f22',
                model_name='gpt-4o-2',
                api_base='https://infmonkeys.openai.azure.com',
                parameters={
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            )
            default_config.status = 'active'
            from models.database import db
            db.session.add(default_config)
            db.session.commit()
            logger.info('默认Azure模型配置初始化成功')
    except Exception as e:
        logger.error(f'初始化默认模型配置失败: {str(e)}')
        raise e