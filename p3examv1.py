
# coding: utf-8

# ## 作业实现思路说明
# 利用python通过mongodb进行数据分析工作，工作重心在于前期数据整理和之后的查询分析。根据所学知识，首先需要进行数据准备工作，对读入的样本数据进行测试，检查数据规范性、是否存在不正常的数据。修复数据后整理成可插入的数据格式插入到mongo中，再做后续的各类分析，挖掘数据信息

# ### 键值组合模式分析
# 通过之前的课程学习，能够了解到所有提交的数据都可能存在一些并不规范的数据，为了能够统一的进行识别处理按照所学知识对所有tag标签的属性值进行收集检查。排查分析后的数据可知，k键值对中可能存在异常字符影响分析的标签属性有14个，没有进行归类定义的有8601个，其他基本都属于比较合理常见的键值，

# In[1]:



import xml.etree.cElementTree as ET
import pprint
import re
import codecs


"""
针对数据和官网介绍的信息数据结构说明，以及之前项目整理的正则表达式，分析出目前数据中能发现的几种情况，其中对问题数据和未归类数据都将进行具体数据的记录
生成问题数据文件，尝试过直接输出在页面，但是会影响加载速度，因此单独保存问题数字字段
"""

lower = re.compile(r'^([a-z]|_)*$')
upper = re.compile(r'^([A-Z]|_)*$')
mixed = re.compile(r'^([a-zA-Z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
splittime = ["1次分割", "2次分割", "3次分割", "4次分割"]
othercnt = []
problemcnt = []


def key_type(element, keys):
    if element.tag == "tag":
        key = element.attrib['k']
        keys=status_colon(key,keys)   
    return keys

def status(key):
    if problemchars.search(key):
        problemcnt.append(key)
        return "异常字符"
    elif lower.search(key):
        return "小写"
    elif upper.search(key):
        return "大写"
    elif mixed.search(key):
        return "大小写混合"
    else:
        othercnt.append(key)
        return "其他类型"

def status_colon(key,keys):
    keySplit = check_colon(key)
    if(len(keySplit)==1):
        process_status(splittime[0], keys)   
        keyStatus=status(key)        
        process_status(keyStatus, keys)
    else:
        keyStatus=splittime[len(keySplit)-1]
        process_status(keyStatus, keys)
        
    return keys

def check_colon(key):
    return re.split('\:', key)

def process_status(status, keys):
    if status in keys:
        keys[status] += 1
    else:
        keys[status] = 1
    return keys


def process_map(filename):
    keys = {}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
        element.clear()
    return keys

def test():
    keys = process_map('chicago.osm')
    pprint.pprint(keys)
    
    file_out = "problemchars-chicago.csv"
    data = []
    with codecs.open(file_out, "w", "utf-8") as fo:
        for line in problemcnt:
            fo.write(line+"\n")

    file_out = "othercntchars-chicago.csv"
    with codecs.open(file_out, "w", "utf-8") as fo:
        for line in othercnt:
            fo.write(line+"\n")
            
            
if __name__ == "__main__":
    test()
    


# #### 统计文件中出现过的所有标签数量和标签内attribute属性键值对的数量
# 设定数据整理思路需要了解大概的标签结构构成。通过结合官方文档说明以及样本数据的构成，设计对本次作业最有效的数据整理方式。
# 除了文件描述标签外，实际存在的标签可以分为 member，node，tag，relation，way，nd，标签次数记录在attrnum，每个标签的attribute分别记录，通过这种方式可以更好的规划到每个标签在后续过程中需要进行的数据处理判断逻辑

# In[3]:



"""
首先从数据表中了解有多少个标签tag,以及每个标签下有多少个属性attr，后续在数据整理入库时作为结构参考
"""
import xml.etree.cElementTree as ET

def collect_tags(filename):
   
    tags={}
    
    
    for event, elem in ET.iterparse(filename):
        if event == 'end':
            tag = elem.tag
            #区分现在的字典表中是否有标签存在，并进行初始化或者计数
            if tag not in tags.keys():
                tags[tag]={}
                tags[tag]["attrnum"]=1
            else:
                tags[tag]["attrnum"]+=1
                
            #区分现在的标签字典表中是否有遍历的属性存在，并进行初始化或者计数
            attrkeys=elem.attrib            
            for key in attrkeys:          
                if(key not in tags[tag].keys()):
                    tags[tag][key]=1
                else:
                    tags[tag][key]+=1
        elem.clear() #通过测试发现如果不清空，内存不会释放
                
    return tags

##查组成要素数量
tags = collect_tags('chicago.osm')
pprint.pprint(tags)



# #### 统计标签结构化的情况，从而答题了解每个标签结构的组成，对于后续json序列化插入有关键的参考价值

# In[4]:

import pprint
import re
import codecs
import xml.etree.cElementTree as ET

##查数据结构，与上述需求不同检查，按照xml结构解析字段统计数
def get_inner_tages(keyDict, keyList):
    if len(keyList) == 1:

        if keyList[0] in keyDict:
            if "Total" in keyDict[keyList[0]]:
                keyDict[keyList[0]]["Total"] += 1
            else:
                keyDict[keyList[0]]["Total"] = 1
        else:
            keyDict[keyList[0]] = {"Total": 1}
    else:
        if keyList[0] not in keyDict:
            keyDict[keyList[0]] = {}
        get_inner_tages(keyDict[keyList[0]], keyList[1:])
    return keyDict


def process_map(filename):
    tags={}
    otheles={}
    for event, element in ET.iterparse(filename):
        if( event =='end'):
            if (element.tag in ["node","way"]):
                alltags = element.findall("tag")
                for tag in alltags:
                    if ((tag.tag == "tag")):
                        key = tag.attrib['k']
                        keySplit = re.split('\:', key)
                        tags = get_inner_tages(tags, keySplit)         
                element.clear()
            else:
                otheles[element.tag]=element.tag
    pprint.pprint(otheles)
    return tags

tags= process_map("chicago.osm")
tags


# ### 替换缩写变成标准单词
# addr:street记录了街道名称，其中出现了各类有个人色彩的缩写，因此通过先输出一次后得出所有addr:street名称结果，并针对结果进行整理后更新，将所有收集到的缩写更新为标准词组

# In[5]:

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

# 经过测试 有些字段可以直接判定不需要进行更新的，单独列出
exception=["East","Damen","Belmont","US-6","Ter","Wabansia","O"]

def convert_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if (street_type not in expected) and (street_type not in exception):
            street_types[street_type].add(street_name)


def audit(osmfile):
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osmfile, events=("end",)):
#   for event, elem in ET.iterparse(osmfile, events=("start",)):
#       if (elem.tag == "node" or elem.tag == "way"):
#            for tag in elem.iter("tag"):
#                if (tag.attrib['k'] == "addr:street"):
#                    convert_street_type(street_types, tag.attrib['v'])
#        elem.clear()

        if (elem.tag in ["node","way"]):
                alltags = elem.findall("tag")  ##效果与.iter效果相同，但一种方式采用end结束处理，另外一种方式采用start方式处理
                for tag in alltags:
                    if ((tag.tag == "tag")):
                        if (tag.attrib['k'] == "addr:street"):
                            convert_street_type(street_types, tag.attrib['v']) 
                elem.clear()
       

    return street_types

