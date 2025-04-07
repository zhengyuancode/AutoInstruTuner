import nltk
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from Data_pretreatment import read_docx,read_txt,preprocess_text,read_md,read_pdf
from LLM_tools import  getLLMChunk
import pkuseg
import json
#解析md并分块
from markdown_it import MarkdownIt
import re


# # 首次运行需确保下载了nltk的punkt分词器
# nltk.download('punkt')
# nltk.download('punkt_tab')

CHUNKFILE="Output\\Chunk\\mychunk.json"

def read_and_preprocess(file_path):
    # 根据文件类型调用相应的读取函数
    text = read_pdf(file_path) if file_path.endswith('.pdf') else (
        read_docx(file_path) if file_path.endswith('.docx') else (
        read_md(file_path) if file_path.endswith('.md') else read_txt(file_path)
        )
    )
    return preprocess_text(text)


def CHsplit(text):
    seg = pkuseg.pkuseg()
    words = seg.cut(text)
    
    sentences = []
    current_sentence = []

    for word in words:
        current_sentence.append(word)
        if word in ['。', '！', '？']:
            sentences.append(''.join(current_sentence))
            current_sentence = []
    
    if current_sentence:
        sentences.append(''.join(current_sentence))
    return sentences

# def split_into_sentences(text, languages):   
#     # 匹配图片（如![](...)）和HTML块（如<html>...</html>）
#     pattern = re.compile(
#         r'(!\[[\s\S]*?\]\([\s\S]*?\))|(<html>[\s\S]*?</html>)',
#         re.IGNORECASE  # 不区分大小写匹配HTML标签
#     )
    
#     sentences = []
#     pos = 0  # 当前处理到的文本位置
    
#     # 遍历所有特殊结构匹配项
#     for match in pattern.finditer(text):
#         start, end = match.start(), match.end()
#         # 处理特殊结构前的普通文本
#         ordinary_text = text[pos:start]
#         if ordinary_text:
#             if languages == 'english':
#                 sentences.extend(nltk.sent_tokenize(ordinary_text))
#             elif languages == 'chinese':
#                 sentences.extend(CHsplit(ordinary_text))
#             else:
#                 raise ValueError("Language must be 'english' or 'chinese'.")
#         # 添加特殊结构作为独立句子
#         sentences.append(match.group())
#         pos = end  # 更新当前位置
    
#     # 处理剩余普通文本
#     ordinary_text = text[pos:]
#     if ordinary_text:
#         if languages == 'english':
#             sentences.extend(nltk.sent_tokenize(ordinary_text))
#         elif languages == 'chinese':
#             sentences.extend(CHsplit(ordinary_text))
#         else:
#             raise ValueError("Language must be 'english' or 'chinese'.")
    
#     print("sentences complete")
#     return sentences
def _split_and_extend(text, sentences, lang):
    """分句处理逻辑保持不变"""
    if not text.strip():
        return
    
    try:
        if lang == 'english':
            sentences.extend(nltk.sent_tokenize(text))
        elif lang == 'chinese':
            sentences.extend(CHsplit(text))
        else:
            raise ValueError("Unsupported language")
    except Exception as e:
        print(f"分句错误: {str(e)}")
        sentences.append(text)

#TODO：测试是否是最佳分句方式了
def split_into_sentences(text, languages):
    # 匹配图片/表格元素及其后续描述（修正版）
    pattern = re.compile(
        r'(?:!\[[\s\S]*?\]\(.*?\)|<\s*html[\s\S]*?</html>)'  # 图片或表格
        r'(?:\s*(?:Figure\s+[\d.-]+[^!<.#]*|图\s*[\d.-]+[^!<.#]*|Table\s+[\d.-]+[^!<.#]*|表\s*[\d.-]+[^!<.#]*))?',  # 可选描述
        re.IGNORECASE
    )
    
    sentences = []
    pos = 0
    
    for match in pattern.finditer(text):
        full_match = match.group()
        start, end = match.start(), match.end()
        
        if start > pos:
            ordinary_text = text[pos:start]
            _split_and_extend(ordinary_text, sentences, languages)
        
        sentences.append(full_match.strip())
        pos = end
    
    if pos < len(text):
        ordinary_text = text[pos:]
        _split_and_extend(ordinary_text, sentences, languages)
    
    return sentences


    
def generate_embeddings(sentences):
    print("embeddings begin")
    model = SentenceTransformer('all-MiniLM-L6-v2')  # 使用一个轻量级的模型
    embeddings = model.encode(sentences)
    print("embeddings complete")
    return embeddings

