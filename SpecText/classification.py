from transformers import pipeline

# 正确初始化 NLI Pipeline（明确指定任务和模型）
nli_pipeline = pipeline(
    task="text-classification",
    model="roberta-large-mnli",
    return_all_scores=True  # 获取所有标签的概率
)

def get_entailment_score(text1, text2):
    # 构建输入格式：将 text1 作为前提，text2 作为假设
    premise = text1
    hypothesis = text2  # 或自定义逻辑（如 "Therefore, " + text2）
    
    # 正确调用 Pipeline（传入单个字典或字符串对）
    result = nli_pipeline(
        {
            "text": premise,          # 前提文本
            "text_pair": hypothesis   # 假设文本
        }
    )
    
    # 提取"蕴含"（ENTAILMENT）标签的概率
    # 标签顺序：["contradiction", "neutral", "entailment"]
    entailment_score = result[0][2]["score"]  # 索引2对应"entailment"
    return entailment_score

# 示例使用
text1 = "The cat is sleeping on the mat."
text2 = "A cat is resting on a mat."
score = get_entailment_score(text1, text2)
print(f"逻辑连贯性得分：{score:.4f}")