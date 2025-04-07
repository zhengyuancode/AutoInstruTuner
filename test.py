import re
from Data_pretreatment import read_md


def merge_intervals(intervals):
    """合并重叠或相邻的区间"""
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_intervals[0]]
    for current in sorted_intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def find_previous_paragraph(text, position):
    """查找指定位置前最近的段落起始位置"""
    # 查找前两个换行符确定段落边界
    para_start = text.rfind('\n\n', 0, position-1)
    if para_start == -1:
        return 0
    else:
        return para_start + 2  # 跳过换行符

def split_content(text):
    # 匹配图片和表格的正则表达式
    pattern = re.compile(r'(!\[.*?\]\(.*?\)|<\/?html>.*?<\/html>)', re.DOTALL)
    
    # 存储块信息和排除区间
    blocks_info = []
    excluded_intervals = []
    
    # 第一次扫描：识别所有匹配项
    matches = list(pattern.finditer(text))
    if not matches:
        return [], text.strip()
    
    # 合并相邻的匹配项
    current_block = []
    prev_end = 0
    block_start = matches[0].start()
    block_end = matches[0].end()
    
    for match in matches[1:]:
        # 检查两个匹配项之间的内容是否为空白
        if re.match(r'^\s*$', text[prev_end:match.start()]):
            block_end = match.end()  # 扩展当前块结束位置
        else:
            # 保存当前块
            current_content = text[block_start:block_end]
            current_block.append((block_start, block_end, current_content))
            # 开始新块
            block_start = match.start()
            block_end = match.end()
        prev_end = match.end()
    
    # 保存最后一个块
    current_block.append((block_start, block_end, text[block_start:block_end]))
    
    # 处理每个块并查找描述文本
    for start, end, content in current_block:
        # 查找前一个段落作为描述
        desc_start = find_previous_paragraph(text, start)
        description = text[desc_start:start].strip()
        
        # 记录需要排除的区间（描述+内容）
        excluded_intervals.append((desc_start, end))
        
        blocks_info.append({
            'description': description,
            'content': content.strip(),
            'start': desc_start,
            'end': end
        })
    
    # 生成剩余文本
    merged = merge_intervals(excluded_intervals)
    remaining = []
    last_pos = 0
    
    for start, end in merged:
        if start > last_pos:
            remaining.append(text[last_pos:start])
        last_pos = end
    
    if last_pos < len(text):
        remaining.append(text[last_pos:])
    
    return blocks_info, ''.join(remaining).strip()

def save_blocks(blocks, remaining_text):
    # 保存带描述的块
    for idx, block in enumerate(blocks, 1):
        content = f"{block['description']}\n\n{block['content']}" if block['description'] else block['content']
        with open(f'block_{idx}.txt', 'w', encoding='utf-8') as f:
            f.write(content)
    
    # 保存剩余文本
    if remaining_text:
        with open('remaining_text.txt', 'w', encoding='utf-8') as f:
            f.write(remaining_text)


# 使用示例
if __name__ == "__main__":
    blocks, remaining = split_content(read_md("Output\\6016B_test.md"))
   
    print(blocks)
    
    # # 保存结果
    # save_blocks(blocks, remaining)
    # print(f'处理完成，共提取出{len(blocks)}个分块，剩余文本已保存。')