def test():
    st_types = audit('chicago.osm')
    pprint.pprint(dict(st_types))
    print("----------------------------------------------------------")
    
if __name__ == '__main__':
    test()


# In[6]:

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

# 经过测试 有些字段可以直接判定不需要进行更新的，单独列出
exception=["East","Damen","Belmont","US-6","Ter","Wabansia","O"]

def convert_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if (street_type not in expected) and (street_type not in exception):
            street_types[street_type].add(street_name)
            
            
def audit(osmfile):
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osmfile, events=("end",)):
#   for event, elem in ET.iterparse(osmfile, events=("start",)):
#       if (elem.tag == "node" or elem.tag == "way"):
#            for tag in elem.iter("tag"):
#                if (tag.attrib['k'] == "addr:street"):
#                    convert_street_type(street_types, tag.attrib['v'])
#        elem.clear()

        if (elem.tag in ["node","way"]):
                alltags = elem.findall("tag")  ##效果与.iter效果相同，但一种方式采用end结束处理，另外一种方式采用start方式处理
                for tag in alltags:
                    if ((tag.tag == "tag")):
                        if (tag.attrib['k'] == "addr:street"):
                            convert_street_type(street_types, tag.attrib['v']) 
                elem.clear()
       

    return street_types


#根据上一条操作的输出记录，展开替换所有已知缩写
mapping = { "St": "Street", "st": "Street",
            "St.": "Street",
            "Ave": "Avenue",
           "Ave.": "Avenue",
           "AVE.": "Avenue",
           "Dr": "drive",
           "Dr.": "drive",
           "Blvd": "boulevard",
           "Blvd.": "boulevard","blvd": "boulevard",
           "Fwy": "freeway",
           "Ln": "lane",
           "Wy": "way",
           "LN": "lane",
           "PKWY": "PARKWAY",
           "Pkwy": "PARKWAY","pkwy": "PARKWAY",
           "Rd": "Road","rd": "Road",
            "Rd.": "Road",
           "Cir":"circle",
           "CT":"court",
           "Ct.":"court",
           "Ct":"court",
           "Ctr.":"court","PLZ":"Plaza",
           "Hwy":"Highway",
           "HWY":"Highway",
           "Hwy.":"Highway"           
            }



