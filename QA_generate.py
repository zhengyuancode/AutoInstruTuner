from LLM_tools import getLLMAns,getMLMAns
from Data_seg import getChunks
import json
import ast
import re
import logging

INPUT="dataSource\\6016B(1-4).md"
OUTPUT1="Output\\qa_pairs_6016B_test.json"
OUTPUT2="Output\\Alpaca_6016B_test.json"
LANGUAGES="english"



format_example='''[{"question":"...","answer":"..."},{"question":"...","answer":"..."},...]'''



def generate_qa_pairs_LLMs(chunk,languages):
    # 构建提示，明确告诉模型你需要从这段文本中抽取QA对
    prompt_LLM = f'''\n\
                <instruction> \n \
               Summarize and extract multiple questions and answer pairs from the following text, \
               and return them in list format only.\n\
                Each element in the list is a dictionary, and each dictionary only contains two keys, "question" and "answer"\n \
                If the given text cannot summarize the information, please return an empty list directly:"[]".\n \
                Your output language must be {languages} \n\
               </instruction> \n\
                <Format example> \n \
                    {format_example} \n \
                </Format example> \n \
                Now, let's get started:\n \
                <text>\n \
               {chunk}\n\
                </text>\n \
                '''
    return getLLMAns(prompt_LLM)

def generate_qa_pairs_MLMs(Image_path_list,chunk_text,languages):
    # 构建提示，明确告诉模型你需要从这段文本中抽取QA对
    prompt_MLM = f'''\n\
                <instruction> \n \
               Summarize and extract multiple questions and answer pairs from the text and picture, \
               and return them in list format only.\n\
                Each element in the list is a dictionary, and each dictionary only contains two keys, "question" and "answer"\n \
                If the given text and picture cannot summarize the information, please return an empty list directly:"[]".\n \
                Your output language must be {languages} \n\
               </instruction> \n\
                <Format example> \n \
                    {format_example} \n \
                </Format example> \n \
                Now, let's get started:\n \
                <text>\n \
               {chunk_text}\n\
                </text>\n \
                '''
    return getMLMAns(Image_path_list,prompt_MLM)

def load_json_list(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON文件内容必须为列表类型")
            return data
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 不存在")
        return None
    except json.JSONDecodeError:
        print("错误：JSON文件格式不正确")
        return None

#chunk预处理，识别出纯文本chunk和多模态chunk
def process_chunk(chunk):
    text_sentences = []
    image_paths = []
    pattern = re.compile(r'!\[\]\((images/[^)]+)\)')

    for sentence in chunk:
        match = pattern.match(sentence)
        if match:
            image_paths.append(match.group(1))
        else:
            text_sentences.append(sentence)
    
    if image_paths:
        return {
            'text': ' '.join(text_sentences),
            'image': image_paths
        }
    else:
        return ' '.join(text_sentences)

def save_to_file(qa_pairs,file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(qa_pairs, file, ensure_ascii=False, indent=4)


# 转换函数,qa对->Alpaca格式
def transform_data(data_list):
    transformed_list = []
    for item in data_list:
        transformed_item = {
            "instruction": item["question"],
            "input": item["chunk"],  # input即当前元素提取的chunk依据
            "output": item["answer"]
        }
        transformed_list.append(transformed_item)
    return transformed_list

def main():
    # Chunks=getChunks(INPUT,LANGUAGES)
    Chunks=load_json_list("Output\\Chunk\\mychunk.json")
    i=0
    qa_pairs=[]
    while(i<len(Chunks)):
        try:
            #chunk预处理，多模态参与融合工作
            chunk=process_chunk(Chunks[i])
            if isinstance(chunk, str):
                print("开始处理纯文本chunk")
                qa_list = ast.literal_eval(generate_qa_pairs_LLMs(chunk,LANGUAGES))
            elif isinstance(chunk, dict):
                print("开始处理多模态chunk")
                qa_list = list(generate_qa_pairs_MLMs(chunk["image"],chunk["text"],LANGUAGES))
                
            
            if qa_list == []:
                print("当前chunk无法由LLM总结")
                i=i+1
                continue
            for item in qa_list:
                if set(item.keys()) != {'question', 'answer'}:
                    raise ValueError("LLM格式回答错误")
            for qa in qa_list:
                if isinstance(chunk, str):
                    qa['chunk']=chunk
                elif isinstance(chunk, dict):
                    qa['chunk']=chunk["text"]
                
            print("qa_list:",qa_list)
            print("-------------------------------------------------------------")
            qa_pairs.extend(qa_list)
            i=i+1
        except:
            print(f"LLM格式回答错误 | 重新开始生成...")
            continue
        # except Exception as e:
        #     logging.error("发生异常:", exc_info=True)
            
    save_to_file(qa_pairs,OUTPUT1)
    
    Alpaca_list=transform_data(qa_pairs)
    save_to_file(Alpaca_list,OUTPUT2)

if __name__ == "__main__":
    main()