#基于语义相似度分块，简化版，对于非常大的文档此方法可能会比较耗时，因为计算句子间的相似度是一个相对昂贵的操作。
# 在这种情况下，可以考虑优化算法或者使用更高效的数据结构来加速处理过程。
#similarity_threshold是一个关键参数，它决定了句子之间需要有多高的相似度才能被归为同一块
#all-MiniLM-L6-v2作为示例，因为它体积小且速度较快。
def chunk_based_on_similarity(sentences, embeddings, similarity_threshold=0.6):
    chunks = []
    current_chunk = [sentences[0]]
    for i in range(1, len(embeddings)):
        sim = cosine_similarity([embeddings[i-1]], [embeddings[i]])
        if sim >= similarity_threshold:
            current_chunk.append(sentences[i])
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentences[i]]
    chunks.append(" ".join(current_chunk))  # 添加最后一个块
    
    
    
    return chunks


#TODO：实现LLM看后面多句内容来判断下一句是否并入
# def chunk_based_on_LLMs(sentences):
#     def is_special_element(sentence):
#         """检测是否为图片或HTML表格元素"""
#         stripped = sentence.strip()
#         return stripped.startswith('![') or stripped.startswith('<html>')

#     def should_merge(result):
#         """解析LLM的返回结果"""
#         return result.strip().lower() in ['是', 'yes', 'y', 'true']

#     if not sentences:
#         return []

#     chunks = []
#     current_chunk = [sentences[0]]
    
#     for sentence in sentences[1:]:
#         # 特殊元素直接合并
#         if is_special_element(sentence):
#             current_chunk.append(sentence)
#             continue
            
#         # 构造LLM提示词
#         prompt = f"请判断以下内容是否可以划为同一个语义段落。\
#                 当前段落内容：{' '.join(current_chunk)}\n\
#                 后续句子：{sentence}\n\
#                 需要合并吗？请只回答是或否，不要给出理由。"
        
#         # 获取LLM判断结果
#         merge_decision = getLLMChunk(prompt)
        
#         if should_merge(merge_decision):
#             current_chunk.append(sentence)
#         else:
#             chunks.append(current_chunk)
#             current_chunk = [sentence]
    
#     # 添加最后一个块
#     if current_chunk:
#         chunks.append(current_chunk)
#     print(chunks)
#     return chunks

def chunk_based_on_LLMs(sentences, n=2, min_chunk_length=3):
    #TODO：微调一个二分类专业分块LLM能改进此效果
    """
    改进版段落切分算法
    :param sentences: 待分块的句子列表
    :param n: 前瞻句子数量（默认2）
    :param min_chunk_length: 最小段落长度阈值（默认3句）
    """
    def is_special_element(s):
        stripped = s.strip()
        return stripped.startswith(('![', '<html>', '<table>'))

    def should_merge(result):
        return result.strip().lower() in ['是', 'yes', 'y', 'true']

    if not sentences:
        return []

    chunks = []
    current_chunk = []
    
    # 预扫描所有特殊元素位置
    special_positions = {i for i,s in enumerate(sentences) if is_special_element(s)}

    i = 0
    while i < len(sentences):
        if not current_chunk:
            current_chunk.append(sentences[i])
            i += 1
            continue

        # 遇到特殊元素时强制合并
        if i in special_positions:
            current_chunk.append(sentences[i])
            i += 1
            continue

        # 动态计算实际可用的前瞻窗口
        lookahead_window = sentences[i:min(i+n, len(sentences))]
        
        # 构造提示词
        prompt = (
            "作为文本分段专家，请判断是否将后续内容合并到当前段落。需考虑：\n"
            "1. 语义连贯性（主要）\n2. 段落长度合理性\n3. 上下文逻辑关系\n\n"
            f"当前段落（{len(current_chunk)}句）: {' '.join(current_chunk[-3:])}\n"  # 显示最近3句避免过长
            f"待合并句: {sentences[i]}\n"
            f"后续{n}句上下文: {' '.join(lookahead_window[1:])}\n"
            "是否需要合并？请只回答是/否。"
        )

        merge_decision = getLLMChunk(prompt)
        
        if should_merge(merge_decision):
            current_chunk.append(sentences[i])
            i += 1
        else:
            # 长度不足时强制合并
            if len(current_chunk) < min_chunk_length and not chunks:
                chunks[-1].extend(current_chunk)
            else:
                chunks.append(current_chunk)
            current_chunk = []
    
    # 处理剩余内容
    if current_chunk:
        if len(current_chunk) < min_chunk_length and chunks:
            chunks[-1].extend(current_chunk)
        else:
            chunks.append(current_chunk)
            
            
    with open(CHUNKFILE, 'w', encoding='utf-8') as file:
        json.dump(chunks, file, ensure_ascii=False, indent=4)
        
    return chunks
    

def getChunks(file_path,languages):
    text = read_and_preprocess(file_path)
    sentences = split_into_sentences(text,languages)
    #获取sentences后可选分块策略
    #Todo：实现动态分块策略，LLM代理分块者
    
    
    
    #使用语义相似度分块
    embeddings = generate_embeddings(sentences)
    return chunk_based_on_similarity(sentences, embeddings)

# text=read_and_preprocess("Output\\6016B_test.md")
# sentences=split_into_sentences(text,"english")
# chunks = chunk_based_on_LLMs(sentences, n=3)  # LLM会参考后续n个句子做决策
# print(chunks)