def update_name(name, mapping):
    if(len(street_type_re.findall(name))>0):
        if street_type_re.findall(name)[0] in exception:
            return name
        else:
            substring=street_type_re.findall(name)[0]
            if(substring in mapping ):
                newname = street_type_re.sub(mapping[substring], name, 1 )
                return newname
            else:
                return name
    else:
        return name


def run():
    st_types = audit('chicago.osm')
    for st_type, ways in st_types.items():
            for name in ways:
                updatename = update_name(name, mapping)
                pprint.pprint(updatename)
            

if __name__ == '__main__':
    run()


# #### 将编辑替换以后的数据写入json文件并写入mongodb

# In[7]:

import pdb
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
from pymongo import MongoClient

'''
<node changeset="7781188" id="219850" lat="41.7585879" lon="-87.9101245" timestamp="2011-04-06T05:17:15Z" uid="207745" user="NE2" version="54">
    <tag k="exit_to" v="Joliet Road" />
    <tag k="highway" v="motorway_junction" />
    <tag k="ref" v="276C" />
  </node>
'''

crtinfo = [ "version", "user", "timestamp", "uid", "changeset"]

problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def  parseJson(element):
    node = {}
    if (element.tag in ["node","way","relation"]) :
        #print("parsejson: ",ET.tostring(element).decode())
        createdinfo = {} 
        geo = [] 
        node_refs = [] 
        
        members=[]
        
        node["id"] = element.attrib["id"]
        node["tagtype"] = element.tag
        
    
        try:
            geo.append(float(element.attrib["lat"]))
            geo.append(float(element.attrib["lon"]))
            node["geo"] = geo      
        except KeyError:
            pass
                
        for ck in crtinfo:
            if(ck in element.keys()):
                createdinfo[ck] = element.attrib[ck]  
        node["ndinfo"] = createdinfo
        
        
        for tag in element.iter("tag"): 
            #print(ET.tostring(tag))            
            key = tag.attrib["k"]    #k值存在多端切分:，需要分别保存
            value = tag.attrib["v"]
            arr = re.split('\:', key)
            node = parse_key(node, arr, value)

            try: 
                node["address"] = node.pop("addr")
            except KeyError:
                pass
            
        #relation有memeber节点    
        for mb in element.iter("member"): 
            #print(ET.tostring(tag))
            member={}
            for k in mb.attrib:
                member[k]= mb.attrib[k]
            members.append(member)
        node["member"]=members

        
        #way节点一般有nd关联节点
        for nd in element.iter("nd"): 
            node_refs.append(nd.attrib["ref"]) 
        node["node_refs"] = node_refs            
        
        return node
    else:
        return None

