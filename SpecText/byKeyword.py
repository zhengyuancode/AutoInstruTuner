import re
import json


with open('SpecText\\output\\All_blocks.json','r',encoding='utf8')as fp:
    Allblock = json.load(fp)

keywords = ["AWACS", "AEW&C", "Exchange of information", "Radar surveillance", "Coordinated operations","J3.6I","J3.6E0","J3.6E1","J3.6C1","J3.6C5","J3.2","J7.1"]
pattern = re.compile("|".join(keywords), re.IGNORECASE)

relevant_blocks = []

for block in Allblock:
    if(block.get("type")=="text"):
        text = block.get("text")
        if pattern.search(text):
            relevant_blocks.append(block)


with open('SpecText\\output\\relevant_blocks.json','a',encoding='utf8')as fp:
    json.dump(relevant_blocks,fp,ensure_ascii=False,indent=4)




    
    