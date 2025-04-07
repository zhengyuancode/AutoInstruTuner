import json


# 读取原MinerU中json文件内容,添加index重写
with open('MinerU/MinerU/6016B(1-4)_content_list.json','r',encoding='utf8')as fp:
    json_data = json.load(fp)

for i in range(0,len(json_data)):
    json_data[i]["index"]=i

with open('SpecText\\output\\All_blocks.json','a',encoding='utf8')as fp:
    json.dump(json_data,fp,ensure_ascii=False,indent=4)