def parse_key(keyDict, keyList, keyValue):      
    if len(keyList) == 1:
        if(keyList[0]=='street'):
            keyValue=update_name(keyValue,mapping)
        keyDict[keyList[0]] = keyValue
    else:
        if keyList[0] not in keyDict:
            keyDict[keyList[0]] = {}
        if isinstance(keyDict[keyList[0]], dict):
            keyDict[keyList[0]]=parse_key(keyDict[keyList[0]], keyList[1:], keyValue)
        else:
            k = ""
            for key in keyList:
                k += key + "_"
            k = k[:-1] 
            keyDict[k] = keyValue
    return keyDict

 
### 经过尝试数据量过大，为了避免内存占用，通过直接传入数据库参数，在业务代码中直接插库，
### fmt支持输出保存数据格式化
def process_map(db,file_in, fmt = False):
    

    file_out = "{0}.json".format(file_in)
    data = []
    idx=0
    with codecs.open(file_out, "w", "utf-8") as fo:
        for event, elem in ET.iterparse(file_in, events=("start","end")):    #针对事件因为需要在内部展开子节点，因此需要events包括开口和闭口
            if(event=="start"):
                
                el = parseJson(elem)          
                idx+=1
                if el:   
                    
                    if fmt:
                        fo.write(json.dumps(el, indent=2)+",\n")
                    else:
                        fo.write(json.dumps(el) + "\n")
                    if("way" in elem.attrib):
                        pprint.pprint(el)
                    db.chicago.insert_one(el)
            elif(event=="end"):
                elem.clear()      
                
    print("all element ",idx)                
    return;


def runInsert():
   
    client = MongoClient("mongodb://192.168.3.155:27017")
    db = client.map
    process_map(db,'chicago.osm', True)
    

runInsert()
    


# In[8]:

import gc
gc.collect()


# In[9]:

import pdb
import string 
import pprint
from pymongo import MongoClient
import os
import re


# ## 基本数据概览
# 
# 数据源采用芝加哥城市数据进行分析，参考文件要求进行如下选择。
# 
# 1、数据文件大小 
# 数据文件大小在1.8GB
# 采用大型文本数据原因是为了检查使用python解析xml文件的功能理解，在数据准备及插入数据库过程中，基本流程内保证内存占用<800M
# 
# 2、本次数据清洗后入库有效数据9869440条。其中relation类型数据2484条，way类型数据1087021条，node类型数据7879935条。
# 
# 

# In[10]:


    
#query()

pprint.pprint("chicago.osm file size : "+ str(os.path.getsize('chicago.osm')))

client =MongoClient("mongodb://192.168.3.155:27017")
db = client.map.chicago


pprint.pprint("all rows " + str(db.count()))

rs= db.aggregate([{
            "$group":{"_id":"$tagtype", "count":{"$sum":1}}
        }])
pprint.pprint("all tag types " )
for doc in rs:
    pprint.pprint(doc)


# ## 数据统计维度分析
# 
# 
# ### 根据用户提交情况统计，展示哪些用户贡献度最高。按照贡献从多到少提供

# In[11]:


print("---------------------------------根据ndinfo.user统计设施次数----------------------------------------------")    
rs= db.aggregate([{
            "$group":{"_id":"$ndinfo.user", "count":{"$sum":1}}},{"$sort":{"count":-1}}
    ])

for doc in rs:
    pprint.pprint(doc)
    


