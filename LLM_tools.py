import requests
import json
import os
from openai import OpenAI
import base64

MAINMODEL="internlm/internlm2_5-7b-chat"
CHUNKMODEL="Qwen/Qwen2.5-7B-Instruct"
URL="https://api.siliconflow.cn/v1/chat/completions"



#qwen多模态
#  base 64 编码格式
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")




def HttpMLM(Image_path_list,text):
    
    encoded_images = []
    print("开始将图片编码...")
    for image_path in Image_path_list:
        full_path = os.path.join("Output", image_path)
        base64_image = encode_image(full_path)
        encoded_images.append(base64_image)   
    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
        # api_key=os.getenv('DASHSCOPE_API_KEY'),
        api_key="sk-03ae1e6cb82d4b22baa2b3fad5eec971",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    print("开始向MLM发起请求...")
    completion = client.chat.completions.create(
        model="qwen-vl-max-latest",
        messages=[
            {
                "role": "system",
                "content": [{"type":"text","text": "You are an expert at extracting and summarizing from images and text."}]},
            {
                "role": "user",
                "content": [
                    # 需要注意，传入Base64，图像格式（即image/{format}）需要与支持的图片列表中的Content Type保持一致。"f"是字符串格式化的方法。
                        # PNG图像：  f"data:image/png;base64,{base64_image}"
                        # JPEG图像： f"data:image/jpeg;base64,{base64_image}"
                        # WEBP图像： f"data:image/webp;base64,{base64_image}"
                    *[
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpg;base64,{image}"}, 
                        }
                        for image in encoded_images
                    ],
                    {"type": "text", "text": text},
                ],
            }
        ],
    )
    print("response:",completion.choices[0].message.content)
    print("-------------------------------------------------------------")
    return (completion.choices[0].message.content)


def HttpLLM(url,model,content):
    url = url
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": False,
        "max_tokens": 512,
        "stop": None,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"},
        "tools": [
            {
                "type": "function",
                "function": {
                    "description": "<string>",
                    "name": "<string>",
                    "parameters": {},
                    "strict": False
                }
            }
        ]
    }
    headers = {
        "Authorization": "Bearer sk-guywwcbzaquapnarghajysvctzjtezvyebhqvtlmcqqdxzvt",
        "Content-Type": "application/json"
    }
    try:
        print("开始向LLM发起请求")
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()
        print("response:",response.text)
        print("-------------------------------------------------------------")
        return response
    except requests.exceptions.HTTPError as http_err:
        # 捕获 HTTP 错误（例如 404, 500 等）
        print(f"HTTP 错误: {http_err}")
        print("状态码:", response.status_code)
        print("响应内容:", response.text)

    except requests.exceptions.ConnectionError as conn_err:
        # 捕获连接错误（例如 DNS 解析失败、网络不可达等）
        print(f"连接错误: {conn_err}")

    except requests.exceptions.Timeout as timeout_err:
        # 捕获请求超时错误
        print(f"请求超时: {timeout_err}")

    except requests.exceptions.RequestException as req_err:
        # 捕获所有其他 requests 相关的异常
        print(f"请求异常: {req_err}")

    except ValueError as json_err:
        # 捕获 JSON 解析错误（例如响应内容不是有效的 JSON）
        print(f"JSON 解析错误: {json_err}")
        print("响应内容:", response.text)

    except Exception as e:
        # 捕获其他未知异常
        print(f"未知错误: {e}") 
    

def getLLMAns(content):
    #假设LLM回答无多选项情况,当前直接获取回答内容忽略过程参数
    LLMresponse = json.loads(HttpLLM(URL,MAINMODEL,content).text)
    response_content=(LLMresponse.get('choices')[0]).get('message').get('content')
    return response_content

def getLLMChunk(content):
    #假设LLM回答无多选项情况,当前直接获取回答内容忽略过程参数
    LLMresponse = json.loads(HttpLLM(URL,MAINMODEL,content).text)
    response_content=(LLMresponse.get('choices')[0]).get('message').get('content')
    return response_content

def getMLMAns(Image_path_list,content):
    
    MLMresponse = json.loads(HttpMLM(Image_path_list,content))
    return MLMresponse