# ### 按照 amenity  设施分类查看提交了多少种设施。由于插入数据中有多种类型，因此可看到没有amenity标签属性的数据最多，其次是公园6881次， place_of_worship理解为教堂等4314次，学校3389次。

# In[12]:


print("---------------------------------根据amenity统计设施次数----------------------------------------------")    
rs= db.aggregate([{
            "$group":{"_id":"$amenity", "count":{"$sum":1}}},{"$sort":{"count":-1}}
    ])

for doc in rs:
    pprint.pprint(doc)


# ### 按照 amenity  =school 提交过的全部学校名称，大部分学校都是唯一提交，有些学校被多个用户或者多次提交数据中。芝加哥全部的学校不区分小初高共有2839所，名称中有middle默认为中学，共有140所。其他学校经对数据抽样常看没有特定规律能够识别是小学或者高中

# In[13]:


print("---------------------------------根据amenity=school统计设施次数----------------------------------------------")    


rs= db.aggregate([
            {"$match":{"amenity":"school"}},
            {"$group":{"_id":"$name","count":{"$sum":1}}},
            {"$sort":{"count":-1}}
    ])

cnt=0
for doc in rs:
    pprint.pprint(doc)
    cnt=cnt+1

print("共有学校 "+str(cnt) +" 所") 


rs= db.aggregate([
            {"$match":{"amenity":"school","name":re.compile("middle",re.IGNORECASE)}},
            {"$group":{"_id":"$name","count":{"$sum":1}}},
            {"$sort":{"count":-1}}
    ])

cnt=0
for doc in rs:
    pprint.pprint(doc)
    cnt+=1

print("中学共有 "+str(cnt)+" 所")


# middle学校数据经由以下24名用户提交，最多提交次数83次，大部分都提交1个条。数据贡献集中在'iandees' 与 'Umbugbene'.针对用户iandees进行分析，得知该用户在各类数据节点都有贡献，贡献度最高的是完善了39483个node节点数据，并且提交了1925条学校信息和自行车出租(bicycle_rental)信息。以上三项是该用户在芝加哥开放数据中贡献最多的部分

# In[14]:


print("---------------------------------根据amenity=school,统计提交人情况统计设施次数----------------------------------------------")    


rs= db.aggregate([
            {"$match":{"amenity":"school","name":re.compile("middle",re.IGNORECASE)}},
            {"$group":{"_id":"$ndinfo.user","count":{"$sum":1}}},
            {"$sort":{"count":-1}}
    ])

cnt=0
for doc in rs:
    pprint.pprint(doc)
    cnt+=1

print("共有 "+str(cnt)+" 名用户提交")




# In[15]:


print("---------------------------------根据user=iandees,统计提交人情况统计设施次数----------------------------------------------")    


rs= db.aggregate([
            {"$match":{"ndinfo.user":"iandees"}},
            {"$group":{"_id":"$tagtype","count":{"$sum":1}}},
            {"$sort":{"count":-1}}
    ])

cnt=0
for doc in rs:
    pprint.pprint(doc)
    cnt+=1

print("iandees在 "+str(cnt)+" 类节点提交数据\r\n\r\n")

rs= db.aggregate([
            {"$match":{"ndinfo.user":"iandees"}},
            {"$group":{"_id":"$amenity","count":{"$sum":1}}},
            {"$sort":{"count":-1}}
    ])

cnt=0
for doc in rs:
    pprint.pprint(doc)
    cnt+=1

print("iandees在 "+str(cnt)+" 种amenity设施种类下提交")


# #### 项目参考说明
# 历史学生完成的优秀案例
# 
# https://github.com/baumanab/udacity_mongo_github/tree/master/final_project
# 
# 数据内存占用的性能评价
# 
# https://pycoders-weekly-chinese.readthedocs.io/en/latest/issue6/processing-xml-in-python-with-element-tree.html
# 
# 数据处理查询的技能点,包括mongo,xml处理形式
# 
# https://stackoverflow.com/search?q=python+pymongo
# https://stackoverflow.com/questions/tagged/python+xml+et
