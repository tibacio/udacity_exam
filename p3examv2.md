
## 作业实现思路说明
利用python通过mongodb进行数据分析工作，工作重心在于前期数据整理和之后的查询分析。根据所学知识，首先需要进行数据准备工作，对读入的样本数据进行测试，检查数据规范性、是否存在不正常的数据。修复数据后整理成可插入的数据格式插入到mongo中，再做后续的各类分析，挖掘数据信息

### 键值组合模式分析
通过之前的课程学习，能够了解到所有提交的数据都可能存在一些并不规范的数据，为了能够统一的进行识别处理按照所学知识对所有tag标签的属性值进行收集检查。排查分析后的数据可知，k键值对中可能存在异常字符影响分析的标签属性有14个，没有进行归类定义的有8601个，其他基本都属于比较合理常见的键值，


```python

# -*- coding: utf-8 -*-
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
    
```

    {'1次分割': 1617867,
     '2次分割': 3053318,
     '3次分割': 1487444,
     '其他类型': 8601,
     '大写': 1131,
     '大小写混合': 29,
     '小写': 1608092,
     '异常字符': 14}
    

#### 统计文件中出现过的所有标签数量和标签内attribute属性键值对的数量
设定数据整理思路需要了解大概的标签结构构成。通过结合官方文档说明以及样本数据的构成，设计对本次作业最有效的数据整理方式。
除了文件描述标签外，实际存在的标签可以分为 member，node，tag，relation，way，nd，标签次数记录在attrnum，每个标签的attribute分别记录，通过这种方式可以更好的规划到每个标签在后续过程中需要进行的数据处理判断逻辑


```python

# -*- coding: utf-8 -*-
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


```

    {'bounds': {'attrnum': 1,
                'maxlat': 1,
                'maxlon': 1,
                'minlat': 1,
                'minlon': 1,
                'origin': 1},
     'member': {'attrnum': 43678, 'ref': 43678, 'role': 43678, 'type': 43678},
     'nd': {'attrnum': 9072027, 'ref': 9072027},
     'node': {'attrnum': 7679935,
              'changeset': 7679935,
              'id': 7679935,
              'lat': 7679935,
              'lon': 7679935,
              'timestamp': 7679935,
              'uid': 7679934,
              'user': 7679934,
              'version': 7679935},
     'osm': {'attrnum': 1, 'generator': 1, 'version': 1},
     'relation': {'attrnum': 2484,
                  'changeset': 2484,
                  'id': 2484,
                  'timestamp': 2484,
                  'uid': 2484,
                  'user': 2484,
                  'version': 2484},
     'tag': {'attrnum': 6158629, 'k': 6158629, 'v': 6158629},
     'way': {'attrnum': 1087021,
             'changeset': 1087021,
             'id': 1087021,
             'timestamp': 1087021,
             'uid': 1087020,
             'user': 1087020,
             'version': 1087021}}
    

#### 统计标签结构化的情况，从而答题了解每个标签结构的组成，对于后续json序列化插入有关键的参考价值


```python
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
```

    {'bounds': 'bounds',
     'member': 'member',
     'nd': 'nd',
     'osm': 'osm',
     'relation': 'relation',
     'tag': 'tag'}
    




    {'Andover Court': {'Total': 1},
     'Comment': {'Total': 14},
     'FAA': {'Total': 1},
     'FIXME': {'Total': 274, 'railway': {'Total': 1}, 'ref': {'Total': 33}},
     'LAYER': {'Total': 4},
     'Length': {'Total': 1},
     'Location': {'Total': 1},
     'Montrose Avenue': {'Total': 1},
     'NHD': {'ComID': {'Total': 7675},
      'Elevation': {'Total': 101},
      'FCode': {'Total': 7665},
      'FDate': {'Total': 5230},
      'FTYPE': {'Total': 5227},
      'FType': {'Total': 2429},
      'GNIS_ID': {'Total': 80},
      'GNIS_Name': {'Total': 82},
      'RESOLUTION': {'Total': 5230},
      'ReachCode': {'Total': 6563},
      'way_id': {'Total': 2435}},
     'NHRP': {'Total': 1},
     'NHS': {'Total': 832},
     'NRHP': {'Total': 1},
     'TODO': {'Total': 3},
     'Train': {'Total': 1},
     'abandoned': {'Total': 25,
      'aeroway': {'Total': 1},
      'highway': {'Total': 19},
      'name': {'Total': 8}},
     'access': {'Total': 4232, 'conditional': {'Total': 1}},
     'add': {'city': {'Total': 1}},
     'addr': {'STE': {'Total': 1},
      'Total': 1,
      'city': {'Total': 20150},
      'country': {'Total': 1798},
      'full': {'Total': 43},
      'housename': {'Total': 145},
      'housenumber': {'Total': 507957},
      'interpolation': {'Total': 30},
      'place': {'Total': 1},
      'postcode': {'Total': 25809},
      'province': {'Total': 2},
      'state': {'Total': 2634},
      'street': {'Total': 508039,
       'name': {'Total': 503165},
       'prefix': {'Total': 486054},
       'suffix': {'Total': 55},
       'type': {'Total': 497420}},
      'suite': {'Total': 11},
      'unit': {'Total': 19}},
     'admin_level': {'Total': 18},
     'advertising': {'Total': 3},
     'aerodrome': {'Total': 1},
     'aeroway': {'Total': 1509},
     'airport_ref': {'Total': 277},
     'alt': {'Total': 1},
     'alt_name': {'Total': 157},
     'amenity': {'Total': 21403},
     'architect': {'Total': 28},
     'area': {'Total': 783},
     'artist_name': {'Total': 20},
     'artwork_type': {'Total': 22},
     'athletics': {'Total': 8},
     'atm': {'Total': 77},
     'attraction': {'Total': 10},
     'attribution': {'Total': 2470},
     'automated': {'Total': 1},
     'b': {'Total': 1},
     'backrest': {'Total': 4},
     'bar': {'Total': 2},
     'barrier': {'Total': 1772},
     'baseball': {'Total': 1},
     'basin': {'Total': 50},
     'bench': {'Total': 45},
     'bicycle': {'Total': 4960},
     'bicycle_parking': {'Total': 3},
     'board_type': {'Total': 1},
     'boat': {'Total': 172},
     'border': {'Total': 1},
     'border_type': {'Total': 8},
     'bottle': {'Total': 13},
     'boundary': {'Total': 4094, 'type': {'Total': 1}},
     'boundary_type': {'Total': 2},
     'brand': {'Total': 113},
     'bridge': {'Total': 6550},
     'bridge_number': {'Total': 15},
     'building': {'Total': 834137,
      'height': {'Total': 43},
      'id': {'Total': 36},
      'level': {'Total': 1},
      'levels': {'Total': 426248},
      'min_level': {'Total': 5},
      'part': {'Total': 53},
      'use': {'Total': 854}},
     'bus': {'Total': 36},
     'busway': {'Total': 6},
     'cables': {'Total': 493},
     'cans': {'Total': 1},
     'capacity': {'Total': 738,
      'disabled': {'Total': 5},
      'parent': {'Total': 3},
      'women': {'Total': 3}},
     'census': {'population': {'Total': 221}, 'year': {'Total': 1}},
     'chain': {'Total': 1},
     'chicag': {'building_id': {'Total': 1}},
     'chicago': {'building_id': {'Total': 735157}},
     'chicago_buildingid': {'Total': 1},
     'chilled': {'Total': 13},
     'chocolate': {'Total': 1},
     'cinema': {'3D': {'Total': 1}},
     'city_served': {'Total': 3},
     'closed': {'Total': 1},
     'clothes': {'Total': 4},
     'collection_time': {'Total': 1},
     'collection_times': {'Total': 5},
     'community': {'Total': 1, 'en': {'Total': 1}},
     'construction': {'Total': 116},
     'contact': {'email': {'Total': 1},
      'fax': {'Total': 9},
      'phone': {'Total': 35},
      'website': {'Total': 24}},
     'content': {'Total': 385},
     'contents': {'Total': 1},
     'conveying': {'Total': 13},
     'country': {'Total': 1},
     'covered': {'Total': 138},
     'craft': {'Total': 2},
     'created_by': {'Total': 9718},
     'crossing': {'Total': 69},
     'cta': {'objectid': {'Total': 12}, 'segmentid': {'Total': 12}},
     'cuisine': {'Total': 1078},
     'culvert': {'Total': 4},
     'cutting': {'Total': 4},
     'cycleway': {'Total': 1136, 'left': {'Total': 3}, 'right': {'Total': 8}},
     'dataset': {'Total': 1},
     'deep_draft': {'Total': 23},
     'delivery': {'Total': 9},
     'demolished': {'Total': 1},
     'denomination': {'Total': 2530},
     'depth': {'Total': 1},
     'description': {'Total': 55},
     'designation': {'Total': 148},
     'diesel': {'Total': 3},
     'diplomatic': {'Total': 1},
     'direction': {'Total': 1},
     'dispensing': {'Total': 40},
     'display': {'Total': 3},
     'disused': {'Total': 11},
     'divider': {'Total': 1},
     'divvy': {'id': {'Total': 300}},
     'drinkable': {'Total': 5},
     'drive_in': {'Total': 1},
     'drive_through': {'Total': 30},
     'drive_thru': {'Total': 1},
     'education': {'Total': 1},
     'ele': {'Total': 12783},
     'electrified': {'Total': 7356},
     'elevator': {'Total': 1},
     'email': {'Total': 3},
     'embankment': {'Total': 72},
     'emergency': {'Total': 86},
     'end_date': {'Total': 3},
     'entarnce': {'Total': 3},
     'entrance': {'Total': 344},
     'ethanol': {'Total': 2},
     'exit_to': {'Total': 547},
     'fax': {'Total': 5},
     'fee': {'Total': 133},
     'female': {'Total': 3},
     'fence_type': {'Total': 4},
     'fenced': {'Total': 1},
     'fire_hydrant': {'type': {'Total': 27}},
     'fireplace': {'Total': 2},
     'fishing': {'Total': 1},
     'fixme': {'Total': 1216},
     'food': {'Total': 9},
     'foot': {'Total': 7176},
     'footway': {'Total': 150},
     'former_name': {'Total': 1},
     'frequency': {'Total': 1671},
     'fuel': {'cng': {'Total': 1},
      'diesel': {'Total': 7},
      'e10': {'Total': 1},
      'ethanol': {'Total': 1},
      'octane_91': {'Total': 4},
      'octane_95': {'Total': 3},
      'octane_98': {'Total': 3}},
     'gauge': {'Total': 7797},
     'generator': {'method': {'Total': 17},
      'output': {'electricity': {'Total': 14}},
      'plant': {'Total': 2},
      'source': {'Total': 25},
      'type': {'Total': 2}},
     'geological': {'Total': 1},
     'gis': {'created': {'Total': 1},
      'feature_id': {'Total': 1},
      'state_id': {'Total': 1}},
     'glass': {'Total': 1},
     'gnis': {'Class': {'Total': 983},
      'County': {'Total': 986},
      'County_num': {'Total': 985},
      'ST_alpha': {'Total': 985},
      'ST_num': {'Total': 985},
      'county_id': {'Total': 10221},
      'county_name': {'Total': 1305},
      'created': {'Total': 10499},
      'edited': {'Total': 45},
      'feature_id': {'Total': 12725},
      'feature_type': {'Total': 259},
      'id': {'Total': 984},
      'import_uuid': {'Total': 1049},
      'reviewed': {'Total': 1033},
      'state_id': {'Total': 10223}},
     'gnis_feature_id': {'Total': 1},
     'gnis_id': {'Total': 1},
     'gnis_state_id': {'Total': 1},
     'gofl': {'Total': 2},
     'golf': {'Total': 7276},
     'golf_cart': {'Total': 1197},
     'grass': {'Total': 3392},
     'grassland': {'Total': 33},
     'harbor': {'Total': 2},
     'health_specialty': {'Total': 1},
     'height': {'Total': 53, 'source': {'Total': 1}},
     'heritage': {'Total': 2, 'operator': {'Total': 2}},
     'hgv': {'Total': 2183, 'national_network': {'Total': 67}},
     'high': {'Total': 2},
     'highway': {'Total': 202320},
     'historic': {'Total': 165, 'amenity': {'Total': 2}, 'nrhp': {'Total': 5}},
     'history': {'Total': 46},
     'horse': {'Total': 1979},
     'ia_in': {'Total': 1},
     'iata': {'Total': 13},
     'icao': {'Total': 7},
     'iis': {'Total': 3},
     'image': {'Total': 1},
     'import_uuid': {'Total': 985},
     'incline': {'Total': 19},
     'indoor': {'Total': 144},
     'industrial': {'Total': 1},
     'information': {'Total': 3},
     'inscription': {'Total': 1},
     'internet_access': {'Total': 16, 'fee': {'Total': 2}},
     'is': {'Total': 3},
     'is_In': {'Total': 12},
     'is_in': {'Total': 3380,
      'continent': {'Total': 8},
      'country': {'Total': 8},
      'state': {'Total': 1}},
     'junction': {'Total': 82},
     'key': {'Total': 2},
     'kosher': {'Total': 5,
      'certification': {'Total': 1},
      'glatt': {'Total': 1},
      'pas_yisrael': {'Total': 1},
      'yoshon': {'Total': 1}},
     'landuse': {'Total': 11224},
     'lanes': {'Total': 4855, 'backward': {'Total': 10}, 'forward': {'Total': 10}},
     'layer': {'Total': 5501},
     'leisure': {'Total': 10720},
     'length': {'Total': 8},
     'level': {'Total': 67},
     'level_crossing': {'Total': 1},
     'levels': {'Total': 2},
     'levels_aboveground': {'Total': 1},
     'lighted': {'Total': 1},
     'link': {'facebook': {'Total': 1},
      'foursquare': {'Total': 3},
      'google_plus': {'Total': 2}},
     'list': {'Total': 1},
     'lit': {'Total': 803},
     'loc_name': {'Total': 92},
     'loc_ref': {'Total': 325},
     'local_ref': {'Total': 7},
     'lock': {'Total': 5},
     'locked': {'Total': 1},
     'lutheran': {'Total': 2},
     'male': {'Total': 3},
     'man_made': {'Total': 1633},
     'marked_trail': {'Total': 92},
     'marker': {'Total': 11},
     'material': {'Total': 4},
     'mattress': {'Total': 2},
     'maxheight': {'Total': 1},
     'maxspeed': {'Total': 1254},
     'maxstay': {'Total': 5},
     'maxweight': {'Total': 8},
     'memorial': {'Total': 1},
     'microbrewery': {'Total': 10},
     'milepost': {'Total': 13},
     'military': {'Total': 1},
     'monitoring_station': {'Total': 1},
     'motor_vehicle': {'Total': 1590},
     'motorcar': {'Total': 50},
     'motorroad': {'Total': 1},
     'multi-story': {'Total': 1},
     'na': {'Total': 2},
     'name': {'': {'Total': 1},
      'Total': 142774,
      'bn': {'Total': 1},
      'bridge': {'Total': 1},
      'en': {'Total': 4},
      'es': {'Total': 2},
      'he': {'Total': 1},
      'hi': {'Total': 1},
      'kn': {'Total': 1},
      'lv': {'Total': 3},
      'pl': {'Total': 1},
      'railway': {'Total': 6},
      'ru': {'Total': 6}},
     'name2': {'Total': 3},
     'name_1': {'Total': 7905},
     'name_2': {'Total': 543},
     'name_3': {'Total': 51},
     'name_4': {'Total': 1},
     'name_former': {'Total': 1},
     'name_other': {'Total': 3},
     'naptan': {'Bearing': {'Total': 1}},
     'nat_name': {'Total': 4},
     'nat_ref': {'Total': 7},
     'natural': {'Total': 11727},
     'network': {'Total': 27},
     'nist': {'fips_code': {'Total': 1}, 'state_fips': {'Total': 1}},
     'noexit': {'Total': 90},
     'noname': {'Total': 3},
     'noref': {'Total': 159},
     'note': {'Total': 374,
      'lanes': {'Total': 39},
      'old_railway_operator': {'Total': 863}},
     'odbl': {'Total': 2173, 'note': {'Total': 35}},
     'office': {'Total': 21},
     'old_name': {'Total': 298},
     'old_railway_operator': {'Total': 4577},
     'old_ref': {'Total': 545},
     'oneay': {'Total': 1},
     'oneway': {'Total': 25327, 'bicycle': {'Total': 2}, 'bus': {'Total': 2}},
     'opened': {'Total': 1},
     'opening_hours': {'Total': 182},
     'operator': {'Total': 9010},
     'organic': {'Total': 1},
     'os': {'Total': 4},
     'outdoor_seating': {'Total': 45},
     'owner': {'Total': 3},
     'ownership': {'Total': 1},
     'park_ride': {'Total': 7},
     'parking': {'Total': 4135,
      'fee': {'Total': 1},
      'lane': {'right': {'Total': 1}}},
     'passengers': {'Total': 1},
     'paved': {'Total': 4},
     'payment': {'bitcoin': {'Total': 7},
      'coins': {'Total': 1},
      'mobile_phone': {'Total': 1}},
     'phone': {'Total': 321},
     'place': {'Total': 1263},
     'planned': {'Total': 1},
     'platforms': {'Total': 29},
     'playground': {'Total': 3},
     'pointless_but_fun': {'Total': 1},
     'population': {'Total': 225},
     'postal_code': {'Total': 10},
     'power': {'Total': 12221},
     'power_rating': {'Total': 4},
     'private': {'Total': 3},
     'proposed': {'Total': 94},
     'protect_class': {'Total': 2},
     'protect_id': {'Total': 1},
     'protected': {'Total': 1},
     'protection_title': {'Total': 2},
     'psv': {'Total': 13},
     'public_transit': {'Total': 3},
     'public_transport': {'Total': 782},
     'radar': {'Total': 1},
     'railway': {'Total': 18748},
     'ramp': {'Total': 6},
     'rank': {'Total': 1},
     'rcn': {'Total': 215},
     'rcn_ref': {'Total': 7},
     'recycling': {'computers': {'Total': 1}},
     'recycling_type': {'Total': 1},
     'ref': {'Total': 10314,
      'isil': {'Total': 3},
      'left': {'Total': 11},
      'nrhp': {'Total': 2},
      'right': {'Total': 9},
      'store_number': {'Total': 2}},
     'reg_name': {'Total': 61},
     'religion': {'Total': 4271},
     'rental': {'Total': 1},
     'research_institution': {'Total': 1},
     'residential': {'Total': 1},
     'residents': {'Total': 1},
     'resource': {'Total': 2},
     'role': {'Total': 1},
     'roof': {'height': {'Total': 4},
      'shape': {'Total': 11},
      'slope': {'direction': {'Total': 4}}},
     'route': {'Total': 121},
     'route_ref': {'Total': 27},
     'ruins': {'Total': 3},
     'sale': {'Total': 2},
     'school': {'Total': 6, 'for': {'Total': 1}},
     'seasonal': {'Total': 2},
     'segregated': {'Total': 64},
     'self_service': {'Total': 1},
     'service': {'Total': 44304,
      'bicycle': {'rental': {'Total': 2},
       'repair': {'Total': 3},
       'retail': {'Total': 3},
       'second_hand': {'Total': 1}}},
     'shelter': {'Total': 59},
     'shelter_type': {'Total': 12},
     'ship': {'Total': 23, 'type': {'Total': 1}},
     'shop': {'Total': 1753},
     'short_name': {'Total': 17},
     'shower': {'Total': 1},
     'sidewalk': {'Total': 2107},
     'ski': {'Total': 46},
     'smoking': {'Total': 28},
     'snowmobile': {'Total': 1},
     'social_facility': {'Total': 6, 'for': {'Total': 1}},
     'soial_facility': {'for': {'Total': 1}},
     'solar': {'Total': 1},
     'source': {'Total': 73724,
      'access': {'Total': 5},
      'amenity': {'Total': 1},
      'deep_draft': {'Total': 23},
      'hgv': {'national_network': {'Total': 67}},
      'name': {'Total': 288},
      'noname': {'Total': 3},
      'outline': {'Total': 1},
      'pkey': {'Total': 1},
      'proposed': {'Total': 5},
      'start_date': {'Total': 12},
      'website': {'Total': 2}},
     'speed': {'Total': 2},
     'sport': {'Total': 11154},
     'sprays': {'Total': 1},
     'stars': {'Total': 1},
     'start_date': {'Total': 30},
     'state': {'Total': 2},
     'state_abbreviation': {'Total': 1},
     'stop': {'Total': 2},
     'stop_id': {'Total': 20},
     'storage': {'Total': 384},
     'subway': {'Total': 262},
     'supervised': {'Total': 6},
     'support': {'Total': 3},
     'surface': {'Total': 1767},
     'surveillance': {'Total': 15},
     'takeaway': {'Total': 16},
     'tank': {'type': {'Total': 384}},
     'target': {'Total': 1},
     'tiger': {'cfcc': {'Total': 91136},
      'county': {'Total': 91681},
      'mtfcc': {'Total': 271},
      'name_base': {'Total': 84976},
      'name_base_1': {'Total': 8792},
      'name_base_2': {'Total': 1093},
      'name_base_3': {'Total': 244},
      'name_base_4': {'Total': 31},
      'name_direction_prefix': {'Total': 22534},
      'name_direction_prefix_1': {'Total': 3785},
      'name_direction_prefix_2': {'Total': 364},
      'name_direction_prefix_3': {'Total': 125},
      'name_direction_prefix_4': {'Total': 18},
      'name_direction_suffix': {'Total': 852},
      'name_direction_suffix_1': {'Total': 161},
      'name_direction_suffix_2': {'Total': 35},
      'name_direction_suffix_3': {'Total': 2},
      'name_type': {'Total': 81302},
      'name_type_1': {'Total': 7481},
      'name_type_2': {'Total': 675},
      'name_type_3': {'Total': 149},
      'name_type_4': {'Total': 24},
      'reviewed': {'Total': 90062},
      'separated': {'Total': 18279},
      'source': {'Total': 23273},
      'tlid': {'Total': 23269},
      'upload': {'Total': 5},
      'upload_uuid': {'Total': 23029},
      'zip_left': {'Total': 70871},
      'zip_left_1': {'Total': 3499},
      'zip_left_2': {'Total': 888},
      'zip_left_3': {'Total': 330},
      'zip_left_4': {'Total': 117},
      'zip_right': {'Total': 67878},
      'zip_right_1': {'Total': 1645},
      'zip_right_2': {'Total': 382},
      'zip_right_3': {'Total': 165},
      'zip_right_4': {'Total': 54}},
     'toilets': {'Total': 1},
     'toll': {'Total': 1119},
     'tourism': {'Total': 477},
     'tower': {'Total': 1, 'construction': {'Total': 1}, 'type': {'Total': 17}},
     'tracks': {'Total': 27},
     'tracktype': {'Total': 1508},
     'traffic control': {'Total': 12},
     'traffic_calming': {'Total': 203},
     'trail_visibility': {'Total': 2},
     'train': {'Total': 6},
     'truck': {'Total': 2},
     'tunnel': {'Total': 1710},
     'turn': {'Total': 1, 'lanes': {'Total': 3}},
     'twitter': {'Total': 3},
     'type': {'Total': 162},
     'uic_shuttle_route': {'Total': 33},
     'un': {'Total': 1},
     'underground': {'Total': 1},
     'url': {'Total': 40},
     'usage': {'Total': 6},
     'vacant': {'Total': 11},
     'vehicle': {'Total': 17},
     'vending': {'Total': 3},
     'voltage': {'Total': 2435},
     'voltage-high': {'Total': 71},
     'voltage-low': {'Total': 25},
     'wall': {'Total': 4},
     'water': {'Total': 185},
     'waterway': {'Total': 3629},
     'website': {'Total': 705},
     'wetap': {'bottle': {'Total': 1},
      'credit': {'Total': 14},
      'photo': {'Total': 10},
      'status': {'Total': 28},
      'statusnote': {'Total': 1}},
     'wetland': {'Total': 13},
     'wheelchair': {'Total': 436, 'description': {'Total': 1}},
     'wholesale': {'Total': 1},
     'width': {'Total': 14},
     'wifi': {'Total': 41},
     'wikipedia': {'Total': 161, 'en': {'Total': 7}},
     'wood': {'Total': 1},
     'wpt_description': {'Total': 17},
     'wpt_symbol': {'Total': 18},
     'zoo': {'Total': 1}}



### 替换缩写变成标准单词
addr:street记录了街道名称，其中出现了各类有个人色彩的缩写，因此通过先输出一次后得出所有addr:street名称结果，并针对结果进行整理后更新，将所有收集到的缩写更新为标准词组


```python
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
```

    {'104': {'North Sherman Avenue #104'},
     '1220': {'8 S Michigan Ave Suite 1220'},
     '129': {'North Milwaukee Avenue 129'},
     '14': {'Route 14'},
     '20': {'US 20'},
     '231': {'East US 231'},
     '30': {'US 30'},
     '34': {'West Route 34', 'US 34'},
     '38': {'Route 38'},
     '47': {'HWY 47'},
     '53': {'Route 53'},
     '59': {'HWY 59',
            'Route 59',
            'Route IL 59',
            'S HWY 59',
            'S Rte 59',
            'South Route 59'},
     '60008': {'60008'},
     '60435': {'1050 Essington Rd. Joliet, IL 60435'},
     '60463': {'60463'},
     '60546': {'60546'},
     '64': {'Route 64'},
     '83': {'South Route 83'},
     'AV': {'South Harding AV'},
     'AVE': {'S EWING AVE'},
     'Access': {'North Breakwater Access'},
     'Armitage': {'W Armitage'},
     'Ashland': {'South Ashland'},
     'Ave': {'Belmont Ave',
             'Brook Forest Ave',
             'Central Ave',
             'Cicero Ave',
             'Dundee Ave',
             'E Park Ave',
             'East 79th Ave',
             'East Ogden Ave',
             'Forest Ave',
             'Jefferson Ave',
             'Lake Ave',
             'Larkin Ave',
             'Maple Ave',
             'Milwaukee Ave',
             'N California Ave',
             'N Greenview Ave',
             'N Hoyne Ave',
             'N Lincoln Ave',
             'N Milwaukee Ave',
             'N Southport Ave',
             'N Western Ave',
             'N Wheaton Ave',
             'North Clybourn Ave',
             'North Lincoln Ave',
             'Oak Ave',
             'Ogden Ave',
             'S Harlem Ave',
             'Sayre Ave',
             'South Cumberland Ave',
             'South Gary Ave',
             'Thatcher Ave',
             'Torrence Ave',
             'Touhy Ave',
             'W 133rd Ave',
             'W Dempster Ave',
             'W Fullerton Ave',
             'W Highland Ave',
             'W Lawrence Ave',
             'W North Ave',
             'W Park Ave',
             'W Prairie Ave',
             'W Touhy Ave',
             'West Euclid Ave',
             'West Fullerton Ave',
             'West Maple Ave',
             'West North Ave',
             'Wilmette Ave'},
     'Ave.': {'Brookfield Ave.',
              'Burlington Ave.',
              'Calumet Ave.',
              'Grand Ave.',
              'Milwaukee Ave.',
              'N Damen Ave.',
              'N. Kilbourn Ave.',
              'N. Oriole Ave.',
              'North Clybourn Ave.',
              'S. Doty Ave.',
              'Touhy Ave.',
              'W Park Ave.',
              'W. Euclid Ave.'},
     'B': {'South Avenue B'},
     'Blvd': {'Franklin Blvd',
              'Grand Blvd',
              'Hansen Blvd',
              'North McCormick Blvd',
              'Oakwood Blvd',
              'Patriot Blvd',
              'Potawatomi Blvd',
              'S Kenilworth Blvd',
              'Sauk Blvd',
              'South Cottage Grove Blvd',
              'Timber Trails Blvd'},
     'Blvd.': {'Indianapolis Blvd.', 'South Naper Blvd.'},
     'Bouleverd': {'South Hyde Park Bouleverd'},
     'Broadway': {'North Broadway', 'West Broadway'},
     'C': {'South Avenue C'},
     'CT': {'East 93rd CT',
            'North Besly CT',
            'North Crilly CT',
            'North Davlin CT',
            'North Fern CT',
            'North Hampden CT',
            'North Hartland CT',
            'North Haussen CT',
            'North Kenton CT',
            'North Lehmann CT',
            'North Maria CT',
            'North Marion CT',
            'North Ritchie CT',
            'North St Johns CT',
            'North St Michaels CT',
            'North Surrey CT',
            'North Waterloo CT',
            'North Willard CT',
            'North Willets CT',
            'North Willetts CT',
            'South Elias CT',
            'South Gilbert CT',
            'South Givins CT',
            'South Grady CT',
            'South Haynes CT',
            'South Melody CT',
            'South Park Shore East CT',
            'South Pitney CT',
            'South Ridgewood CT',
            'South Shelby CT',
            'South Tan CT',
            'South Washington Park CT',
            'West Henry CT',
            'West Julia CT',
            'West Lithuanian Plaza CT',
            'West St Georges CT',
            'West Village CT'},
     'Center': {'Convenience Center',
                'Yorktown Center',
                'Yorktown Shopping Center'},
     'Chicago': {'South Chicago'},
     'Cir': {'Glenbrook Cir', 'Aspen Cir'},
     'Circle': {'Blanchard Circle',
                'Calvin Circle',
                'Knox Circle',
                'Townplace Circle',
                'Woodland Park Circle'},
     'Ct': {'Alpine Ct',
            'Andra Ct',
            'Boulder Ct',
            'Breckenridge Ct',
            'Brittany Ct',
            'Dillon Ct',
            'Durango Ct',
            'Glenbrook Ct',
            'Hennessy Ct',
            'Joan Ct',
            'Kerry Ct',
            'Kilkenny Ct',
            'Leadville Ct',
            'Loveland Ct',
            'Pamela Ct',
            'Park Ct',
            'Pauline Ct',
            'Powder Horn Ct',
            'Telluride Ct',
            'Timber Ct',
            'Timber Trails Ct',
            'Toll View Ct',
            'Towne Ct',
            'Vail Ct',
            'Woodland Park Ct'},
     'Ct.': {'W. Peregrine Ct.'},
     'Ctr.': {'Elk Grove Town Ctr.'},
     'D': {'South Avenue D'},
     'Dr': {'Academic Dr',
            'Alpine Dr',
            'Arrowhead Dr',
            'Augusta Dr',
            'Authority Dr',
            'Boulder Dr',
            'Breckenridge Dr',
            'Brentwood Dr',
            'Briarwood Dr',
            'Charlestown Dr',
            'Copper Mountain Dr',
            'Fox Valley Center Dr',
            'Greenbriar Dr',
            'Gregory M Sears Dr',
            'Industrial Dr',
            'John M Boor Dr',
            'Marketview Dr',
            'Meadows Dr',
            'N Bolingbrook Dr',
            'N Columbus Service Dr',
            'Plaza Dr',
            'Raymond Dr',
            'Regent Dr',
            'Steamboat Dr',
            'Summit Dr',
            'Varsity Dr',
            'Woodridge Dr'},
     'Dr.': {'Auburn Dr.',
             'Corporate Grove Dr.',
             'Montrose Harbor Dr.',
             'W Lakeshore Dr.',
             'W. Peregrine Dr.'},
     'E': {'South Avenue E', 'Danada Square E'},
     'Elston': {'N Elston'},
     'F': {'South Avenue F'},
     'G': {'South Avenue G'},
     'Glenwood': {'N Glenwood'},
     'Grand': {'East Grand'},
     'H': {'South Avenue H'},
     'HWY': {'W Lincoln HWY'},
     'Highway': {'Busse Highway',
                 'East Northwest Highway',
                 'Lincoln Highway',
                 'North Northwest Highway',
                 'Northwest Highway',
                 'South Robert Kingery Highway',
                 'West Northwest Highway'},
     'Hwy': {'N. Northwest Hwy'},
     'Hwy.': {'W. Northwest Hwy.'},
     'J': {'South Avenue J'},
     'Justamere': {'Justamere'},
     'K': {'South Avenue K'},
     'Kedzie': {'N Kedzie', 'Kedzie'},
     'L': {'South Avenue L'},
     'LN': {'North Sauganash LN',
            'West Evelyn LN',
            'West Harrington LN',
            'West High Bridge LN',
            'West Joyce LN',
            'West Memory LN',
            'West University LN'},
     'Ln': {'Brighton Ln',
            'Erica Ln',
            'Evergreen Ln',
            'Hendricks Ln',
            'Leadville Ln',
            'Running Deer Ln',
            'White Feather Ln'},
     'Loomis': {'South Loomis'},
     'M': {'South Avenue M'},
     'Market': {'West Fulton Market', 'West South Water Market'},
     'Milwaukee': {'N Milwaukee'},
     'Montrose': {'West Montrose'},
     'N': {'Michigan Avenue N', 'South Avenue N'},
     'North': {'Gloucester Way North', 'Parkway North'},
     'PKWY': {'North Edens PKWY',
              'North State PKWY',
              'South Calumet PKWY',
              'South Campus PKWY',
              'South Euclid PKWY',
              'South Halsted PKWY',
              'South Indiana PKWY',
              'South Lee PKWY',
              'South Louie PKWY',
              'South Prairie PKWY',
              'South Throop PKWY',
              'South Tom PKWY',
              'South Walden PKWY',
              'South Wong PKWY',
              'South Young PKWY',
              'West Beverly Glen PKWY',
              'West College PKWY',
              'West Congress PKWY',
              'West Diversey PKWY',
              'West Fullerton PKWY',
              'West Normal PKWY',
              'West Winneconna PKWY'},
     'PLZ': {'East 125th PLZ', 'East Carver PLZ'},
     'Park': {'East Groveland Park',
              'East Madison Avenue Park',
              'East Madison Park',
              'East Woodland Park',
              'Ingleside Park',
              'Milburn Park',
              'Rehm Park',
              'South Washington Park',
              'West Midway Park'},
     'Path': {'Shining Moon Path', 'Red Hawk Path'},
     'Paulina': {'N Paulina'},
     'Pkwy': {'Veterans Pkwy', 'W Veterans Pkwy'},
     'Pl': {'Margaret Pl'},
     'Plaza': {'Merchandise Mart Plaza',
               'North Riverside Plaza',
               'South Riverside Plaza',
               'West Merchandise Mart Plaza'},
     'Prospect': {'South Prospect'},
     'Pwy': {'Prairie Stone Pwy'},
     'RD': {'Randall RD'},
     'ROW': {'West Churchill ROW'},
     'Rd': {'Big Timber Rd',
            'Binder Rd',
            'Bloomingdale Rd',
            'Carpenter Rd',
            'Crane Rd',
            'Dara James Rd',
            'Dundee Rd',
            'E Higgins Rd',
            'E State Rd',
            'East Higgins Rd',
            'Freeman Rd',
            'Galligan Rd',
            'Hobson Rd',
            'Justamere Rd',
            'Kirk Rd',
            'Lake Cook Rd',
            'Manheim Rd',
            'Mason Rd',
            'McHenry Rd',
            'Miller Rd',
            'N Rand Rd',
            'N Randal Rd',
            'N Randall Rd',
            'N Weber Rd',
            'N Wood Dale Rd',
            'Nesler Rd',
            'Normantown Rd',
            'North Randall Rd',
            'Pingree Rd',
            'Plainfield Rd',
            'Powers Rd',
            'Pyott Rd',
            'Rand Rd',
            'Randall Rd',
            'Ridge Rd',
            'S LaGrange Rd',
            'S Naperville Rd',
            'S Randall Rd',
            'Schmale Rd',
            'Silver Glen Rd',
            'South Eola Rd',
            'Tower Hill Rd',
            'Trout Farm Rd',
            'Tyrrell Rd',
            'W Romeo Rd',
            'W Schick Rd',
            'Warrenville Rd',
            'Waukegan Rd',
            'Wise Rd'},
     'Rd.': {'Baldwin Rd.',
             'E. Rand Rd.',
             'N. Rand Rd.',
             'S. Arlington Heights Rd.',
             'W. State Rd.'},
     'SD': {'North Humboldt SD'},
     'Shabbona': {'Shabbona'},
     'St': {'159th St',
            'Capital St',
            'Central St',
            'Cross St',
            'Deborah St',
            'Dempster St',
            'Division St',
            'E Chicago St',
            'E Main St',
            'Harbor St',
            'Jackson St',
            'Jean St',
            'Kathleen St',
            'Kildare St',
            'Liberty St',
            'Lillie St',
            'Main St',
            'N Division St',
            'N Ellsworth St',
            'N Franklin St',
            'N Halsted St',
            'N Main St',
            'N Railroad St',
            'N St. Clair St',
            'N State St',
            'N. Clark St',
            'Nequa St',
            'North Hough St',
            'Ohio St',
            'Park St',
            'Pierce St',
            'Railroad St',
            'Raymond St',
            'Rose St',
            'S 1st St',
            'S 5th St',
            'S 8th St',
            'S Fryer St',
            'S Gilbert St',
            'S Lincolnway St',
            'S State St',
            'S Washington St',
            'Short St',
            'Suzanne St',
            'Tipperary St',
            'Towne St',
            'W 111 St',
            'W 183rd St',
            'W Chicago St',
            'W Division St',
            'W Grace St',
            'W Lake St',
            'W Lockport St',
            'W Main St',
            'W Washington St',
            'W. Belden St',
            'Watch St',
            'Webster St',
            'Welch St',
            'West Lake St'},
     'St.': {'E. Illinois St.',
             'East 53rd St.',
             'N. Main St.',
             'W 129th St.',
             'W Eames St.'},
     'Terrace': {'Colfax Terrace',
                 'Harvard Terrace',
                 'Hull Terrace',
                 'North Alta Vista Terrace',
                 'North Eastlake Terrace',
                 'North Edgebrook Terrace',
                 'North Geneva Terrace',
                 'North Parkview Terrace',
                 'North Riversedge Terrace',
                 'North Sandburg Terrace',
                 'North Wesley Terrace',
                 'Ridge Terrace',
                 'South Park Terrace',
                 'West Cahill Terrace',
                 'West California Terrace',
                 'West Castlewood Terrace',
                 'West Gordon Terrace',
                 'West Jonquil Terrace',
                 'West Juneway Terrace',
                 'West Junior Terrace',
                 'West Margate Terrace',
                 'West Westgate Terrace'},
     'Trl': {'Sleeping Bear Trl'},
     'WAY': {'South Boulevard WAY'},
     'WEST': {'North Lincoln Park  WEST'},
     'Walk': {'North River Walk'},
     'Way': {'Woodridge Way'},
     'West': {'Ginny Lane West',
              'Gloucester Way West',
              'North Lincoln Park  West',
              'North Lincoln Park West',
              'Park Avenue West',
              'South Doty Avenue West'},
     'blvd': {'Sauk blvd'},
     'pkwy': {'Center pkwy'},
     'rd': {'S. Rohlwing rd'},
     'road': {'west cuba road and rand road', 'E Algonquin road'},
     'st': {'E main st'}}
    ----------------------------------------------------------
    


```python
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
```

    'N. Northwest Highway'
    'South Avenue D'
    'Elk Grove Town court'
    'Touhy Avenue'
    'N Damen Avenue'
    'Brookfield Avenue'
    'Calumet Avenue'
    'W. Euclid Avenue'
    'N. Oriole Avenue'
    'Burlington Avenue'
    'Milwaukee Avenue'
    'S. Doty Avenue'
    'N. Kilbourn Avenue'
    'North Clybourn Avenue'
    'Grand Avenue'
    'W Park Avenue'
    'South Avenue M'
    'S. Rohlwing Road'
    'US 30'
    'Center PARKWAY'
    'Merchandise Mart Plaza'
    'West Merchandise Mart Plaza'
    'North Riverside Plaza'
    'South Riverside Plaza'
    'S EWING AVE'
    'Gloucester Way North'
    'Parkway North'
    'South Chicago'
    'Raymond drive'
    'Boulder drive'
    'Arrowhead drive'
    'Varsity drive'
    'Gregory M Sears drive'
    'Augusta drive'
    'Fox Valley Center drive'
    'Woodridge drive'
    'Summit drive'
    'Academic drive'
    'Meadows drive'
    'Steamboat drive'
    'Breckenridge drive'
    'Greenbriar drive'
    'John M Boor drive'
    'Briarwood drive'
    'Plaza drive'
    'Marketview drive'
    'Industrial drive'
    'Charlestown drive'
    'Regent drive'
    'Brentwood drive'
    'Copper Mountain drive'
    'N Columbus Service drive'
    'Alpine drive'
    'Authority drive'
    'N Bolingbrook drive'
    'Yorktown Center'
    'Yorktown Shopping Center'
    'Convenience Center'
    'East 125th Plaza'
    'East Carver Plaza'
    'N Glenwood'
    'N Paulina'
    'East Grand'
    'W Lincoln Highway'
    'South Route 59'
    'S HWY 59'
    'Route IL 59'
    'S Rte 59'
    'HWY 59'
    'Route 59'
    'N Elston'
    'South Avenue C'
    'South Avenue K'
    'South Avenue H'
    'West Montrose'
    'W. Northwest Highway'
    'Route 53'
    'West Harrington lane'
    'West High Bridge lane'
    'West Evelyn lane'
    'North Sauganash lane'
    'West Memory lane'
    'West University lane'
    'West Joyce lane'
    '8 S Michigan Ave Suite 1220'
    'South Avenue B'
    'White Feather lane'
    'Erica lane'
    'Running Deer lane'
    'Brighton lane'
    'Evergreen lane'
    'Hendricks lane'
    'Leadville lane'
    'North Humboldt SD'
    'Route 64'
    'North Milwaukee Avenue 129'
    'South Avenue F'
    'W. Peregrine court'
    'HWY 47'
    'Margaret Pl'
    'South Avenue L'
    'South Ashland'
    'South Avenue E'
    'Danada Square E'
    'Shabbona'
    'East US 231'
    'Auburn drive'
    'Montrose Harbor drive'
    'W. Peregrine drive'
    'W Lakeshore drive'
    'Corporate Grove drive'
    'Sauk boulevard'
    'South Route 83'
    'West Churchill ROW'
    'Indianapolis boulevard'
    'South Naper boulevard'
    'Woodridge Way'
    'N Milwaukee'
    'East Madison Park'
    'East Groveland Park'
    'East Madison Avenue Park'
    'Milburn Park'
    'East Woodland Park'
    'Rehm Park'
    'West Midway Park'
    'South Washington Park'
    'Ingleside Park'
    'South Hyde Park Bouleverd'
    'Ridge Terrace'
    'North Alta Vista Terrace'
    'West Castlewood Terrace'
    'West Junior Terrace'
    'West Westgate Terrace'
    'North Riversedge Terrace'
    'North Wesley Terrace'
    'North Geneva Terrace'
    'Hull Terrace'
    'North Parkview Terrace'
    'North Eastlake Terrace'
    'West Margate Terrace'
    'West Jonquil Terrace'
    'North Edgebrook Terrace'
    'South Park Terrace'
    'Harvard Terrace'
    'West California Terrace'
    'West Juneway Terrace'
    'West Cahill Terrace'
    'North Sandburg Terrace'
    'West Gordon Terrace'
    'Colfax Terrace'
    'US 20'
    'N Kedzie'
    'Kedzie'
    'Prairie Stone Pwy'
    'South Avenue J'
    'North Lincoln Park  West'
    'Park Avenue West'
    'South Doty Avenue West'
    'Ginny Lane West'
    'North Lincoln Park West'
    'Gloucester Way West'
    'west cuba road and rand road'
    'E Algonquin road'
    'Michigan Avenue N'
    'South Avenue N'
    'Veterans PARKWAY'
    'W Veterans PARKWAY'
    'Maple Avenue'
    'East Ogden Avenue'
    'Forest Avenue'
    'South Cumberland Avenue'
    'W Prairie Avenue'
    'S Harlem Avenue'
    'W North Avenue'
    'Lake Avenue'
    'N Western Avenue'
    'Belmont Avenue'
    'N Hoyne Avenue'
    'Ogden Avenue'
    'N California Avenue'
    'W Park Avenue'
    'W 133rd Avenue'
    'W Touhy Avenue'
    'Brook Forest Avenue'
    'North Lincoln Avenue'
    'Thatcher Avenue'
    'N Lincoln Avenue'
    'West Fullerton Avenue'
    'W Fullerton Avenue'
    'West Euclid Avenue'
    'Central Avenue'
    'N Southport Avenue'
    'N Wheaton Avenue'
    'W Highland Avenue'
    'Sayre Avenue'
    'W Dempster Avenue'
    'Touhy Avenue'
    'East 79th Avenue'
    'Torrence Avenue'
    'Wilmette Avenue'
    'North Clybourn Avenue'
    'W Lawrence Avenue'
    'Milwaukee Avenue'
    'N Greenview Avenue'
    'Dundee Avenue'
    'West Maple Avenue'
    'Larkin Avenue'
    'South Gary Avenue'
    'N Milwaukee Avenue'
    'E Park Avenue'
    'Oak Avenue'
    'Jefferson Avenue'
    'Cicero Avenue'
    'West North Avenue'
    'S. Arlington Heights Road'
    'E. Rand Road'
    'W. State Road'
    'Baldwin Road'
    'N. Rand Road'
    'Park Street'
    'Lillie Street'
    'Capital Street'
    'W Division Street'
    'N Ellsworth Street'
    'Jean Street'
    'Short Street'
    'Cross Street'
    'Deborah Street'
    'Kildare Street'
    'W Main Street'
    'S Gilbert Street'
    'Railroad Street'
    'Webster Street'
    'S 1st Street'
    'W Lake Street'
    'Harbor Street'
    'N Halsted Street'
    'Central Street'
    'Ohio Street'
    'Kathleen Street'
    'W Grace Street'
    'W. Belden Street'
    'S 5th Street'
    'Raymond Street'
    'Towne Street'
    'S Washington Street'
    '159th Street'
    'Suzanne Street'
    'N State Street'
    'Liberty Street'
    'Welch Street'
    'W 111 Street'
    'S Fryer Street'
    'S State Street'
    'Jackson Street'
    'Rose Street'
    'W Chicago Street'
    'Main Street'
    'S Lincolnway Street'
    'E Chicago Street'
    'W Washington Street'
    'N Division Street'
    'Dempster Street'
    'North Hough Street'
    'West Lake Street'
    'N Railroad Street'
    'S 8th Street'
    'N Main Street'
    'W Lockport Street'
    'N Franklin Street'
    'N. Clark Street'
    'Tipperary Street'
    'Nequa Street'
    'Watch Street'
    'Pierce Street'
    'E Main Street'
    'N St. Clair Street'
    'W 183rd Street'
    'Division Street'
    'West Fulton Market'
    'West South Water Market'
    '60008'
    'South Prospect'
    'Shining Moon Path'
    'Red Hawk Path'
    'W Eames Street'
    'E. Illinois Street'
    'East 53rd Street'
    'W 129th Street'
    'N. Main Street'
    'Justamere'
    'Townplace Circle'
    'Blanchard Circle'
    'Calvin Circle'
    'Woodland Park Circle'
    'Knox Circle'
    'South Loomis'
    '1050 Essington Rd. Joliet, IL 60435'
    'North Breakwater Access'
    'Randall RD'
    'North Lincoln Park  WEST'
    'Ridge Road'
    'Silver Glen Road'
    'Manheim Road'
    'N Weber Road'
    'Crane Road'
    'Kirk Road'
    'W Schick Road'
    'Wise Road'
    'Binder Road'
    'S LaGrange Road'
    'Freeman Road'
    'Hobson Road'
    'Dundee Road'
    'Justamere Road'
    'N Wood Dale Road'
    'East Higgins Road'
    'E Higgins Road'
    'Pyott Road'
    'S Naperville Road'
    'Bloomingdale Road'
    'Mason Road'
    'Rand Road'
    'N Rand Road'
    'McHenry Road'
    'E State Road'
    'Carpenter Road'
    'W Romeo Road'
    'Plainfield Road'
    'Miller Road'
    'Trout Farm Road'
    'S Randall Road'
    'Waukegan Road'
    'Normantown Road'
    'North Randall Road'
    'Big Timber Road'
    'N Randal Road'
    'Pingree Road'
    'South Eola Road'
    'Warrenville Road'
    'Dara James Road'
    'Lake Cook Road'
    'N Randall Road'
    'Nesler Road'
    'Galligan Road'
    'Randall Road'
    'Tyrrell Road'
    'Tower Hill Road'
    'Powers Road'
    'Schmale Road'
    'Sleeping Bear Trl'
    'South Avenue G'
    'North River Walk'
    'Telluride court'
    'Glenbrook court'
    'Park court'
    'Leadville court'
    'Hennessy court'
    'Alpine court'
    'Powder Horn court'
    'Towne court'
    'Breckenridge court'
    'Brittany court'
    'Boulder court'
    'Dillon court'
    'Kilkenny court'
    'Vail court'
    'Andra court'
    'Woodland Park court'
    'Pauline court'
    'Toll View court'
    'Durango court'
    'Joan court'
    'Timber Trails court'
    'Pamela court'
    'Loveland court'
    'Kerry court'
    'Timber court'
    'North Besly court'
    'North Kenton court'
    'South Tan court'
    'South Washington Park court'
    'North Crilly court'
    'South Ridgewood court'
    'North Willetts court'
    'North Hartland court'
    'South Elias court'
    'North Marion court'
    'South Haynes court'
    'West Lithuanian Plaza court'
    'North Haussen court'
    'North St Johns court'
    'South Grady court'
    'West St Georges court'
    'West Julia court'
    'South Gilbert court'
    'South Shelby court'
    'North Fern court'
    'South Park Shore East court'
    'West Henry court'
    'North Lehmann court'
    'West Village court'
    'North Ritchie court'
    'South Pitney court'
    'North Willets court'
    'North Hampden court'
    'North Surrey court'
    'North Willard court'
    'South Givins court'
    'North Waterloo court'
    'North Davlin court'
    'South Melody court'
    'North St Michaels court'
    'East 93rd court'
    'North Maria court'
    '60463'
    'Glenbrook circle'
    'Aspen circle'
    'South Robert Kingery Highway'
    'West Northwest Highway'
    'Lincoln Highway'
    'East Northwest Highway'
    'Busse Highway'
    'North Northwest Highway'
    'Northwest Highway'
    'West Fullerton PARKWAY'
    'West Beverly Glen PARKWAY'
    'West Winneconna PARKWAY'
    'South Euclid PARKWAY'
    'West Diversey PARKWAY'
    'South Calumet PARKWAY'
    'South Wong PARKWAY'
    'South Young PARKWAY'
    'West Normal PARKWAY'
    'West Congress PARKWAY'
    'South Halsted PARKWAY'
    'South Indiana PARKWAY'
    'South Walden PARKWAY'
    'North Edens PARKWAY'
    'South Louie PARKWAY'
    'South Lee PARKWAY'
    'South Tom PARKWAY'
    'North State PARKWAY'
    'South Throop PARKWAY'
    'South Campus PARKWAY'
    'South Prairie PARKWAY'
    'West College PARKWAY'
    'W Armitage'
    'North Broadway'
    'West Broadway'
    'E main Street'
    'North Sherman Avenue #104'
    '60546'
    'Route 38'
    'South Harding AV'
    'Patriot boulevard'
    'North McCormick boulevard'
    'Franklin boulevard'
    'Oakwood boulevard'
    'Hansen boulevard'
    'S Kenilworth boulevard'
    'Sauk boulevard'
    'Grand boulevard'
    'South Cottage Grove boulevard'
    'Timber Trails boulevard'
    'Potawatomi boulevard'
    'Route 14'
    'South Boulevard WAY'
    'West Route 34'
    'US 34'
    

#### 将编辑替换以后的数据写入json文件并写入mongodb


```python
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
    
```

    all element  24043776
    


```python
import gc
gc.collect()
```




    4356




```python
import pdb
import string 
import pprint
from pymongo import MongoClient
import os
import re
```

## 基本数据概览

数据源采用芝加哥城市数据进行分析，参考文件要求进行如下选择。

1、数据文件大小 
数据文件大小在1.8GB
采用大型文本数据原因是为了检查使用python解析xml文件的功能理解，在数据准备及插入数据库过程中，基本流程内保证内存占用<800M

2、本次数据清洗后入库有效数据9869440条。其中relation类型数据2484条，way类型数据1087021条，node类型数据7879935条。




```python

    
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
```

    'chicago.osm file size : 1887427618'
    'all rows 8769440'
    'all tag types '
    {'_id': 'relation', 'count': 2484}
    {'_id': 'way', 'count': 1087021}
    {'_id': 'node', 'count': 7679935}
    

## 数据统计维度分析


### 根据用户提交情况统计，展示哪些用户贡献度最高。按照贡献从多到少提供


```python

print("---------------------------------根据ndinfo.user统计设施次数----------------------------------------------")    
rs= db.aggregate([{
            "$group":{"_id":"$ndinfo.user", "count":{"$sum":1}}},{"$sort":{"count":-1}}
    ])

for doc in rs:
    pprint.pprint(doc)
    
```

    ---------------------------------根据ndinfo.user统计设施次数----------------------------------------------
    {'_id': 'chicago-buildings', 'count': 5724631}
    {'_id': 'Umbugbene', 'count': 1031161}
    {'_id': 'alexrudd (NHD)', 'count': 269298}
    {'_id': 'woodpeck_fixbot', 'count': 261575}
    {'_id': 'TIGERcnl', 'count': 119770}
    {'_id': 'patester24', 'count': 115641}
    {'_id': 'mpinnau', 'count': 107196}
    {'_id': 'bbmiller', 'count': 85927}
    {'_id': 'NE2', 'count': 82519}
    {'_id': 'Sundance', 'count': 78046}
    {'_id': 'Kristian M Zoerhoff', 'count': 67888}
    {'_id': 'Tom Layo', 'count': 63017}
    {'_id': 'nickvet419', 'count': 58955}
    {'_id': 'Deo Favente', 'count': 50629}
    {'_id': 'bot-mode', 'count': 48483}
    {'_id': 'iandees', 'count': 42925}
    {'_id': 'alexrudd', 'count': 34574}
    {'_id': 'Rub21', 'count': 33913}
    {'_id': 'WernerP', 'count': 31840}
    {'_id': 'mappy123', 'count': 24876}
    {'_id': 'Eliyak', 'count': 18284}
    {'_id': '42429', 'count': 15487}
    {'_id': 'boeleman81', 'count': 14555}
    {'_id': 'Ru55Ht', 'count': 12731}
    {'_id': 'maxerickson', 'count': 12641}
    {'_id': 'Forest Gregg', 'count': 12574}
    {'_id': 'Steven Vance', 'count': 11968}
    {'_id': 'andrewpmk', 'count': 11660}
    {'_id': 'Chris Lawrence', 'count': 11064}
    {'_id': 'jimjoe45', 'count': 10451}
    {'_id': 'mkeller3', 'count': 9159}
    {'_id': 'JWAddison', 'count': 8901}
    {'_id': 'KristenK', 'count': 8552}
    {'_id': 'fumo7887', 'count': 8333}
    {'_id': 'BeatlesZeppelinRush', 'count': 7667}
    {'_id': 'jbk123', 'count': 7593}
    {'_id': 'GXCEB0TOSM', 'count': 7131}
    {'_id': 'GeneBase', 'count': 6499}
    {'_id': 'be9110', 'count': 6496}
    {'_id': 'AndrewSnow', 'count': 6163}
    {'_id': 'MikeNBulk', 'count': 6079}
    {'_id': 'linuxUser16', 'count': 5494}
    {'_id': 'dmcbride98', 'count': 5121}
    {'_id': 'MikeN', 'count': 5098}
    {'_id': 'lbk100', 'count': 4759}
    {'_id': 'zephyr', 'count': 4755}
    {'_id': 'Gone', 'count': 4587}
    {'_id': 'sargas', 'count': 4437}
    {'_id': 'richlv', 'count': 4289}
    {'_id': 'DaveHansenTiger', 'count': 3961}
    {'_id': 'Cam4rd98', 'count': 3886}
    {'_id': 'Gary Cox', 'count': 3437}
    {'_id': 'Geogast', 'count': 3373}
    {'_id': 'dcs', 'count': 3352}
    {'_id': 'Brian Clark', 'count': 3326}
    {'_id': 'California Bear', 'count': 3018}
    {'_id': 'NHD edits', 'count': 2994}
    {'_id': 'StellanL', 'count': 2934}
    {'_id': 'Ivan Komarov', 'count': 2880}
    {'_id': 'Blue Nacho', 'count': 2848}
    {'_id': 'Mythdraug', 'count': 2799}
    {'_id': 'C_H', 'count': 2758}
    {'_id': 'bruck4', 'count': 2721}
    {'_id': 'TMLutas', 'count': 2690}
    {'_id': 'mattbierner', 'count': 2665}
    {'_id': 'rcpax', 'count': 2653}
    {'_id': 'BenUWebmaster', 'count': 2607}
    {'_id': 'Lart', 'count': 2573}
    {'_id': 'Brian@Brea', 'count': 2523}
    {'_id': 'gxceb0t', 'count': 2440}
    {'_id': 'Matthew Truch', 'count': 2438}
    {'_id': 'blahedo', 'count': 2124}
    {'_id': 'Rusty388', 'count': 2043}
    {'_id': 'Mirro', 'count': 2042}
    {'_id': 'fredr', 'count': 1870}
    {'_id': 'ocotillo', 'count': 1863}
    {'_id': 'Apoxol', 'count': 1760}
    {'_id': 'Czech', 'count': 1755}
    {'_id': 'eric22', 'count': 1744}
    {'_id': 'Jim Grisham', 'count': 1714}
    {'_id': 'RalfZ', 'count': 1651}
    {'_id': 'raykendo', 'count': 1648}
    {'_id': 'rolandg', 'count': 1616}
    {'_id': 'D!zzy', 'count': 1581}
    {'_id': 'ksturm2', 'count': 1576}
    {'_id': 'MGH', 'count': 1525}
    {'_id': 'chris983', 'count': 1476}
    {'_id': 'Jim Mauck', 'count': 1441}
    {'_id': 'VE6SRV', 'count': 1440}
    {'_id': 'SmallR2002', 'count': 1384}
    {'_id': 'Derick Rethans', 'count': 1341}
    {'_id': 'newscientist', 'count': 1321}
    {'_id': 'OSMF Redaction Account', 'count': 1261}
    {'_id': 'li3n3', 'count': 1238}
    {'_id': 'BobM', 'count': 1187}
    {'_id': 'RetiredInNH', 'count': 1178}
    {'_id': 'Phil D Basket', 'count': 1170}
    {'_id': 'debutterfly', 'count': 1160}
    {'_id': 'PhQ', 'count': 1153}
    {'_id': 'kollokollo', 'count': 1132}
    {'_id': 'Dylan Semler', 'count': 1123}
    {'_id': 'elektrikshoos', 'count': 1103}
    {'_id': 'Scott Usher', 'count': 1087}
    {'_id': 'g246020', 'count': 1050}
    {'_id': 'nwscfox', 'count': 1026}
    {'_id': 'bobws', 'count': 938}
    {'_id': 'jvg312', 'count': 914}
    {'_id': 'fredjunod', 'count': 909}
    {'_id': 'robgeb', 'count': 906}
    {'_id': 'Jeremy', 'count': 891}
    {'_id': 'OSchlüter', 'count': 872}
    {'_id': 'vkungys', 'count': 854}
    {'_id': 'DoubleA', 'count': 835}
    {'_id': 'Sarutobi', 'count': 804}
    {'_id': 'Cheesehead Dave', 'count': 782}
    {'_id': 'crex', 'count': 746}
    {'_id': 'PeterIto', 'count': 719}
    {'_id': 'amillar', 'count': 712}
    {'_id': 'phobie', 'count': 711}
    {'_id': 'encleadus', 'count': 703}
    {'_id': 'cluening', 'count': 693}
    {'_id': 'JaapK', 'count': 685}
    {'_id': 'CHAINJOJ', 'count': 666}
    {'_id': 'DGlow', 'count': 638}
    {'_id': 'matthieun', 'count': 635}
    {'_id': 'geostone', 'count': 632}
    {'_id': 'davidearl', 'count': 622}
    {'_id': 'RoadGeek_MD99', 'count': 599}
    {'_id': 'asdf1234', 'count': 588}
    {'_id': 'Phil Scherer', 'count': 585}
    {'_id': 'Andrew Fish', 'count': 574}
    {'_id': 'homeslice60148', 'count': 573}
    {'_id': 'smlyons77', 'count': 572}
    {'_id': 'cdelacruz', 'count': 569}
    {'_id': 'nerfer', 'count': 553}
    {'_id': 'TorhamZed', 'count': 549}
    {'_id': 'alexz', 'count': 526}
    {'_id': 'becw', 'count': 523}
    {'_id': 'dunduk', 'count': 517}
    {'_id': 'bitslab-diaz', 'count': 508}
    {'_id': 'BrianKiwi', 'count': 500}
    {'_id': 'ChrisZontine', 'count': 499}
    {'_id': 'hogrod', 'count': 489}
    {'_id': 'Davio', 'count': 477}
    {'_id': '!i!', 'count': 475}
    {'_id': 'dcat', 'count': 461}
    {'_id': 'bitslab', 'count': 460}
    {'_id': 'Dennis McClendon', 'count': 445}
    {'_id': 'fitzsimons', 'count': 437}
    {'_id': 'MacDude72', 'count': 428}
    {'_id': 'Mark Gray', 'count': 427}
    {'_id': 'mvexel', 'count': 425}
    {'_id': 'wotaskd', 'count': 424}
    {'_id': 'stucki1', 'count': 420}
    {'_id': 'Voyeur', 'count': 419}
    {'_id': 'dchiles', 'count': 417}
    {'_id': 'randomjunk', 'count': 415}
    {'_id': 'Squirrel1982', 'count': 413}
    {'_id': 'Milliams', 'count': 407}
    {'_id': 'cassini83', 'count': 406}
    {'_id': 'Mattslomka', 'count': 395}
    {'_id': 'HolgerJeromin', 'count': 384}
    {'_id': 'neuhausr', 'count': 379}
    {'_id': 'iarspider', 'count': 374}
    {'_id': 'nicberry', 'count': 368}
    {'_id': 'FrViPofm', 'count': 364}
    {'_id': 'Minh Nguyen', 'count': 364}
    {'_id': 'da_gibb', 'count': 359}
    {'_id': 'DennisL', 'count': 354}
    {'_id': 'jt7724', 'count': 349}
    {'_id': 'safado', 'count': 342}
    {'_id': 'PHerison', 'count': 341}
    {'_id': 'FTA', 'count': 336}
    {'_id': 'Toolman_Johnny', 'count': 333}
    {'_id': 'Ronan L', 'count': 331}
    {'_id': 'tachoknight', 'count': 320}
    {'_id': 'dweg', 'count': 319}
    {'_id': 'Cerritus', 'count': 313}
    {'_id': 'Maskulinum', 'count': 301}
    {'_id': 'oldtopos', 'count': 295}
    {'_id': 'nusense', 'count': 295}
    {'_id': 'aphedox', 'count': 294}
    {'_id': 'eMerzh', 'count': 290}
    {'_id': 'jpflasch', 'count': 290}
    {'_id': 'NE3', 'count': 287}
    {'_id': 'Spacer212', 'count': 284}
    {'_id': 'Paul Johnson', 'count': 283}
    {'_id': 'T_9er', 'count': 279}
    {'_id': 'hobbesvsboyle', 'count': 279}
    {'_id': 'msdess', 'count': 278}
    {'_id': 'Moovit Team', 'count': 278}
    {'_id': 'dwilkins', 'count': 271}
    {'_id': 'mabrew', 'count': 257}
    {'_id': 'mbuege', 'count': 255}
    {'_id': 'uboot', 'count': 254}
    {'_id': 'Zol87', 'count': 253}
    {'_id': 'ewedistrict', 'count': 253}
    {'_id': 'mspyker', 'count': 251}
    {'_id': 'Aaron Lidman', 'count': 250}
    {'_id': 'botdidier2020', 'count': 240}
    {'_id': 'irasesu', 'count': 239}
    {'_id': 'kay_D', 'count': 225}
    {'_id': 'Jano John Akim Franke', 'count': 218}
    {'_id': 'mgoe', 'count': 216}
    {'_id': 'zehpunktbarron', 'count': 213}
    {'_id': 'lgoughenour', 'count': 209}
    {'_id': 'oba510', 'count': 204}
    {'_id': 'trailuser79', 'count': 202}
    {'_id': 'DJM', 'count': 201}
    {'_id': 'Eric Fischer', 'count': 198}
    {'_id': 'dirkmunson', 'count': 197}
    {'_id': 'mmlange', 'count': 195}
    {'_id': 'xybot', 'count': 194}
    {'_id': 'jotzt', 'count': 194}
    {'_id': 'j22fung', 'count': 192}
    {'_id': 'rennsix', 'count': 191}
    {'_id': 'VMPhil', 'count': 191}
    {'_id': 'jerjozwik', 'count': 189}
    {'_id': 'mpbretl', 'count': 184}
    {'_id': 'mabapla', 'count': 183}
    {'_id': 'Kevin Garcia', 'count': 183}
    {'_id': 'mkinoshita', 'count': 181}
    {'_id': 'LockportDan', 'count': 176}
    {'_id': 'thylacine222', 'count': 167}
    {'_id': 'erwin6330', 'count': 166}
    {'_id': 'kr4z33', 'count': 164}
    {'_id': 'escada', 'count': 163}
    {'_id': 'Fox61', 'count': 162}
    {'_id': 'Peter-DG', 'count': 161}
    {'_id': 'Detcin0', 'count': 161}
    {'_id': 'mdk', 'count': 161}
    {'_id': 'yotann', 'count': 155}
    {'_id': 'richard worl', 'count': 151}
    {'_id': 'aerosuch', 'count': 148}
    {'_id': 'Taroc', 'count': 148}
    {'_id': 'cparker333', 'count': 148}
    {'_id': 'jaut', 'count': 146}
    {'_id': 'gormur', 'count': 146}
    {'_id': 'danhillreports', 'count': 146}
    {'_id': 'motlib', 'count': 145}
    {'_id': 'Vlad', 'count': 145}
    {'_id': 'je091926', 'count': 139}
    {'_id': 'Apo42', 'count': 133}
    {'_id': 'Clorox', 'count': 131}
    {'_id': 'htbeef', 'count': 130}
    {'_id': 'David & Christine Schmitt', 'count': 127}
    {'_id': 'rosskin92', 'count': 127}
    {'_id': 'van Rees', 'count': 126}
    {'_id': 'GreggTownsend', 'count': 122}
    {'_id': 'whomichael', 'count': 122}
    {'_id': 'wvaughan', 'count': 122}
    {'_id': 'cncr04s', 'count': 121}
    {'_id': 'alexrudd2', 'count': 119}
    {'_id': 'RobParal', 'count': 119}
    {'_id': 'ParagonPrime', 'count': 119}
    {'_id': 'cardswin2005', 'count': 116}
    {'_id': 'SimonMercier', 'count': 115}
    {'_id': 'kugelfiesch', 'count': 115}
    {'_id': 'mrizzitiello', 'count': 115}
    {'_id': 'cdavila', 'count': 113}
    {'_id': 'BCNorwich', 'count': 112}
    {'_id': 'nm7s9', 'count': 111}
    {'_id': 'captainjim', 'count': 110}
    {'_id': 'Thomas8122', 'count': 110}
    {'_id': 'Randy Bosma', 'count': 110}
    {'_id': '@linux_loco', 'count': 109}
    {'_id': 'pksohn', 'count': 109}
    {'_id': 'Anthony771', 'count': 108}
    {'_id': 'johnjreiser', 'count': 107}
    {'_id': 'terremoto73', 'count': 106}
    {'_id': 'jdough', 'count': 106}
    {'_id': 'jgrnt', 'count': 105}
    {'_id': 'jumbanho', 'count': 103}
    {'_id': 'markjr', 'count': 103}
    {'_id': 'lesscan', 'count': 100}
    {'_id': 'phil3nix', 'count': 100}
    {'_id': 'Noel Peterson', 'count': 100}
    {'_id': 'ToffeHoff', 'count': 99}
    {'_id': 'jtegen', 'count': 99}
    {'_id': 'maxolasersquad', 'count': 97}
    {'_id': 'DiestelkampAaron', 'count': 93}
    {'_id': 'zero01101', 'count': 90}
    {'_id': 'RascalTwitch', 'count': 90}
    {'_id': 'Johnny Carlsen', 'count': 90}
    {'_id': 'wegerje', 'count': 89}
    {'_id': 'craigloftus', 'count': 89}
    {'_id': 'KptKaos', 'count': 89}
    {'_id': 'ChrisHamby', 'count': 88}
    {'_id': 'Zartbitter', 'count': 88}
    {'_id': 'Zaaj', 'count': 88}
    {'_id': 'salix01', 'count': 87}
    {'_id': 'robert', 'count': 85}
    {'_id': 'egore911', 'count': 84}
    {'_id': 'gpsradler', 'count': 81}
    {'_id': 'Jeffrey Jakucyk', 'count': 81}
    {'_id': 'rab', 'count': 80}
    {'_id': 'Pierre-Alain Dorange', 'count': 80}
    {'_id': 'mypetyak', 'count': 79}
    {'_id': 'Ed_Hedborn', 'count': 79}
    {'_id': 'pbroviak', 'count': 78}
    {'_id': 'AndrewBuck', 'count': 76}
    {'_id': 'tug3', 'count': 75}
    {'_id': 'Cjlanda', 'count': 75}
    {'_id': 'Jason Tinkey', 'count': 73}
    {'_id': 'AaronAsAChimp', 'count': 73}
    {'_id': 'robo1999', 'count': 73}
    {'_id': 'Ropino', 'count': 72}
    {'_id': 'MeltedGeneral', 'count': 71}
    {'_id': 'eleven81', 'count': 71}
    {'_id': 'kavn', 'count': 70}
    {'_id': 'zors1843', 'count': 70}
    {'_id': 'brastins', 'count': 69}
    {'_id': 'mannequinZOD', 'count': 69}
    {'_id': 'wambacher', 'count': 69}
    {'_id': 'Fabi2', 'count': 68}
    {'_id': 'Jeff Johnson', 'count': 68}
    {'_id': 'geowas', 'count': 68}
    {'_id': 'Hundehalter', 'count': 68}
    {'_id': 'myjetsam', 'count': 67}
    {'_id': 'Joe Barbara', 'count': 67}
    {'_id': 'JessAk71', 'count': 67}
    {'_id': 'medavis7695', 'count': 66}
    {'_id': 'tmcw', 'count': 66}
    {'_id': 'Stefan Bethke', 'count': 66}
    {'_id': 'JRW416', 'count': 66}
    {'_id': 'EHE-ELS', 'count': 65}
    {'_id': 'Jacek Broda', 'count': 65}
    {'_id': 'geochrome', 'count': 65}
    {'_id': 'fx99', 'count': 65}
    {'_id': 'Humanist', 'count': 65}
    {'_id': 'DavidF716', 'count': 63}
    {'_id': 'PurpleMustang', 'count': 63}
    {'_id': 'Harry Wood', 'count': 62}
    {'_id': 'torsodog', 'count': 62}
    {'_id': 'tartanabroad', 'count': 61}
    {'_id': 'DMcKerlie', 'count': 61}
    {'_id': 'orienteerer', 'count': 61}
    {'_id': 'Wichita-dweller', 'count': 60}
    {'_id': 'rlconkl', 'count': 60}
    {'_id': 'rvanderveer', 'count': 58}
    {'_id': 'JaggedMind', 'count': 58}
    {'_id': 'n9tog', 'count': 57}
    {'_id': 'rh387', 'count': 57}
    {'_id': 'lawyer26', 'count': 57}
    {'_id': 'BassManNate', 'count': 57}
    {'_id': 'samgranieri', 'count': 57}
    {'_id': 'ansis', 'count': 56}
    {'_id': 'CuriousOne', 'count': 56}
    {'_id': 'Sharkz', 'count': 56}
    {'_id': 'JB82', 'count': 55}
    {'_id': 'winlemski', 'count': 55}
    {'_id': 'wasat', 'count': 54}
    {'_id': 'ToeBee', 'count': 54}
    {'_id': 'GeoTomDe', 'count': 54}
    {'_id': 'WickedSavvy', 'count': 53}
    {'_id': 'White_Rabbit', 'count': 53}
    {'_id': 'Archibum', 'count': 52}
    {'_id': 'paulmach', 'count': 52}
    {'_id': 'brittag', 'count': 52}
    {'_id': 'bsharp53', 'count': 51}
    {'_id': 'mapmeld', 'count': 50}
    {'_id': 'damada80', 'count': 50}
    {'_id': 'KindredCoda', 'count': 49}
    {'_id': 'jjcross', 'count': 49}
    {'_id': 'staticphantom', 'count': 49}
    {'_id': 'Heptazane', 'count': 49}
    {'_id': 'pschonmann', 'count': 48}
    {'_id': 'gcamp', 'count': 47}
    {'_id': 'werner2101', 'count': 47}
    {'_id': 'brwk', 'count': 47}
    {'_id': 'kweejee', 'count': 47}
    {'_id': 'LpAngelRob', 'count': 46}
    {'_id': 'emacsen', 'count': 46}
    {'_id': 'Amaroussi', 'count': 45}
    {'_id': 'BFX', 'count': 45}
    {'_id': 'marchel2', 'count': 45}
    {'_id': 'wheelmap_visitor', 'count': 45}
    {'_id': 'nanders', 'count': 45}
    {'_id': 'Wenya', 'count': 44}
    {'_id': 'mr earth', 'count': 44}
    {'_id': 'jbsnyder', 'count': 44}
    {'_id': 'Samusz', 'count': 43}
    {'_id': 'bstenson', 'count': 42}
    {'_id': 'nakratz', 'count': 42}
    {'_id': 'jengert', 'count': 42}
    {'_id': 'huirad', 'count': 42}
    {'_id': 'Danila U', 'count': 41}
    {'_id': 'ruph', 'count': 40}
    {'_id': 'kbcmdba', 'count': 40}
    {'_id': 'SveLil', 'count': 40}
    {'_id': 'Milo', 'count': 40}
    {'_id': 'hca', 'count': 40}
    {'_id': '25or6to4', 'count': 40}
    {'_id': 'natecook1000', 'count': 40}
    {'_id': 'Jolene Chow', 'count': 39}
    {'_id': 'omascow', 'count': 39}
    {'_id': 'patrick mchaffie', 'count': 39}
    {'_id': 'Your Village Maps', 'count': 39}
    {'_id': 'Andre Engels', 'count': 39}
    {'_id': 'data1', 'count': 39}
    {'_id': 'Michael Schulze', 'count': 38}
    {'_id': 'lmaxon', 'count': 38}
    {'_id': 'golfgeek', 'count': 38}
    {'_id': 'stevo81989', 'count': 37}
    {'_id': 'Jay Decker', 'count': 37}
    {'_id': 'usrbrv8', 'count': 37}
    {'_id': 'jimzat', 'count': 37}
    {'_id': 'daganzdaanda', 'count': 37}
    {'_id': 'R_W_mp', 'count': 37}
    {'_id': 'Aquin', 'count': 36}
    {'_id': 'Tony Pedretti', 'count': 36}
    {'_id': '10richierich', 'count': 36}
    {'_id': 'conwaygroup', 'count': 36}
    {'_id': 'jimheinen', 'count': 35}
    {'_id': 'elbatrop', 'count': 35}
    {'_id': 'Tronikon', 'count': 35}
    {'_id': 'Manu1400', 'count': 35}
    {'_id': 'Cali42', 'count': 34}
    {'_id': 'moonwashed', 'count': 34}
    {'_id': 'logic', 'count': 34}
    {'_id': 'cgu66', 'count': 33}
    {'_id': 'meineke', 'count': 33}
    {'_id': 'Andy Allan', 'count': 33}
    {'_id': 'Serway', 'count': 33}
    {'_id': 'sedot', 'count': 31}
    {'_id': 'adjuva', 'count': 31}
    {'_id': 'h4ck3rm1k3', 'count': 30}
    {'_id': 'Urbano24', 'count': 30}
    {'_id': 'higaki', 'count': 30}
    {'_id': 'randy777', 'count': 30}
    {'_id': 'woodpeck_repair', 'count': 30}
    {'_id': 'BugBuster', 'count': 29}
    {'_id': 'Bryce C Nesbitt', 'count': 29}
    {'_id': 'jnevar', 'count': 29}
    {'_id': 'Joven', 'count': 29}
    {'_id': 'TJOB', 'count': 28}
    {'_id': 'migurski', 'count': 28}
    {'_id': 'thereallswa', 'count': 28}
    {'_id': 'amyb', 'count': 28}
    {'_id': 'Brad86', 'count': 27}
    {'_id': 'lxbarth', 'count': 27}
    {'_id': 'racquetmaster314', 'count': 27}
    {'_id': 'jjasek2', 'count': 26}
    {'_id': 'MrMacs', 'count': 26}
    {'_id': 'growe222', 'count': 26}
    {'_id': 'JonM_Chicago', 'count': 26}
    {'_id': 'henningpohl', 'count': 25}
    {'_id': 'FastEddie', 'count': 25}
    {'_id': 'davebb', 'count': 24}
    {'_id': 'dadinck', 'count': 24}
    {'_id': 'RyanK', 'count': 24}
    {'_id': 'Menkus', 'count': 24}
    {'_id': 'Jeffernan', 'count': 23}
    {'_id': 'n9oum', 'count': 23}
    {'_id': 'Welshie', 'count': 23}
    {'_id': 'Marcussacapuces91', 'count': 23}
    {'_id': 'toconnor2424', 'count': 22}
    {'_id': 'ahaninil', 'count': 22}
    {'_id': 'Garrett Miller', 'count': 22}
    {'_id': 'scai', 'count': 22}
    {'_id': 'OMapper', 'count': 22}
    {'_id': 'andrewsh', 'count': 21}
    {'_id': 'hefee', 'count': 21}
    {'_id': 'grandpachicago', 'count': 21}
    {'_id': 'Zach Elliott', 'count': 21}
    {'_id': 'Alexander Roalter', 'count': 21}
    {'_id': 'raif10', 'count': 21}
    {'_id': 'hfyu', 'count': 20}
    {'_id': 'tharkban', 'count': 20}
    {'_id': 'Peter14', 'count': 20}
    {'_id': 'MichaelCampbell', 'count': 20}
    {'_id': 'tsukasabuddha', 'count': 20}
    {'_id': 'Kelsey Johnson', 'count': 20}
    {'_id': 'Verm', 'count': 20}
    {'_id': 'seav', 'count': 20}
    {'_id': 'uluzman', 'count': 19}
    {'_id': 'arteku', 'count': 19}
    {'_id': 'ivansanchez', 'count': 19}
    {'_id': 'Jonathon Schrader', 'count': 19}
    {'_id': 'rahulsaurav', 'count': 18}
    {'_id': 'sco', 'count': 18}
    {'_id': 'Reclus', 'count': 18}
    {'_id': 'ben_says', 'count': 18}
    {'_id': 'tri11', 'count': 18}
    {'_id': 'down2party', 'count': 18}
    {'_id': 'Alfred Sawatzky', 'count': 18}
    {'_id': 'RussNelson', 'count': 17}
    {'_id': 'Cicerone', 'count': 17}
    {'_id': 'Jksc224', 'count': 17}
    {'_id': 'arborist10', 'count': 17}
    {'_id': 'mapper999', 'count': 17}
    {'_id': 'Glassman', 'count': 17}
    {'_id': 'Dion Dock', 'count': 17}
    {'_id': 'NigelKarp', 'count': 16}
    {'_id': 'skipshearer', 'count': 16}
    {'_id': 'dumroo', 'count': 16}
    {'_id': 'bjornphoto', 'count': 16}
    {'_id': 'brpu', 'count': 16}
    {'_id': 'Juan-Pablo Velez', 'count': 16}
    {'_id': 'Scarlet B', 'count': 16}
    {'_id': 'styckx', 'count': 16}
    {'_id': 'kbuck', 'count': 15}
    {'_id': 'jibtrim', 'count': 15}
    {'_id': 'chdr', 'count': 15}
    {'_id': 'user_5359', 'count': 15}
    {'_id': 'Michael Collins', 'count': 15}
    {'_id': 'Jimmy R', 'count': 15}
    {'_id': 'alangard', 'count': 15}
    {'_id': 'geoMartin', 'count': 14}
    {'_id': 'Mauls', 'count': 14}
    {'_id': 'gcjunge', 'count': 14}
    {'_id': 'hugi', 'count': 14}
    {'_id': 'AE35', 'count': 14}
    {'_id': 'YaZug', 'count': 14}
    {'_id': 'spencerrecneps', 'count': 14}
    {'_id': 'sfw', 'count': 14}
    {'_id': 'Ken Ovryn', 'count': 14}
    {'_id': 'WiFi404', 'count': 14}
    {'_id': 'AKC', 'count': 14}
    {'_id': 'dmgroom', 'count': 14}
    {'_id': 'djo_man', 'count': 14}
    {'_id': 'kerosin', 'count': 14}
    {'_id': '2WYCE', 'count': 14}
    {'_id': 'isabellekh', 'count': 13}
    {'_id': 'Daniel Jeffries', 'count': 13}
    {'_id': 'FIM', 'count': 13}
    {'_id': 'jbnewman', 'count': 13}
    {'_id': 'omems', 'count': 13}
    {'_id': 'Waubonsee Community College', 'count': 13}
    {'_id': 'Justin Haugens', 'count': 13}
    {'_id': 'Hoeth', 'count': 13}
    {'_id': 'abc-12345', 'count': 13}
    {'_id': 'jazzact', 'count': 13}
    {'_id': 'Nerfbait', 'count': 12}
    {'_id': 'user_7659', 'count': 12}
    {'_id': 'Carl Simonson', 'count': 12}
    {'_id': 'melb_guy', 'count': 12}
    {'_id': 'marook', 'count': 12}
    {'_id': 'Orblivion', 'count': 12}
    {'_id': 'Jmallen18', 'count': 12}
    {'_id': 'pvanwylen', 'count': 12}
    {'_id': 'Chaos99', 'count': 12}
    {'_id': 'aude', 'count': 12}
    {'_id': 'NicRoets', 'count': 12}
    {'_id': 'imnichol', 'count': 12}
    {'_id': 'mapserver', 'count': 12}
    {'_id': 'IrishCubsFan', 'count': 12}
    {'_id': 'nkhall', 'count': 12}
    {'_id': 'Mchendriks', 'count': 11}
    {'_id': 'Tim Litwiller', 'count': 11}
    {'_id': 'Dark Asteroid', 'count': 11}
    {'_id': 'Visum', 'count': 11}
    {'_id': 'RichardCorbin', 'count': 11}
    {'_id': 'poppei82', 'count': 11}
    {'_id': 'jim_reese', 'count': 11}
    {'_id': 'Quintesant', 'count': 11}
    {'_id': "Mike O'Donnell", 'count': 11}
    {'_id': 'Hotarunohikari', 'count': 11}
    {'_id': 'Ahlzen', 'count': 11}
    {'_id': 'nicolas17', 'count': 11}
    {'_id': 'kcgarp', 'count': 11}
    {'_id': 'Patrick60657', 'count': 11}
    {'_id': 'zhaostu', 'count': 11}
    {'_id': 'gregjgisp', 'count': 10}
    {'_id': 'mhammett', 'count': 10}
    {'_id': 'mbwall', 'count': 10}
    {'_id': 'brear47', 'count': 10}
    {'_id': 'Josef73', 'count': 10}
    {'_id': 'VinceHradil', 'count': 10}
    {'_id': 'AutumnAR', 'count': 10}
    {'_id': 'Two K', 'count': 10}
    {'_id': 'Walter Schlögl', 'count': 10}
    {'_id': 'PA94', 'count': 10}
    {'_id': 'xeen', 'count': 10}
    {'_id': 'lesko987', 'count': 10}
    {'_id': 'mikelmaron', 'count': 10}
    {'_id': 'Maarten Deen', 'count': 10}
    {'_id': 'storm72', 'count': 10}
    {'_id': 'buurmas', 'count': 10}
    {'_id': 'Math1985', 'count': 10}
    {'_id': 'achims311', 'count': 10}
    {'_id': 'scruss', 'count': 10}
    {'_id': 'girivs', 'count': 9}
    {'_id': 'Ulmon Community', 'count': 9}
    {'_id': 'fredbird67', 'count': 9}
    {'_id': '156281', 'count': 9}
    {'_id': 'SK53', 'count': 9}
    {'_id': 'flamozzle', 'count': 9}
    {'_id': 'dmetech', 'count': 9}
    {'_id': 'nfgusedautoparts', 'count': 9}
    {'_id': 'pauldzy', 'count': 9}
    {'_id': 'hsdgis', 'count': 9}
    {'_id': 'noliver', 'count': 9}
    {'_id': 'John Carlee', 'count': 9}
    {'_id': 'cubistcastle', 'count': 9}
    {'_id': 'ryuex6', 'count': 9}
    {'_id': 'BrianMoloney', 'count': 9}
    {'_id': 'Longbow4u', 'count': 9}
    {'_id': 'sk8tripr', 'count': 9}
    {'_id': 'milicz', 'count': 8}
    {'_id': 'Boeboe', 'count': 8}
    {'_id': 'csmncooper', 'count': 8}
    {'_id': 'Jguy', 'count': 8}
    {'_id': 'jazztunes', 'count': 8}
    {'_id': 'Thyais Meade', 'count': 8}
    {'_id': 'Trex2001', 'count': 8}
    {'_id': 'Andre68', 'count': 8}
    {'_id': 'moosejaw', 'count': 8}
    {'_id': 'lhillberg', 'count': 8}
    {'_id': 'TonyMa', 'count': 8}
    {'_id': 'maximeguillaud', 'count': 8}
    {'_id': 'jaswilli', 'count': 8}
    {'_id': 'Jayen A', 'count': 7}
    {'_id': 'lindsaybayley', 'count': 7}
    {'_id': 'palewire', 'count': 7}
    {'_id': 'mxndrwgrdnr', 'count': 7}
    {'_id': 'Cristhian De la Reza', 'count': 7}
    {'_id': 'Ohr', 'count': 7}
    {'_id': 'sllockard', 'count': 7}
    {'_id': 'ulfl', 'count': 7}
    {'_id': 'cerrigno', 'count': 7}
    {'_id': 'N-Krove', 'count': 7}
    {'_id': 'robrobrob', 'count': 7}
    {'_id': 'Cobaltblue16', 'count': 7}
    {'_id': 'Animebando', 'count': 7}
    {'_id': 'elwarren', 'count': 7}
    {'_id': 'sejohnson', 'count': 7}
    {'_id': 'sanborn', 'count': 7}
    {'_id': 'joedwy', 'count': 7}
    {'_id': 'gundog', 'count': 7}
    {'_id': 'LucyGeog', 'count': 7}
    {'_id': '1248', 'count': 7}
    {'_id': 'Jeff Ollie', 'count': 7}
    {'_id': 'cacrawf', 'count': 7}
    {'_id': 'Scott Lav', 'count': 6}
    {'_id': 'nikoleali', 'count': 6}
    {'_id': 'sjbucaro', 'count': 6}
    {'_id': 'DavidF', 'count': 6}
    {'_id': 'aroach', 'count': 6}
    {'_id': 'greggerm', 'count': 6}
    {'_id': 'techlady', 'count': 6}
    {'_id': 'LA2', 'count': 6}
    {'_id': 'CalliBrown', 'count': 6}
    {'_id': 'Jblack76', 'count': 6}
    {'_id': 'JerenYun', 'count': 6}
    {'_id': 'jamesks', 'count': 6}
    {'_id': 'Kristotu', 'count': 6}
    {'_id': 'Grueny', 'count': 6}
    {'_id': 'J Hodge', 'count': 6}
    {'_id': 'Rob Gagala', 'count': 6}
    {'_id': 'darklighter', 'count': 6}
    {'_id': 'miklas', 'count': 6}
    {'_id': 'Kia Of North Aurora', 'count': 6}
    {'_id': 'parukhin', 'count': 6}
    {'_id': 'Hedaja', 'count': 6}
    {'_id': 'schenectandy', 'count': 6}
    {'_id': 'spod', 'count': 6}
    {'_id': 'Dieter Schmeer', 'count': 5}
    {'_id': 'earias04', 'count': 5}
    {'_id': 'WyattZastrow', 'count': 5}
    {'_id': 'eedfre', 'count': 5}
    {'_id': 'gwumapper', 'count': 5}
    {'_id': 'Maryland Home Search', 'count': 5}
    {'_id': 'KyleMachalinski', 'count': 5}
    {'_id': '503Greg', 'count': 5}
    {'_id': 'aldimond', 'count': 5}
    {'_id': 'brogo', 'count': 5}
    {'_id': 'maddentim', 'count': 5}
    {'_id': 'williamrh', 'count': 5}
    {'_id': 'jstratm', 'count': 5}
    {'_id': 'MikeMike', 'count': 5}
    {'_id': 'Bakerboy448', 'count': 5}
    {'_id': 'Ppatel1', 'count': 5}
    {'_id': 'LMarkko', 'count': 5}
    {'_id': 'Sabra Sharaya', 'count': 5}
    {'_id': 'CAPTAINWIK', 'count': 5}
    {'_id': 'Gozgo', 'count': 5}
    {'_id': 'davidbmalone', 'count': 5}
    {'_id': 'ljurus', 'count': 5}
    {'_id': 'paully', 'count': 5}
    {'_id': 'Esperanza36', 'count': 5}
    {'_id': 'KDS4444', 'count': 5}
    {'_id': 'sdahod', 'count': 5}
    {'_id': 'JeffreyHerr', 'count': 5}
    {'_id': 'verticalgeo', 'count': 5}
    {'_id': 'DEX50', 'count': 5}
    {'_id': 'HattoriHanzo', 'count': 5}
    {'_id': 'Eric Hansen', 'count': 5}
    {'_id': 'don-vip', 'count': 5}
    {'_id': 'YuraH', 'count': 5}
    {'_id': 'jsachicago', 'count': 5}
    {'_id': 'yusufbangura', 'count': 5}
    {'_id': 'bdopenstreetmap', 'count': 5}
    {'_id': 'Unusual User Name', 'count': 5}
    {'_id': 'Ant-man', 'count': 5}
    {'_id': 'Bussophron', 'count': 5}
    {'_id': 'beej71', 'count': 5}
    {'_id': 'jneptune', 'count': 4}
    {'_id': 'cvwarren', 'count': 4}
    {'_id': 'mgmcc', 'count': 4}
    {'_id': 'meghanjeanne', 'count': 4}
    {'_id': 'afdreher', 'count': 4}
    {'_id': 'Bobo3', 'count': 4}
    {'_id': 'kjon', 'count': 4}
    {'_id': 'skorasaurus', 'count': 4}
    {'_id': 'kalafut', 'count': 4}
    {'_id': 'EPAstor', 'count': 4}
    {'_id': 'Lasting Damage', 'count': 4}
    {'_id': 'dondrake', 'count': 4}
    {'_id': 'azap23', 'count': 4}
    {'_id': 'catarrh', 'count': 4}
    {'_id': 'marmarinou', 'count': 4}
    {'_id': 'spark', 'count': 4}
    {'_id': 'scarz', 'count': 4}
    {'_id': 'rolajos', 'count': 4}
    {'_id': 'jrade', 'count': 4}
    {'_id': 'ChicagoPat', 'count': 4}
    {'_id': 'Jean Bully', 'count': 4}
    {'_id': 'MFKDGAF', 'count': 4}
    {'_id': 'kcorless', 'count': 4}
    {'_id': 'moebeeeeee', 'count': 4}
    {'_id': 'timd40', 'count': 4}
    {'_id': 'JohnWG', 'count': 4}
    {'_id': 'HHCacher', 'count': 4}
    {'_id': 'JRE1979', 'count': 4}
    {'_id': 'Pancake Lover', 'count': 4}
    {'_id': 'Chet S', 'count': 4}
    {'_id': 'ddohler', 'count': 4}
    {'_id': 'matteditmsts', 'count': 4}
    {'_id': 'derFred', 'count': 4}
    {'_id': 'patmulchrone', 'count': 4}
    {'_id': 'jg3', 'count': 4}
    {'_id': 'Boyee', 'count': 4}
    {'_id': 'Mappington', 'count': 4}
    {'_id': 'plincoln', 'count': 4}
    {'_id': 'Jonathan ZHAO', 'count': 4}
    {'_id': 'agnieszka78', 'count': 4}
    {'_id': 'aschmitz', 'count': 4}
    {'_id': '3ftcatheter', 'count': 4}
    {'_id': 'ayo10', 'count': 4}
    {'_id': 'HaBazza', 'count': 4}
    {'_id': 'alimamo', 'count': 4}
    {'_id': 'FightingIrish1', 'count': 3}
    {'_id': 'riverpaddler', 'count': 3}
    {'_id': 'choess', 'count': 3}
    {'_id': 'nimix', 'count': 3}
    {'_id': 'Rouni', 'count': 3}
    {'_id': 'Rosscoe', 'count': 3}
    {'_id': 'keinseier', 'count': 3}
    {'_id': 'Anthonyloc1', 'count': 3}
    {'_id': 'Jamie Tate', 'count': 3}
    {'_id': 'Dr Kludge', 'count': 3}
    {'_id': 'RafalG', 'count': 3}
    {'_id': 'fugazi0176', 'count': 3}
    {'_id': 'bobbow', 'count': 3}
    {'_id': 'tyler grad party', 'count': 3}
    {'_id': 'jharpster', 'count': 3}
    {'_id': 'PierZen', 'count': 3}
    {'_id': 'Bradley Goliber', 'count': 3}
    {'_id': 'GeoVern', 'count': 3}
    {'_id': 'StarlaM', 'count': 3}
    {'_id': 'amorfeusz', 'count': 3}
    {'_id': 'Hobgoblin', 'count': 3}
    {'_id': 'Bryan Luman', 'count': 3}
    {'_id': 'soonerbh', 'count': 3}
    {'_id': 'rickmastfan67', 'count': 3}
    {'_id': 'MeLLoCeLLo', 'count': 3}
    {'_id': 'mziehm', 'count': 3}
    {'_id': 'Josip Jebac', 'count': 3}
    {'_id': 'ejswendsen', 'count': 3}
    {'_id': 'doremite', 'count': 3}
    {'_id': 'ceyockey', 'count': 3}
    {'_id': 'scidude', 'count': 3}
    {'_id': 'Mark_S', 'count': 3}
    {'_id': 'dforsi', 'count': 3}
    {'_id': 'Scott07', 'count': 3}
    {'_id': 'Joe The Dragon', 'count': 3}
    {'_id': 'Warhobbit', 'count': 3}
    {'_id': 'hipsmart', 'count': 3}
    {'_id': 'jenrl', 'count': 3}
    {'_id': 'Pmz', 'count': 3}
    {'_id': 'EdwardD20', 'count': 3}
    {'_id': 'jkokoris', 'count': 3}
    {'_id': 'Geo_Liz', 'count': 3}
    {'_id': 'Privett', 'count': 3}
    {'_id': 'JJ21', 'count': 3}
    {'_id': 'psparks67', 'count': 3}
    {'_id': 'WanMil', 'count': 3}
    {'_id': 'wieland', 'count': 3}
    {'_id': 'Astadamasta', 'count': 3}
    {'_id': 'Kenny Oh', 'count': 3}
    {'_id': 'jsjgruber', 'count': 3}
    {'_id': 'lyx', 'count': 3}
    {'_id': 'CourtneyClark', 'count': 3}
    {'_id': 'ADSLLC', 'count': 3}
    {'_id': 'nandu', 'count': 3}
    {'_id': 'Kurt Pfaender', 'count': 3}
    {'_id': 'DaBears', 'count': 3}
    {'_id': 'Tom Chance', 'count': 3}
    {'_id': 'eberry', 'count': 3}
    {'_id': 'r4vi', 'count': 3}
    {'_id': 'Gecko07', 'count': 3}
    {'_id': 'jwthornton', 'count': 3}
    {'_id': 'mj890530', 'count': 3}
    {'_id': 'Oleksandr Zabolotnyi', 'count': 2}
    {'_id': 'edenh', 'count': 2}
    {'_id': 'malenki', 'count': 2}
    {'_id': 'ajashton', 'count': 2}
    {'_id': 'abgandar', 'count': 2}
    {'_id': 'anbr', 'count': 2}
    {'_id': 'maneshe', 'count': 2}
    {'_id': 'pnorman', 'count': 2}
    {'_id': 'Julia Norris', 'count': 2}
    {'_id': 'HokiePilot', 'count': 2}
    {'_id': 'jacobbraeutigam', 'count': 2}
    {'_id': 'wmann', 'count': 2}
    {'_id': 'Relax Inn', 'count': 2}
    {'_id': 'jdwilbur', 'count': 2}
    {'_id': 'PeterLitton', 'count': 2}
    {'_id': 'SXSPM', 'count': 2}
    {'_id': 'DLichti', 'count': 2}
    {'_id': 'djplx', 'count': 2}
    {'_id': 'yasse1406', 'count': 2}
    {'_id': 'iav', 'count': 2}
    {'_id': 'EdVisser', 'count': 2}
    {'_id': 'MrMintyFresh', 'count': 2}
    {'_id': 'hopet', 'count': 2}
    {'_id': 'Maheshkr81', 'count': 2}
    {'_id': 'EricW2000', 'count': 2}
    {'_id': 'jfire', 'count': 2}
    {'_id': 'mapsinE3', 'count': 2}
    {'_id': 'bdcrazy', 'count': 2}
    {'_id': 'bcd2', 'count': 2}
    {'_id': 'HDietze', 'count': 2}
    {'_id': 'Ards Man', 'count': 2}
    {'_id': 'Goldilocks', 'count': 2}
    {'_id': 'BBOSM', 'count': 2}
    {'_id': 'hartsfmf', 'count': 2}
    {'_id': 'John Keith Hohm', 'count': 2}
    {'_id': 'sahal', 'count': 2}
    {'_id': 'Espio', 'count': 2}
    {'_id': 'QLP2004', 'count': 2}
    {'_id': 'Wicked Chocolates', 'count': 2}
    {'_id': 'Catalin Capota', 'count': 2}
    {'_id': 'Sparks', 'count': 2}
    {'_id': 'huntermap', 'count': 2}
    {'_id': 'TheHammer', 'count': 2}
    {'_id': 'Syl', 'count': 2}
    {'_id': 'skobbler', 'count': 2}
    {'_id': 'theophrastos', 'count': 2}
    {'_id': 'GaryBill', 'count': 2}
    {'_id': 'adelehant', 'count': 2}
    {'_id': 'tchai', 'count': 2}
    {'_id': 'breizhjedi', 'count': 2}
    {'_id': 'ChicagoAndy', 'count': 2}
    {'_id': 'nhoffm', 'count': 2}
    {'_id': 'Sven Anders', 'count': 2}
    {'_id': 'Thommie Rother', 'count': 2}
    {'_id': 'sclarke', 'count': 2}
    {'_id': 'worldwidewolford', 'count': 2}
    {'_id': 'pagedesk', 'count': 2}
    {'_id': 'Clang', 'count': 2}
    {'_id': 'jeremyfelt', 'count': 2}
    {'_id': 'mueschel', 'count': 2}
    {'_id': 'PaulEdlund', 'count': 2}
    {'_id': 'Robbins', 'count': 2}
    {'_id': 'Siddiqui', 'count': 2}
    {'_id': 'localcelebrity', 'count': 2}
    {'_id': 'fireball2', 'count': 2}
    {'_id': None, 'count': 2}
    {'_id': 'tixuwuoz', 'count': 2}
    {'_id': 'Gregory Williams', 'count': 2}
    {'_id': 'JoshD', 'count': 2}
    {'_id': 'Oberaffe', 'count': 2}
    {'_id': 'BigBadChicago', 'count': 2}
    {'_id': 'chimaps', 'count': 2}
    {'_id': 'jot', 'count': 2}
    {'_id': 'ns130291', 'count': 2}
    {'_id': 'schlek', 'count': 2}
    {'_id': 'hfs', 'count': 2}
    {'_id': 'ckaufman', 'count': 2}
    {'_id': 'leuty', 'count': 2}
    {'_id': 'dieterdreist', 'count': 2}
    {'_id': 'jcnoble2', 'count': 2}
    {'_id': 'joyous', 'count': 2}
    {'_id': 'jmsmith', 'count': 2}
    {'_id': 'batniu', 'count': 2}
    {'_id': 'Adduc', 'count': 2}
    {'_id': 'gkirsch', 'count': 2}
    {'_id': 'Jesús Gómez', 'count': 2}
    {'_id': 'slapula', 'count': 2}
    {'_id': 'jazzdude00021', 'count': 2}
    {'_id': 'Shalini', 'count': 2}
    {'_id': 'corin_atwell', 'count': 2}
    {'_id': 'anthonyfrance', 'count': 2}
    {'_id': 'incongruity', 'count': 2}
    {'_id': 'EricSJ', 'count': 1}
    {'_id': 'dufekin', 'count': 1}
    {'_id': 'beweta', 'count': 1}
    {'_id': 'NBahler', 'count': 1}
    {'_id': 'behemoth14', 'count': 1}
    {'_id': 'railfan-eric', 'count': 1}
    {'_id': 'DENelson83', 'count': 1}
    {'_id': 'triplemultiplex', 'count': 1}
    {'_id': 'naoliv', 'count': 1}
    {'_id': 'Jedrzej Pelka', 'count': 1}
    {'_id': 'rmaus', 'count': 1}
    {'_id': 'Kingofitall', 'count': 1}
    {'_id': 'happy5214', 'count': 1}
    {'_id': 'GIS_Downers', 'count': 1}
    {'_id': 'j3d', 'count': 1}
    {'_id': 'SoulMap', 'count': 1}
    {'_id': 'smurfzilla', 'count': 1}
    {'_id': 'WASIO', 'count': 1}
    {'_id': 'catflop', 'count': 1}
    {'_id': 'local1001', 'count': 1}
    {'_id': 'marscot', 'count': 1}
    {'_id': 'Claudius Henrichs', 'count': 1}
    {'_id': 'JessieB', 'count': 1}
    {'_id': 'williamsmdr', 'count': 1}
    {'_id': 'stw1701', 'count': 1}
    {'_id': 'fachi', 'count': 1}
    {'_id': 'IncaEmpire', 'count': 1}
    {'_id': 'slashme', 'count': 1}
    {'_id': 'MasiMaster', 'count': 1}
    {'_id': 'Cyphase', 'count': 1}
    {'_id': 'Suz_Andersen', 'count': 1}
    {'_id': 'mjulius', 'count': 1}
    {'_id': 'Caribou52', 'count': 1}
    {'_id': 'kre3d', 'count': 1}
    {'_id': 'saG', 'count': 1}
    {'_id': 'jimt1963', 'count': 1}
    {'_id': 'John Carota', 'count': 1}
    {'_id': 'Pmcall221', 'count': 1}
    {'_id': 'jgon6', 'count': 1}
    {'_id': 'sbichsel', 'count': 1}
    {'_id': 'ehatlebe', 'count': 1}
    {'_id': 'SNIPatrick', 'count': 1}
    {'_id': 'Dhilbish', 'count': 1}
    {'_id': 'Stemby', 'count': 1}
    {'_id': 'mboote', 'count': 1}
    {'_id': 'ciccio20', 'count': 1}
    {'_id': 'zEEs', 'count': 1}
    {'_id': 'rhop', 'count': 1}
    {'_id': 'falcoiii', 'count': 1}
    {'_id': 'Merichleri', 'count': 1}
    {'_id': 'shivarx', 'count': 1}
    {'_id': 'Krystyna Kowalik', 'count': 1}
    {'_id': 'thesocialbatch', 'count': 1}
    {'_id': 'PerKjaer', 'count': 1}
    {'_id': 'devotedlhasa', 'count': 1}
    {'_id': 'katie@freydesign', 'count': 1}
    {'_id': 'dabowler15', 'count': 1}
    {'_id': 'T2000', 'count': 1}
    {'_id': 'pirgostrans', 'count': 1}
    {'_id': 'MDSEUSA', 'count': 1}
    {'_id': 'Gerneck', 'count': 1}
    {'_id': 'gremillard', 'count': 1}
    {'_id': 'biverson', 'count': 1}
    {'_id': 'aceman444', 'count': 1}
    {'_id': 'jlyo', 'count': 1}
    {'_id': '9008bp_gmail', 'count': 1}
    {'_id': 'MaureenFlanagan', 'count': 1}
    {'_id': 'Immediate MD', 'count': 1}
    {'_id': 'djapeman', 'count': 1}
    {'_id': 'brucegoldstone', 'count': 1}
    {'_id': 'Duraply', 'count': 1}
    {'_id': 'mattdtc', 'count': 1}
    {'_id': 'DaBunny', 'count': 1}
    {'_id': 'Bazturd', 'count': 1}
    {'_id': 'Riss Centaur', 'count': 1}
    {'_id': 'odna', 'count': 1}
    {'_id': 'sdole', 'count': 1}
    {'_id': 'Tonita', 'count': 1}
    {'_id': 'otsf12', 'count': 1}
    {'_id': 'dealsmag', 'count': 1}
    {'_id': 'epanella', 'count': 1}
    {'_id': 'Jokke', 'count': 1}
    {'_id': 'marcwmclaughlin', 'count': 1}
    {'_id': 'gorn', 'count': 1}
    {'_id': 'thebuckinghamchicago', 'count': 1}
    {'_id': 'eziggy', 'count': 1}
    {'_id': 'chmoss', 'count': 1}
    {'_id': 'Ennasee', 'count': 1}
    {'_id': 'Central America', 'count': 1}
    {'_id': 'patmccarthy68', 'count': 1}
    {'_id': 'androidguy', 'count': 1}
    {'_id': 'CleanUp', 'count': 1}
    {'_id': 'aruzin', 'count': 1}
    {'_id': 'Blobo123', 'count': 1}
    {'_id': 'cata2c', 'count': 1}
    {'_id': 'Jofus', 'count': 1}
    {'_id': 'oldenburg69', 'count': 1}
    {'_id': 'Theodin', 'count': 1}
    {'_id': 'Mr PJ', 'count': 1}
    {'_id': 'mempko', 'count': 1}
    {'_id': 'Philip Kluss', 'count': 1}
    {'_id': 'MannyMartinez', 'count': 1}
    {'_id': 'clipdude', 'count': 1}
    {'_id': 'Vinay Nayik', 'count': 1}
    {'_id': 'oss', 'count': 1}
    {'_id': '3mikey1', 'count': 1}
    {'_id': 'Safco Dental', 'count': 1}
    {'_id': 'Vikky Chan', 'count': 1}
    {'_id': 'Paul Esling', 'count': 1}
    {'_id': 'UteBarry', 'count': 1}
    {'_id': 'durin42', 'count': 1}
    {'_id': 'gLarson', 'count': 1}
    {'_id': 'dmgroom_ct', 'count': 1}
    {'_id': 'dmhall2', 'count': 1}
    {'_id': 'malford924', 'count': 1}
    {'_id': 'Augusto S', 'count': 1}
    {'_id': 'Tom Donofrio', 'count': 1}
    {'_id': 'dmarkowicz', 'count': 1}
    {'_id': 'Steve', 'count': 1}
    {'_id': 'DonGauthier', 'count': 1}
    {'_id': 'staehler', 'count': 1}
    {'_id': 'captainjjim', 'count': 1}
    {'_id': 'Solidmercury', 'count': 1}
    {'_id': 'Data411', 'count': 1}
    {'_id': 'Dschwen', 'count': 1}
    {'_id': 'Canabis', 'count': 1}
    {'_id': 'CrossFit Park Ridge', 'count': 1}
    {'_id': 'rewallac', 'count': 1}
    {'_id': 'MHKid', 'count': 1}
    {'_id': 'cquest', 'count': 1}
    {'_id': 'Tinshack', 'count': 1}
    {'_id': 'freshworks', 'count': 1}
    {'_id': 'AM909', 'count': 1}
    {'_id': 'BiIbo', 'count': 1}
    {'_id': 'DGilbertson', 'count': 1}
    {'_id': 'Jacobs Studios', 'count': 1}
    {'_id': 'jpers36', 'count': 1}
    {'_id': 'indigomc', 'count': 1}
    {'_id': 'GSX', 'count': 1}
    {'_id': 'skst', 'count': 1}
    {'_id': 'Chris Filip', 'count': 1}
    {'_id': 'nicklbailey', 'count': 1}
    {'_id': 'Daniel Neel', 'count': 1}
    {'_id': 'indot-sfischer', 'count': 1}
    {'_id': 'csheaff', 'count': 1}
    {'_id': 'brianwalk_r', 'count': 1}
    {'_id': 'MarksOSM', 'count': 1}
    {'_id': 'rayosborn', 'count': 1}
    {'_id': 'tkaap', 'count': 1}
    {'_id': 'ChicagoAnimation', 'count': 1}
    {'_id': 'euphoria240', 'count': 1}
    {'_id': 'bretmoy', 'count': 1}
    {'_id': 'ckellner', 'count': 1}
    {'_id': 'C Byrne', 'count': 1}
    {'_id': 'Ksurma20216', 'count': 1}
    {'_id': 'Mehettinger', 'count': 1}
    {'_id': 'seazeal_fz', 'count': 1}
    {'_id': 'Simon M', 'count': 1}
    {'_id': 'tusharsamant', 'count': 1}
    {'_id': 'kls', 'count': 1}
    {'_id': 'Sharlin', 'count': 1}
    {'_id': 'osm-sputnik', 'count': 1}
    {'_id': 'meduza8000', 'count': 1}
    {'_id': 'Snusmumriken', 'count': 1}
    {'_id': 'LEPT0N', 'count': 1}
    {'_id': 'Liniment', 'count': 1}
    {'_id': 'Brutus', 'count': 1}
    {'_id': 'DialH', 'count': 1}
    {'_id': '夯船长', 'count': 1}
    {'_id': 'kaerast', 'count': 1}
    {'_id': 'Drew2324', 'count': 1}
    {'_id': 'sdawgisinthebuilding', 'count': 1}
    {'_id': 'Este13', 'count': 1}
    {'_id': 'xylome', 'count': 1}
    {'_id': 'tesia1971', 'count': 1}
    {'_id': 'hemidrums', 'count': 1}
    {'_id': 'LibertyWatchman', 'count': 1}
    {'_id': 'AbbyMae', 'count': 1}
    {'_id': 'Belmont Tower', 'count': 1}
    {'_id': 'gam3', 'count': 1}
    {'_id': 'nvk', 'count': 1}
    {'_id': 'amstephanie', 'count': 1}
    {'_id': 'Lemur', 'count': 1}
    {'_id': 'jeffkelley', 'count': 1}
    {'_id': 'BBultema', 'count': 1}
    {'_id': 'Chipk', 'count': 1}
    {'_id': 'Stephanie May', 'count': 1}
    {'_id': 'Yuwei Lin', 'count': 1}
    {'_id': 'vergueishon', 'count': 1}
    {'_id': 'freietonne-db', 'count': 1}
    {'_id': 'zacmccormick', 'count': 1}
    {'_id': 'CJ Rhodes', 'count': 1}
    {'_id': 'hankpi', 'count': 1}
    {'_id': 'Paulo Magalhaes', 'count': 1}
    {'_id': 'dlhawkins', 'count': 1}
    {'_id': 'lorac42', 'count': 1}
    {'_id': 'heinzp', 'count': 1}
    {'_id': 'Matt Toups', 'count': 1}
    {'_id': 'Jim Campbell', 'count': 1}
    {'_id': 'nickrosencrans', 'count': 1}
    {'_id': 'deadfocus', 'count': 1}
    {'_id': 'dtkindler', 'count': 1}
    {'_id': 'Gafergus', 'count': 1}
    {'_id': 'bkredell', 'count': 1}
    {'_id': 'rjroxas', 'count': 1}
    {'_id': 'Nyq', 'count': 1}
    {'_id': 'davidrohome', 'count': 1}
    {'_id': '_sev', 'count': 1}
    {'_id': 'mstriewe', 'count': 1}
    {'_id': 'MartyW', 'count': 1}
    {'_id': 'Naumburger', 'count': 1}
    {'_id': 'Nzara', 'count': 1}
    {'_id': 'WillCoForests', 'count': 1}
    {'_id': 'samlarsen1', 'count': 1}
    {'_id': 'surlyjake', 'count': 1}
    {'_id': 'Beccasvetlik', 'count': 1}
    {'_id': 'SCT67', 'count': 1}
    {'_id': 'sidsethupathi', 'count': 1}
    {'_id': 'Sked', 'count': 1}
    {'_id': 'Jeff Glass', 'count': 1}
    {'_id': 'birksland', 'count': 1}
    {'_id': 'Rostyua', 'count': 1}
    {'_id': 'CK1234', 'count': 1}
    {'_id': 'AnandTiwari', 'count': 1}
    {'_id': 'Randy25', 'count': 1}
    {'_id': 'Bike Mapper', 'count': 1}
    {'_id': 'didier2020', 'count': 1}
    {'_id': 'joeldw', 'count': 1}
    {'_id': 'Chuck Howard', 'count': 1}
    {'_id': 'gdjones', 'count': 1}
    {'_id': 'PhilipIbarrola', 'count': 1}
    {'_id': 'ChicagoBob', 'count': 1}
    {'_id': 'Flatrongraad', 'count': 1}
    {'_id': 'jspiewa', 'count': 1}
    {'_id': 'Hartmut Holzgraefe', 'count': 1}
    {'_id': 'mmcgrenera', 'count': 1}
    

### 按照 amenity  设施分类查看提交了多少种设施。由于插入数据中有多种类型，因此可看到没有amenity标签属性的数据最多，其次是公园6881次， place_of_worship理解为教堂等4314次，学校3389次。


```python

print("---------------------------------根据amenity统计设施次数----------------------------------------------")    
rs= db.aggregate([{
            "$group":{"_id":"$amenity", "count":{"$sum":1}}},{"$sort":{"count":-1}}
    ])

for doc in rs:
    pprint.pprint(doc)
```

    ---------------------------------根据amenity统计设施次数----------------------------------------------
    {'_id': None, 'count': 8748323}
    {'_id': 'parking', 'count': 6881}
    {'_id': 'place_of_worship', 'count': 4314}
    {'_id': 'school', 'count': 3389}
    {'_id': 'restaurant', 'count': 919}
    {'_id': 'fast_food', 'count': 770}
    {'_id': 'fuel', 'count': 452}
    {'_id': 'grave_yard', 'count': 430}
    {'_id': 'bicycle_rental', 'count': 299}
    {'_id': 'bank', 'count': 276}
    {'_id': 'fire_station', 'count': 266}
    {'_id': 'cafe', 'count': 235}
    {'_id': 'library', 'count': 233}
    {'_id': 'shelter', 'count': 190}
    {'_id': 'fountain', 'count': 186}
    {'_id': 'swimming_pool', 'count': 184}
    {'_id': 'post_office', 'count': 180}
    {'_id': 'drinking_water', 'count': 179}
    {'_id': 'pharmacy', 'count': 173}
    {'_id': 'hospital', 'count': 151}
    {'_id': 'toilets', 'count': 135}
    {'_id': 'pub', 'count': 119}
    {'_id': 'bar', 'count': 112}
    {'_id': 'post_box', 'count': 91}
    {'_id': 'police', 'count': 81}
    {'_id': 'townhall', 'count': 76}
    {'_id': 'bench', 'count': 67}
    {'_id': 'bicycle_parking', 'count': 67}
    {'_id': 'theatre', 'count': 65}
    {'_id': 'public_building', 'count': 62}
    {'_id': 'college', 'count': 58}
    {'_id': 'atm', 'count': 54}
    {'_id': 'car_wash', 'count': 42}
    {'_id': 'cinema', 'count': 42}
    {'_id': 'university', 'count': 30}
    {'_id': 'bus_station', 'count': 18}
    {'_id': 'prison', 'count': 17}
    {'_id': 'car_rental', 'count': 17}
    {'_id': 'kindergarten', 'count': 15}
    {'_id': 'arts_centre', 'count': 14}
    {'_id': 'dentist', 'count': 13}
    {'_id': 'waste_basket', 'count': 12}
    {'_id': 'community_centre', 'count': 12}
    {'_id': 'courthouse', 'count': 11}
    {'_id': 'veterinary', 'count': 10}
    {'_id': 'doctors', 'count': 8}
    {'_id': 'social_facility', 'count': 7}
    {'_id': 'car_sharing', 'count': 7}
    {'_id': 'bbq', 'count': 7}
    {'_id': 'clinic', 'count': 7}
    {'_id': 'parking_entrance', 'count': 7}
    {'_id': 'nightclub', 'count': 6}
    {'_id': 'emergency_phone', 'count': 6}
    {'_id': 'bureau_de_change', 'count': 5}
    {'_id': 'vending_machine', 'count': 5}
    {'_id': 'gym', 'count': 5}
    {'_id': 'marketplace', 'count': 5}
    {'_id': 'social_centre', 'count': 4}
    {'_id': 'nursing_home', 'count': 4}
    {'_id': 'recycling', 'count': 4}
    {'_id': 'ferry_terminal', 'count': 4}
    {'_id': 'taxi', 'count': 3}
    {'_id': 'pitch', 'count': 3}
    {'_id': 'ice_cream', 'count': 3}
    {'_id': 'shower', 'count': 3}
    {'_id': 'telephone', 'count': 3}
    {'_id': 'clock', 'count': 3}
    {'_id': 'proposed', 'count': 3}
    {'_id': 'parking_space', 'count': 2}
    {'_id': 'charging_station', 'count': 2}
    {'_id': 'storage', 'count': 2}
    {'_id': 'retirement_home', 'count': 2}
    {'_id': 'retail', 'count': 2}
    {'_id': 'shop', 'count': 2}
    {'_id': 'insurance', 'count': 2}
    {'_id': 'bleachers', 'count': 2}
    {'_id': 'exercise_facility', 'count': 2}
    {'_id': 'Government', 'count': 2}
    {'_id': 'picnic_site', 'count': 1}
    {'_id': 'boat_storage', 'count': 1}
    {'_id': 'plaza', 'count': 1}
    {'_id': 'gr', 'count': 1}
    {'_id': 'hookah_lounge', 'count': 1}
    {'_id': 'animal_shelter', 'count': 1}
    {'_id': 'conference_centre', 'count': 1}
    {'_id': 'wa', 'count': 1}
    {'_id': 'restaurant;bar', 'count': 1}
    {'_id': 'auto_impound', 'count': 1}
    {'_id': 'amphitheatre', 'count': 1}
    {'_id': 'embassy', 'count': 1}
    {'_id': 'biergarten', 'count': 1}
    {'_id': 'dance_theater', 'count': 1}
    {'_id': 'restrooms / water', 'count': 1}
    {'_id': 'monastery', 'count': 1}
    {'_id': 'baby_hatch', 'count': 1}
    {'_id': 'banquet_hall', 'count': 1}
    {'_id': 'web_development', 'count': 1}
    {'_id': 'overlook', 'count': 1}
    {'_id': 'rental', 'count': 1}
    {'_id': 'fitness_center', 'count': 1}
    {'_id': 'gas_station', 'count': 1}
    {'_id': 'hydrant', 'count': 1}
    {'_id': 'picnic', 'count': 1}
    {'_id': 'department_store', 'count': 1}
    {'_id': 'casino', 'count': 1}
    {'_id': 'food_court', 'count': 1}
    {'_id': 'gymnasium', 'count': 1}
    {'_id': 'Lombard Village Hall', 'count': 1}
    {'_id': 'batting_cage', 'count': 1}
    {'_id': 'dojo', 'count': 1}
    {'_id': 'internet_access', 'count': 1}
    {'_id': 'optometrist', 'count': 1}
    {'_id': 'spa', 'count': 1}
    {'_id': 'fitness_centre', 'count': 1}
    {'_id': 'picnic_table', 'count': 1}
    {'_id': 'arts_center', 'count': 1}
    

### 按照 amenity  =school 提交过的全部学校名称，大部分学校都是唯一提交，有些学校被多个用户或者多次提交数据中。芝加哥全部的学校不区分小初高共有2839所，名称中有middle默认为中学，共有140所。其他学校经对数据抽样常看没有特定规律能够识别是小学或者高中


```python

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

```

    ---------------------------------根据amenity=school统计设施次数----------------------------------------------
    {'_id': None, 'count': 166}
    {'_id': 'Lincoln Elementary School', 'count': 16}
    {'_id': 'Lincoln School', 'count': 11}
    {'_id': 'Saint Marys School', 'count': 10}
    {'_id': 'Saint Joseph School', 'count': 9}
    {'_id': 'Sacred Heart School', 'count': 8}
    {'_id': 'Saint Mary School', 'count': 8}
    {'_id': 'Saint Johns School', 'count': 8}
    {'_id': 'Central School', 'count': 8}
    {'_id': 'Washington Elementary School', 'count': 8}
    {'_id': 'Immaculate Conception School', 'count': 7}
    {'_id': 'Washington School', 'count': 6}
    {'_id': 'Whittier Elementary School', 'count': 6}
    {'_id': 'Trinity School', 'count': 6}
    {'_id': 'Immanuel School', 'count': 6}
    {'_id': 'Central Elementary School', 'count': 6}
    {'_id': 'Saint Paul School', 'count': 5}
    {'_id': 'Jefferson Elementary School', 'count': 5}
    {'_id': 'Benjamin Franklin Elementary School', 'count': 5}
    {'_id': 'Liberty Elementary School', 'count': 5}
    {'_id': 'Lincoln Junior High School', 'count': 5}
    {'_id': 'North Elementary School', 'count': 4}
    {'_id': 'Saint James School', 'count': 4}
    {'_id': 'Garfield Elementary School', 'count': 4}
    {'_id': 'Holy Cross School', 'count': 4}
    {'_id': 'South Elementary School', 'count': 4}
    {'_id': 'Irving Elementary School', 'count': 4}
    {'_id': 'Saint Peters School', 'count': 4}
    {'_id': 'Saint John School', 'count': 4}
    {'_id': 'Madison Elementary School', 'count': 4}
    {'_id': 'Longfellow School', 'count': 4}
    {'_id': 'Montessori School', 'count': 4}
    {'_id': 'Abraham Lincoln Elementary School', 'count': 4}
    {'_id': "Saint Mary's School", 'count': 4}
    {'_id': 'Highland Elementary School', 'count': 3}
    {'_id': 'Willard Elementary School', 'count': 3}
    {'_id': 'Walsh Elementary School', 'count': 3}
    {'_id': 'Lake Forest Academy', 'count': 3}
    {'_id': 'Prairie Elementary School', 'count': 3}
    {'_id': 'Emerson Elementary School', 'count': 3}
    {'_id': 'Saint Theresa School', 'count': 3}
    {'_id': 'Holy Rosary School', 'count': 3}
    {'_id': 'Sheridan Elementary School', 'count': 3}
    {'_id': 'Park School', 'count': 3}
    {'_id': 'Franklin School', 'count': 3}
    {'_id': 'Fairview Elementary School', 'count': 3}
    {'_id': 'Saint Nicholas School', 'count': 3}
    {'_id': 'Zion School', 'count': 3}
    {'_id': 'Park View Elementary School', 'count': 3}
    {'_id': 'Saint Anne School', 'count': 3}
    {'_id': 'Mohawk Elementary School', 'count': 3}
    {'_id': 'Carl Sandburg School', 'count': 3}
    {'_id': 'Assumption School', 'count': 3}
    {'_id': 'Indian Trail Elementary School', 'count': 3}
    {'_id': 'Our Lady of Perpetual Help School', 'count': 3}
    {'_id': 'Greenbriar School', 'count': 3}
    {'_id': 'McKinley Elementary School', 'count': 3}
    {'_id': 'Saint Thomas More School', 'count': 3}
    {'_id': 'Roosevelt School', 'count': 3}
    {'_id': 'Saint Paul Lutheran School', 'count': 3}
    {'_id': 'Debbies School of Beauty Culture', 'count': 3}
    {'_id': 'Trinity Lutheran School', 'count': 3}
    {'_id': 'Saint George School', 'count': 3}
    {'_id': 'Indian Trail Junior High School', 'count': 3}
    {'_id': 'Christ the King School', 'count': 3}
    {'_id': 'Chicago Urban Skills Institute', 'count': 3}
    {'_id': 'Thomas Jefferson Elementary School', 'count': 3}
    {'_id': 'Saint Josephs School', 'count': 3}
    {'_id': 'Jefferson School', 'count': 3}
    {'_id': 'George Washington Elementary School', 'count': 3}
    {'_id': 'Visitation School', 'count': 2}
    {'_id': 'Jane Addams Elementary School', 'count': 2}
    {'_id': 'Burnham Elementary School', 'count': 2}
    {'_id': 'Garvey Elementary School', 'count': 2}
    {'_id': 'Wheaton-Warrenville South High School', 'count': 2}
    {'_id': 'Jackie Robinson Elementary School', 'count': 2}
    {'_id': 'Dewey Elementary School', 'count': 2}
    {'_id': 'St Hyacinth Catholic School', 'count': 2}
    {'_id': 'Dawes Elementary School', 'count': 2}
    {'_id': 'Latin School of Chicago', 'count': 2}
    {'_id': 'Monroe Elementary School', 'count': 2}
    {'_id': 'Creekside Elementary School', 'count': 2}
    {'_id': "Walker's Grove Elementary School", 'count': 2}
    {'_id': 'Liberty Elementary', 'count': 2}
    {'_id': 'Graham Elementary School', 'count': 2}
    {'_id': 'Central High School', 'count': 2}
    {'_id': 'Washington School (historical)', 'count': 2}
    {'_id': 'John Simatovich Elementary School', 'count': 2}
    {'_id': 'Saint Mary of the Lake School', 'count': 2}
    {'_id': 'George Washington High School', 'count': 2}
    {'_id': 'Nobel Elementary School', 'count': 2}
    {'_id': 'Lowell Elementary School', 'count': 2}
    {'_id': 'Devonshire Elementary School', 'count': 2}
    {'_id': 'Wilson School', 'count': 2}
    {'_id': 'Washington Junior High School', 'count': 2}
    {'_id': 'Saint Catherine School', 'count': 2}
    {'_id': 'Enger School', 'count': 2}
    {'_id': 'Stevenson Elementary School', 'count': 2}
    {'_id': 'Eastview Elementary School', 'count': 2}
    {'_id': 'Wood Dale Junior High School', 'count': 2}
    {'_id': 'Saint Jude School', 'count': 2}
    {'_id': 'Bethany School', 'count': 2}
    {'_id': 'Eisenhower Junior High School', 'count': 2}
    {'_id': 'Hillcrest Elementary School', 'count': 2}
    {'_id': 'McCleery Elementary School', 'count': 2}
    {'_id': 'Saint Patrick School', 'count': 2}
    {'_id': 'Saint Pius X School', 'count': 2}
    {'_id': 'Saint Raphael School', 'count': 2}
    {'_id': 'Salt Creek Elementary School', 'count': 2}
    {'_id': 'Wilson Elementary School', 'count': 2}
    {'_id': 'Riley School', 'count': 2}
    {'_id': "Saint Peter's School", 'count': 2}
    {'_id': 'Saint Philip School', 'count': 2}
    {'_id': 'Sased School', 'count': 2}
    {'_id': 'Haines Elementary School', 'count': 2}
    {'_id': 'Clinton Elementary School', 'count': 2}
    {'_id': 'Southwest Chicago Christian School', 'count': 2}
    {'_id': 'Neil Armstrong Elementary School', 'count': 2}
    {'_id': 'Mount Carmel School', 'count': 2}
    {'_id': 'Robert Frost Elementary School', 'count': 2}
    {'_id': 'Hawthorne Elementary School', 'count': 2}
    {'_id': 'Woodrow Wilson Elementary School', 'count': 2}
    {'_id': 'Providence Catholic High School', 'count': 2}
    {'_id': 'Pershing Elementary School', 'count': 2}
    {'_id': 'Pleasant Hill Elementary School', 'count': 2}
    {'_id': 'Columbus Elementary School', 'count': 2}
    {'_id': 'Holmes Elementary School', 'count': 2}
    {'_id': 'Saint Pauls School', 'count': 2}
    {'_id': 'Holy Family School', 'count': 2}
    {'_id': 'Saint Cornelius School', 'count': 2}
    {'_id': 'Highland Middle School', 'count': 2}
    {'_id': 'Holy Trinity School', 'count': 2}
    {'_id': 'Ascension School', 'count': 2}
    {'_id': 'Saint Francis Xavier School', 'count': 2}
    {'_id': 'Longwood Elementary School', 'count': 2}
    {'_id': 'Roosevelt University', 'count': 2}
    {'_id': 'Algonquin Middle School', 'count': 2}
    {'_id': 'Everett Elementary School', 'count': 2}
    {'_id': 'Emerson School', 'count': 2}
    {'_id': 'Christ School', 'count': 2}
    {'_id': 'Roosevelt Elementary School', 'count': 2}
    {'_id': 'Eisenhower Elementary School', 'count': 2}
    {'_id': 'Saint Marys Seminary', 'count': 2}
    {'_id': 'Saint Ann School', 'count': 2}
    {'_id': 'Dwight D Eisenhower Elementary School', 'count': 2}
    {'_id': 'Saint Francis School', 'count': 2}
    {'_id': 'Nathan Hale Elementary School', 'count': 2}
    {'_id': 'All Saints School', 'count': 2}
    {'_id': 'Mann School', 'count': 2}
    {'_id': 'Bryant School', 'count': 2}
    {'_id': 'Jefferson Junior High School', 'count': 2}
    {'_id': 'Froebel School', 'count': 2}
    {'_id': 'Field Elementary School', 'count': 2}
    {'_id': 'Sherwood Elementary School', 'count': 2}
    {'_id': 'North School', 'count': 2}
    {'_id': 'Eugene Field School', 'count': 2}
    {'_id': 'Central Middle School', 'count': 2}
    {'_id': 'Annunciation School', 'count': 2}
    {'_id': 'Westbrook Elementary School', 'count': 2}
    {'_id': 'Grant School', 'count': 2}
    {'_id': 'Woodland School', 'count': 2}
    {'_id': 'Madison School', 'count': 2}
    {'_id': 'Saint Thomas School', 'count': 2}
    {'_id': 'Golgotha Early Childhood Center', 'count': 2}
    {'_id': 'Saint Angela School', 'count': 2}
    {'_id': 'Zion Lutheran School', 'count': 2}
    {'_id': 'Saint Michaels School', 'count': 2}
    {'_id': 'Kennedy Elementary School', 'count': 2}
    {'_id': 'Grant Elementary School', 'count': 2}
    {'_id': 'Palatine High School', 'count': 2}
    {'_id': 'Mundell Elementary School', 'count': 2}
    {'_id': 'Saint John Bosco School', 'count': 2}
    {'_id': 'Scott Elementary School', 'count': 2}
    {'_id': 'Gary Elementary School', 'count': 2}
    {'_id': 'Immanuel Lutheran School', 'count': 2}
    {'_id': 'Highlands Elementary School', 'count': 2}
    {'_id': 'Reed Elementary School', 'count': 2}
    {'_id': 'Mark Twain Elementary School', 'count': 2}
    {'_id': 'Saint Benedict School', 'count': 2}
    {'_id': 'Reavis Elementary School', 'count': 2}
    {'_id': 'Schneider Elementary School', 'count': 2}
    {'_id': 'Bolingbrook High School', 'count': 2}
    {'_id': 'Camelot School', 'count': 2}
    {'_id': 'Saint Alexander School', 'count': 2}
    {'_id': 'Saint Joan of Arc School', 'count': 2}
    {'_id': 'Ardmore Elementary School', 'count': 2}
    {'_id': 'Kenwood Elementary School', 'count': 2}
    {'_id': 'Traughber Junior High School', 'count': 2}
    {'_id': 'Saints Peter and Paul School', 'count': 2}
    {'_id': 'Turner Elementary School', 'count': 2}
    {'_id': 'Cove School', 'count': 2}
    {'_id': 'Memorial Elementary School', 'count': 2}
    {'_id': 'Saint Marks School', 'count': 2}
    {'_id': 'Dirksen Elementary School', 'count': 2}
    {'_id': 'Jonas E Salk Elementary School', 'count': 2}
    {'_id': 'Minooka Junior High School', 'count': 2}
    {'_id': 'Grace School', 'count': 2}
    {'_id': 'Young Elementary School', 'count': 2}
    {'_id': 'Eugene Field Elementary School', 'count': 2}
    {'_id': 'National-Louis University', 'count': 2}
    {'_id': 'Our Lady of Grace School', 'count': 2}
    {'_id': 'Longfellow Elementary School', 'count': 2}
    {'_id': 'Acapulco Driving School', 'count': 2}
    {'_id': 'Libertyville High School', 'count': 2}
    {'_id': 'Barrington Middle School', 'count': 2}
    {'_id': 'American Islamic College', 'count': 2}
    {'_id': 'Holy Angels School', 'count': 2}
    {'_id': 'Saint Alphonsus School', 'count': 2}
    {'_id': 'Nicholas A Hermes Elementary School', 'count': 2}
    {'_id': 'Old Town School of Folk Music', 'count': 2}
    {'_id': 'Notre Dame School', 'count': 2}
    {'_id': 'Kolmar School', 'count': 2}
    {'_id': 'Woodland Elementary School', 'count': 2}
    {'_id': 'Lafayette Elementary School', 'count': 2}
    {'_id': 'Walnut Trails Elementary School', 'count': 2}
    {'_id': 'James Whitcomb Riley Elementary School', 'count': 2}
    {'_id': 'Illinois Center for Rehabilitation', 'count': 1}
    {'_id': 'Miner Junior High School', 'count': 1}
    {'_id': 'Windsor Elementary School', 'count': 1}
    {'_id': 'Lake Louise Elementary School', 'count': 1}
    {'_id': 'Victor J. Andrew High School', 'count': 1}
    {'_id': 'Gwendolyn Brooks Elementary School', 'count': 1}
    {'_id': 'Granger Middle School', 'count': 1}
    {'_id': 'Robert Frost Junior High School', 'count': 1}
    {'_id': 'Sycamore Trails Elementary School', 'count': 1}
    {'_id': 'Agassiz Elementary School', 'count': 1}
    {'_id': 'Spaulding Elementary School', 'count': 1}
    {'_id': 'Earle School', 'count': 1}
    {'_id': 'Green Elementary School', 'count': 1}
    {'_id': 'Dirksen Middle School', 'count': 1}
    {'_id': 'Cullen School', 'count': 1}
    {'_id': 'Kipling School', 'count': 1}
    {'_id': "Children's Developmental Institute", 'count': 1}
    {'_id': 'Ryder Elementary School', 'count': 1}
    {'_id': 'Indian Plains High School', 'count': 1}
    {'_id': 'Dunne School', 'count': 1}
    {'_id': 'Mount Calvary Christian Academy', 'count': 1}
    {'_id': 'Plainfield CISD 202 High School Site', 'count': 1}
    {'_id': 'Foster Park Elementary School', 'count': 1}
    {'_id': 'Sauganash School', 'count': 1}
    {'_id': 'Owen Scholastic Academy', 'count': 1}
    {'_id': 'Lovett School', 'count': 1}
    {'_id': 'Sayre Language Academy', 'count': 1}
    {'_id': 'Frederick Douglass Middle School', 'count': 1}
    {'_id': 'Spencer Technology Academy', 'count': 1}
    {'_id': 'Austin Polytechnical Academy High School', 'count': 1}
    {'_id': 'Barrington High School', 'count': 1}
    {'_id': 'Finkl Elementary School', 'count': 1}
    {'_id': 'Warren Elementary School', 'count': 1}
    {'_id': 'Seton Academy', 'count': 1}
    {'_id': 'Elizabeth Meyer School', 'count': 1}
    {'_id': 'Hefferan Elementary School', 'count': 1}
    {'_id': 'White School', 'count': 1}
    {'_id': 'Dvorak Elementary School', 'count': 1}
    {'_id': 'Mason Elementary School', 'count': 1}
    {'_id': 'Queen of Martyrs School', 'count': 1}
    {'_id': 'Twain Elementary School', 'count': 1}
    {'_id': 'Randolph School', 'count': 1}
    {'_id': 'Sir Miles Davis Academy', 'count': 1}
    {'_id': 'Stagg Elementary School', 'count': 1}
    {'_id': 'Saint Genevieve School', 'count': 1}
    {'_id': 'Carroll Elementary School', 'count': 1}
    {'_id': 'Carroll-Rosenwald Elementary School', 'count': 1}
    {'_id': 'West Pullman Elementary School', 'count': 1}
    {'_id': 'Yates Elementary School', 'count': 1}
    {'_id': 'Anna R. Langford Community Academy', 'count': 1}
    {'_id': 'Simmons School', 'count': 1}
    {'_id': 'Oak Lawn High School', 'count': 1}
    {'_id': 'Amelia Earhart Elementary School', 'count': 1}
    {'_id': 'John H. Hamline Branch School', 'count': 1}
    {'_id': 'Edward A Bouchet Math & Science Academy', 'count': 1}
    {'_id': 'John L. Marsh Elementary School', 'count': 1}
    {'_id': 'Ruiz School', 'count': 1}
    {'_id': 'O A Thorp Scholastic Academy', 'count': 1}
    {'_id': 'Barry Elementary School', 'count': 1}
    {'_id': 'Saint Columbanus School', 'count': 1}
    {'_id': 'Chicago Vocational High School', 'count': 1}
    {'_id': 'Saint Charles Borromeo School', 'count': 1}
    {'_id': 'Turner-Drew Language Academy', 'count': 1}
    {'_id': 'Kershaw Elementary School', 'count': 1}
    {'_id': 'Saint Veronica School', 'count': 1}
    {'_id': 'McCutcheon Elementary School', 'count': 1}
    {'_id': 'John Muir Elementary School', 'count': 1}
    {'_id': 'Farren School', 'count': 1}
    {'_id': 'Saint Richard School', 'count': 1}
    {'_id': 'West School', 'count': 1}
    {'_id': 'Calumet Elementary School', 'count': 1}
    {'_id': 'James R. Doolittle, Jr. Elementary School', 'count': 1}
    {'_id': 'Wendell Smith Elementary School', 'count': 1}
    {'_id': 'Poe Classical School', 'count': 1}
    {'_id': 'Paul Simon Job Corps Center', 'count': 1}
    {'_id': 'William E.B. Dubois Elementary School', 'count': 1}
    {'_id': 'McCosh Elementary School', 'count': 1}
    {'_id': 'Future School and Park Site', 'count': 1}
    {'_id': 'McClure Junior High School', 'count': 1}
    {'_id': 'Willowbrook High School', 'count': 1}
    {'_id': 'Gunsaulus Scholastic Academy', 'count': 1}
    {'_id': 'Burke Elementary School', 'count': 1}
    {'_id': 'Curie Metropolitan High School', 'count': 1}
    {'_id': 'Illinois College of Optometry', 'count': 1}
    {'_id': 'UNO Soccer Academy', 'count': 1}
    {'_id': "Lyon's Township High School South Campus", 'count': 1}
    {'_id': 'Westmont High School', 'count': 1}
    {'_id': 'Walker School', 'count': 1}
    {'_id': 'Hinsdale Central High School', 'count': 1}
    {'_id': 'The Lane Elementary School', 'count': 1}
    {'_id': 'Jacob H. Carruthers Center for Inner City Studies', 'count': 1}
    {'_id': 'McClellan Elementary School', 'count': 1}
    {'_id': 'Buffalo Grove High School', 'count': 1}
    {'_id': 'Prospect Elementary School', 'count': 1}
    {'_id': 'Westview Hills Middle School', 'count': 1}
    {'_id': 'Rauner College Prep', 'count': 1}
    {'_id': 'Saint Mary of the Angels School', 'count': 1}
    {'_id': 'James B. Conant High School', 'count': 1}
    {'_id': 'Oakbrook Elementary School', 'count': 1}
    {'_id': 'Fairwood School', 'count': 1}
    {'_id': 'Nansen School', 'count': 1}
    {'_id': 'Gallistel Language Academy', 'count': 1}
    {'_id': 'Annunciata School', 'count': 1}
    {'_id': 'Paul Robeson High School', 'count': 1}
    {'_id': 'Harte Elementary School', 'count': 1}
    {'_id': 'Mount Vernon Elementary School', 'count': 1}
    {'_id': 'Jane Horton Ball Elementary School', 'count': 1}
    {'_id': 'Saint Phillip Neri School', 'count': 1}
    {'_id': 'National Teachers Academy', 'count': 1}
    {'_id': 'Simeon Vocational High School', 'count': 1}
    {'_id': 'Hoffman Estates High School', 'count': 1}
    {'_id': 'Anthony School', 'count': 1}
    {'_id': 'Weber High School', 'count': 1}
    {'_id': 'Lyon School', 'count': 1}
    {'_id': 'John Leigh Grammar School', 'count': 1}
    {'_id': 'Ridge Lawn Elementary School', 'count': 1}
    {'_id': 'J. Giles Elementary School', 'count': 1}
    {'_id': 'Steinmetz High School', 'count': 1}
    {'_id': 'Burr Oak Elementary School', 'count': 1}
    {'_id': 'Lawrence Elementary School', 'count': 1}
    {'_id': 'Willow Bend Elementary School', 'count': 1}
    {'_id': 'Rolling Meadows High School', 'count': 1}
    {'_id': 'Council Oak Montessori School', 'count': 1}
    {'_id': 'Barnard Elementary School', 'count': 1}
    {'_id': 'Clara Muhammad Elementary School', 'count': 1}
    {'_id': 'Powell Elementary School', 'count': 1}
    {'_id': "Saint Bride's School", 'count': 1}
    {'_id': 'Saint Bernadette School', 'count': 1}
    {'_id': 'Carver Primary School', 'count': 1}
    {'_id': 'New Field School', 'count': 1}
    {'_id': 'Jordan Community School', 'count': 1}
    {'_id': 'Sabin Magnet Dual Language School', 'count': 1}
    {'_id': 'Crown Point High School', 'count': 1}
    {'_id': 'Jesse Owens Community Academy', 'count': 1}
    {'_id': 'Grissom School', 'count': 1}
    {'_id': 'Saint Florian School', 'count': 1}
    {'_id': 'Francis Parker High School', 'count': 1}
    {'_id': 'Our Lady of Hungary School', 'count': 1}
    {'_id': 'International College of Surgeons', 'count': 1}
    {'_id': 'McCrone Research Institute', 'count': 1}
    {'_id': 'Dawson Technical Institute of Kennedy-King College', 'count': 1}
    {'_id': 'Swift Elementary School', 'count': 1}
    {'_id': 'Brenneman Elementary School', 'count': 1}
    {'_id': 'Barton Elementary School', 'count': 1}
    {'_id': 'Arnold School', 'count': 1}
    {'_id': 'Talcott Elementary School', 'count': 1}
    {'_id': 'Wells Community Academy High School', 'count': 1}
    {'_id': 'Carpenter Elementary School', 'count': 1}
    {'_id': 'Schiller Middle School', 'count': 1}
    {'_id': 'Smyth Elementary School', 'count': 1}
    {'_id': 'Cregier Vocational High School', 'count': 1}
    {'_id': 'Herbert Elementary School', 'count': 1}
    {'_id': 'Whitney M. Young Magnet High School', 'count': 1}
    {'_id': 'Tefft Middle School', 'count': 1}
    {'_id': 'Skinner Classical Elementary School', 'count': 1}
    {'_id': 'Chavez Multi-Cultural Academy', 'count': 1}
    {'_id': 'Hedges Elementary School', 'count': 1}
    {'_id': 'Andersen Elementary School', 'count': 1}
    {'_id': 'Hamline Elementary School', 'count': 1}
    {'_id': 'Sullivan High School', 'count': 1}
    {'_id': 'Saint Sabina School', 'count': 1}
    {'_id': 'Kelvyn Park High School', 'count': 1}
    {'_id': 'Kate Starr Kellogg Elementary School', 'count': 1}
    {'_id': 'Clissold Elementary School', 'count': 1}
    {'_id': 'Saint Barnabas School', 'count': 1}
    {'_id': 'Esmond Elementary School', 'count': 1}
    {'_id': 'Morgan Park High School', 'count': 1}
    {'_id': 'Saint Cajetan School', 'count': 1}
    {'_id': 'Lake View High School', 'count': 1}
    {'_id': 'Illinois Center for Rehabilitation and Education', 'count': 1}
    {'_id': 'Therapeutic School and Center forAutism Research ', 'count': 1}
    {'_id': 'Benito Juarez Community Academy', 'count': 1}
    {'_id': 'McCormick Elementary School', 'count': 1}
    {'_id': 'Little Village High School', 'count': 1}
    {'_id': 'Brown Elementary School', 'count': 1}
    {'_id': 'Good Shepherd School', 'count': 1}
    {'_id': 'Spry Elementary School', 'count': 1}
    {'_id': 'Kate S. Buckingham School', 'count': 1}
    {'_id': 'Saint Matthias School', 'count': 1}
    {'_id': 'Winfield Elementary School', 'count': 1}
    {'_id': 'Bethesda School', 'count': 1}
    {'_id': 'Oak Elementary School', 'count': 1}
    {'_id': 'Jamieson Elementary School', 'count': 1}
    {'_id': 'Robert Taft Middle School', 'count': 1}
    {'_id': 'Goethe Elementary School', 'count': 1}
    {'_id': 'Saint Sylvester School', 'count': 1}
    {'_id': 'Stowe Elementary School', 'count': 1}
    {'_id': 'Chase Elementary School', 'count': 1}
    {'_id': 'Chopin Elementary School', 'count': 1}
    {'_id': "Saint Mark's School", 'count': 1}
    {'_id': 'Brentano Elementary Math and Science Academy', 'count': 1}
    {'_id': 'Saint John Berchmans School', 'count': 1}
    {'_id': 'Mather High School', 'count': 1}
    {'_id': 'Stone Scholastic Academy', 'count': 1}
    {'_id': 'G. Armstrong Elementary School', 'count': 1}
    {'_id': 'George Westinghouse College Prep', 'count': 1}
    {'_id': 'Providence Saint Mel High School', 'count': 1}
    {'_id': 'Beidler Elementary School', 'count': 1}
    {'_id': 'Saint Nicolas School', 'count': 1}
    {'_id': 'Marquette Elementary School', 'count': 1}
    {'_id': 'Ernest Prussing Elementary School', 'count': 1}
    {'_id': 'Smyser Elementary School', 'count': 1}
    {'_id': 'Gordon Technical High School', 'count': 1}
    {'_id': 'Sacred Heart Schools', 'count': 1}
    {'_id': 'Irving Park Middle School', 'count': 1}
    {'_id': 'Reilly Elementary School', 'count': 1}
    {'_id': 'Our Lady of Victory School', 'count': 1}
    {'_id': 'Lake Street Elementary School', 'count': 1}
    {'_id': 'Patrick Henry Elementary School', 'count': 1}
    {'_id': 'Carol Moseley Braun School', 'count': 1}
    {'_id': 'Eisenhower High School', 'count': 1}
    {'_id': 'Pennoyer School', 'count': 1}
    {'_id': 'Mary Seat of Wisdom School', 'count': 1}
    {'_id': "Saint Peter's Lutheran School", 'count': 1}
    {'_id': 'Oriole Park Elementary School', 'count': 1}
    {'_id': 'Crow Island Elementary School', 'count': 1}
    {'_id': 'Marie Murphy School', 'count': 1}
    {'_id': 'Sears Elementary School', 'count': 1}
    {'_id': 'Our Lady of Ransom School', 'count': 1}
    {'_id': 'Maine East High School', 'count': 1}
    {'_id': 'Our Lady Mother of the Church School', 'count': 1}
    {'_id': 'Everett McKinley Dirksen School', 'count': 1}
    {'_id': 'Union Ridge Elementary School', 'count': 1}
    {'_id': 'Frazer International Magnet School', 'count': 1}
    {'_id': 'Colonel John Wheeler Middle School', 'count': 1}
    {'_id': 'Saint Paul of the Cross School', 'count': 1}
    {'_id': 'Saint Williams School', 'count': 1}
    {'_id': 'Julia S. Malloy Education Center', 'count': 1}
    {'_id': 'Attea Middle School', 'count': 1}
    {'_id': 'Saint John Brebeuf School', 'count': 1}
    {'_id': 'Montini Catholic High School', 'count': 1}
    {'_id': 'Kaneland Harter Middle School', 'count': 1}
    {'_id': 'Inter-American Magnet School', 'count': 1}
    {'_id': 'Knox School', 'count': 1}
    {'_id': 'Northeast Elementary School', 'count': 1}
    {'_id': 'Richard J. Daley Academy', 'count': 1}
    {'_id': 'Evergreen Park High School', 'count': 1}
    {'_id': 'Northwest School', 'count': 1}
    {'_id': 'Schrum Memorial Middle School', 'count': 1}
    {'_id': 'Schubert Elementary School', 'count': 1}
    {'_id': 'Falconer Elementary School', 'count': 1}
    {'_id': 'White Eagle Elementary School', 'count': 1}
    {'_id': 'Westchester Middle School', 'count': 1}
    {'_id': 'Geneva High School', 'count': 1}
    {'_id': 'Metea Valley High School', 'count': 1}
    {'_id': 'Neuqua Valley High School', 'count': 1}
    {'_id': 'Norton Creek Elementary School', 'count': 1}
    {'_id': 'Wredling Middle School', 'count': 1}
    {'_id': 'Wayne Builta School', 'count': 1}
    {'_id': 'Darwin Elementary School', 'count': 1}
    {'_id': 'Gregory R. Fischer Middle School', 'count': 1}
    {'_id': 'Northside Learning Center', 'count': 1}
    {'_id': 'Streamwood High School', 'count': 1}
    {'_id': 'Butterfield Elementary School', 'count': 1}
    {'_id': 'Canty Elementary School', 'count': 1}
    {'_id': 'St. Charles North High School', 'count': 1}
    {'_id': 'Edison Park Elementary School', 'count': 1}
    {'_id': 'Saint Turibius School', 'count': 1}
    {'_id': 'Lourdes High School', 'count': 1}
    {'_id': 'Lee Elementary School', 'count': 1}
    {'_id': 'Pasteur Elementary School', 'count': 1}
    {'_id': 'Saint Thecla School', 'count': 1}
    {'_id': 'Stock Elementary School', 'count': 1}
    {'_id': 'Dulles Elementary School', 'count': 1}
    {'_id': 'Saint Juliana School', 'count': 1}
    {'_id': 'Northside College Preparatory High School', 'count': 1}
    {'_id': 'Peterson Elementary School', 'count': 1}
    {'_id': 'Saint Lambert School', 'count': 1}
    {'_id': 'Caroline Bentley Elementary School', 'count': 1}
    {'_id': 'Saint Bruno School', 'count': 1}
    {'_id': 'Ridgewood Baptist Academy High School', 'count': 1}
    {'_id': 'Chicago Waldorf School', 'count': 1}
    {'_id': 'Avery Coonley School', 'count': 1}
    {'_id': 'University of Chicago Laboratory School', 'count': 1}
    {'_id': 'Aurora Central Catholic High School', 'count': 1}
    {'_id': 'Bryan Junior High School', 'count': 1}
    {'_id': 'Ogden Avenue Elementary School', 'count': 1}
    {'_id': 'Saint Joseph High School', 'count': 1}
    {'_id': 'Timothy Christian High School', 'count': 1}
    {'_id': 'Owens School', 'count': 1}
    {'_id': 'Luther High School South', 'count': 1}
    {'_id': 'Kennedy Junior High School', 'count': 1}
    {'_id': 'West RIdge Elementary School', 'count': 1}
    {'_id': 'Montessori School of Lisle', 'count': 1}
    {'_id': 'Benet Academy', 'count': 1}
    {'_id': 'Wauconda Community High School', 'count': 1}
    {'_id': 'Naperville Central High School', 'count': 1}
    {'_id': 'Elgin High School', 'count': 1}
    {'_id': 'Brookwood Junior High School', 'count': 1}
    {'_id': 'Hyde Park Academy', 'count': 1}
    {'_id': 'Mount Carmel High School', 'count': 1}
    {'_id': 'Thornwood High School', 'count': 1}
    {'_id': 'Saint Viator High School', 'count': 1}
    {'_id': 'West Aurora High School', 'count': 1}
    {'_id': 'Rose E. Krug Elementary School', 'count': 1}
    {'_id': 'Southeast School', 'count': 1}
    {'_id': 'River Grove Elementary School', 'count': 1}
    {'_id': 'Saint Francis Borgia School', 'count': 1}
    {'_id': 'Resurrection High School', 'count': 1}
    {'_id': 'Beard School', 'count': 1}
    {'_id': 'Manor Hill Elementary School', 'count': 1}
    {'_id': 'Glenn Westlake Middle School', 'count': 1}
    {'_id': 'Divine Providence School', 'count': 1}
    {'_id': 'Proviso West High School', 'count': 1}
    {'_id': 'South Loop Elementary School', 'count': 1}
    {'_id': 'Lemont High School', 'count': 1}
    {'_id': 'Trumbull Elementary School', 'count': 1}
    {'_id': 'Shakespeare Elementary School', 'count': 1}
    {'_id': 'Hamilton Elementary School', 'count': 1}
    {'_id': 'John J. Pershing Magnet School', 'count': 1}
    {'_id': 'Dunbar High School', 'count': 1}
    {'_id': 'Fermi Elementary School', 'count': 1}
    {'_id': 'Parkside Community Academy', 'count': 1}
    {'_id': 'Carl Sandburg High School', 'count': 1}
    {'_id': 'King College Prep', 'count': 1}
    {'_id': 'Nathan S. Davis Elementary School', 'count': 1}
    {'_id': 'Kozminski Community Academy', 'count': 1}
    {'_id': 'Rich Central High School', 'count': 1}
    {'_id': 'Philip Murray Language Academy', 'count': 1}
    {'_id': 'Saint Thomas the Apostle Grade School', 'count': 1}
    {'_id': 'William H. Ray Elementary School', 'count': 1}
    {'_id': 'Fleming Branch School', 'count': 1}
    {'_id': 'Grimes School', 'count': 1}
    {'_id': 'Hale Elementary School', 'count': 1}
    {'_id': 'Saint Rene School', 'count': 1}
    {'_id': 'Brother Rice High School', 'count': 1}
    {'_id': 'Meadow Lane School', 'count': 1}
    {'_id': 'Graham School of Management', 'count': 1}
    {'_id': 'Chicago High School for the Agricultural Sciences', 'count': 1}
    {'_id': 'Saint Cristina School', 'count': 1}
    {'_id': 'Hayt Elementary School', 'count': 1}
    {'_id': 'Wilmette Junior High School', 'count': 1}
    {'_id': 'Regina Dominican High School', 'count': 1}
    {'_id': 'Lombard Junior High School', 'count': 1}
    {'_id': 'Beth Hillel School', 'count': 1}
    {'_id': 'Franklin Fine Arts Center', 'count': 1}
    {'_id': 'Holden Elementary School', 'count': 1}
    {'_id': 'Bell School', 'count': 1}
    {'_id': 'Walker Elementary School', 'count': 1}
    {'_id': 'Lake Park High School', 'count': 1}
    {'_id': 'Lincolnwood Elementary School', 'count': 1}
    {'_id': 'Wadsworth Elementary School', 'count': 1}
    {'_id': 'Seabury-Western Theological Seminary', 'count': 1}
    {'_id': 'Harper Elementary School', 'count': 1}
    {'_id': 'McKenzie Elementary School', 'count': 1}
    {'_id': 'Ronald Knox Montessori School', 'count': 1}
    {'_id': 'Martin Luther King, Jr. Laboratory School', 'count': 1}
    {'_id': 'Shore Elementary School', 'count': 1}
    {'_id': 'Lutheran School of Theology', 'count': 1}
    {'_id': 'Stewart Elementary School', 'count': 1}
    {'_id': 'Carnegie Elementary School', 'count': 1}
    {'_id': 'Carver High School', 'count': 1}
    {'_id': 'Seventh Avenue Elementary School', 'count': 1}
    {'_id': 'L. J. Hauser Junior High School', 'count': 1}
    {'_id': 'De Marillac School', 'count': 1}
    {'_id': 'Brook Park Elementary School', 'count': 1}
    {'_id': 'Brenan Elementary School', 'count': 1}
    {'_id': 'Mater Christi School', 'count': 1}
    {'_id': 'Goudy Elementary School', 'count': 1}
    {'_id': 'Hollywood Elementary School', 'count': 1}
    {'_id': 'Riverside - Brookfield Township High School', 'count': 1}
    {'_id': 'Minooka Community High School - South Campus', 'count': 1}
    {'_id': 'Minooka Community High School - Centtral Campus', 'count': 1}
    {'_id': 'John Gates Elementary School', 'count': 1}
    {'_id': 'Wicker Park School', 'count': 1}
    {'_id': 'Sherman School of Excellence', 'count': 1}
    {'_id': 'Pritzker Elementary School', 'count': 1}
    {'_id': 'Old Orchard Junior High School', 'count': 1}
    {'_id': 'British School of Chicago', 'count': 1}
    {'_id': 'Bogan High School', 'count': 1}
    {'_id': 'Perspectives High School of Technology', 'count': 1}
    {'_id': 'Waldorf School of Chicago', 'count': 1}
    {'_id': 'Newberry Elementary Math & Science Academy', 'count': 1}
    {'_id': 'LaSalle Language Academy', 'count': 1}
    {'_id': 'Orrington Elementary School', 'count': 1}
    {'_id': 'Lincoln Prarie School', 'count': 1}
    {'_id': 'Hoover Elementary School', 'count': 1}
    {'_id': 'Avondale Public School', 'count': 1}
    {'_id': 'Tarkington Elementary School', 'count': 1}
    {'_id': 'Prieto School', 'count': 1}
    {'_id': 'Hanson Park Elementary School', 'count': 1}
    {'_id': 'Seven Holy Founders School', 'count': 1}
    {'_id': 'Arie Crown Hebrew Day School', 'count': 1}
    {'_id': 'Joan Dachs Bais Yaakov', 'count': 1}
    {'_id': 'Mosaic Early Childhood Center', 'count': 1}
    {'_id': 'Ida Crown Jewish Academy', 'count': 1}
    {'_id': 'Iroquois Community School', 'count': 1}
    {'_id': 'Wilbur Wright Middle School', 'count': 1}
    {'_id': 'Munster High School', 'count': 1}
    {'_id': 'Lucia Goodwin Elementary School', 'count': 1}
    {'_id': 'Komarek Elementary School', 'count': 1}
    {'_id': 'Bethany Lutheran School', 'count': 1}
    {'_id': 'Elmwood Elementary School', 'count': 1}
    {'_id': 'Deerfield High School', 'count': 1}
    {'_id': 'Music Institute of Chicago', 'count': 1}
    {'_id': 'John Hancock School', 'count': 1}
    {'_id': 'McKay Elementary School', 'count': 1}
    {'_id': 'Everett Dirksen Elementary School', 'count': 1}
    {'_id': 'Sutherland Elementary School', 'count': 1}
    {'_id': 'Beethoven Elementary School', 'count': 1}
    {'_id': 'Clay Elementary School', 'count': 1}
    {'_id': 'Abe Lincoln Elementary School', 'count': 1}
    {'_id': 'Herzl Junior College', 'count': 1}
    {'_id': 'Rogers Park Montessori School', 'count': 1}
    {'_id': 'Glen Crest Junior High School', 'count': 1}
    {'_id': 'Briar Glen Elementary School', 'count': 1}
    {'_id': 'McPherson Elementary School', 'count': 1}
    {'_id': 'Saint Augustine College', 'count': 1}
    {'_id': 'Abbott Elementary School', 'count': 1}
    {'_id': 'Drake Elementary School', 'count': 1}
    {'_id': 'Beebe Elementary School', 'count': 1}
    {'_id': 'Carl Sandburg Junior High School', 'count': 1}
    {'_id': 'Saints Peter and Paul Parochial School', 'count': 1}
    {'_id': 'Humboldt Park Vocational Education Center', 'count': 1}
    {'_id': 'Bowen High School', 'count': 1}
    {'_id': 'Timber Trails Elementary', 'count': 1}
    {'_id': 'Saint Thomas of Villanova School', 'count': 1}
    {'_id': 'Dundee-Crown High School', 'count': 1}
    {'_id': 'Howard B. Thomas Elementary School', 'count': 1}
    {'_id': 'Miriam G. Canter Middle School', 'count': 1}
    {'_id': 'Harrison Street Elementary School', 'count': 1}
    {'_id': 'Chappell School', 'count': 1}
    {'_id': 'Glenwood School - Rathje Campus', 'count': 1}
    {'_id': 'Hibbard Elementary School', 'count': 1}
    {'_id': 'Haines Middle School', 'count': 1}
    {'_id': 'Whitney Elementary School', 'count': 1}
    {'_id': 'Thompson Middle School', 'count': 1}
    {'_id': 'Westchester Intermediate School', 'count': 1}
    {'_id': 'John Jay Elementary School', 'count': 1}
    {'_id': 'Dwyer Elementary School', 'count': 1}
    {'_id': 'Country Trails Elementary School', 'count': 1}
    {'_id': 'Ellis Middle School', 'count': 1}
    {'_id': 'Prairie View Grade School', 'count': 1}
    {'_id': 'Prairie Knolls Middle School', 'count': 1}
    {'_id': 'Dunton School', 'count': 1}
    {'_id': 'Avalon Park School', 'count': 1}
    {'_id': 'Juliette Low Elementary School', 'count': 1}
    {'_id': 'Larkin High School', 'count': 1}
    {'_id': 'Prairie Ridge High School', 'count': 1}
    {'_id': 'Kimball Hill Elementary School', 'count': 1}
    {'_id': 'Elmer H Franzen Elementary School', 'count': 1}
    {'_id': 'Dever Elementary School', 'count': 1}
    {'_id': 'Holmes Junior High School', 'count': 1}
    {'_id': 'Forest View Elementary School', 'count': 1}
    {'_id': 'Gilberts Elementary School', 'count': 1}
    {'_id': 'Huntley High School', 'count': 1}
    {'_id': 'Rosary High School', 'count': 1}
    {'_id': 'Henry W Cowherd Middle School', 'count': 1}
    {'_id': 'Allen Elementary School', 'count': 1}
    {'_id': 'Shoop Elementary School', 'count': 1}
    {'_id': 'St Mary Magdalene School', 'count': 1}
    {'_id': 'T E Culbertson Elementary School', 'count': 1}
    {'_id': 'Gross Elementary School', 'count': 1}
    {'_id': 'Romeoville High School', 'count': 1}
    {'_id': 'Kenyon Woods Middle School', 'count': 1}
    {'_id': 'Fort Dearborn Elementary School', 'count': 1}
    {'_id': 'Georgetown Elementary School', 'count': 1}
    {'_id': 'Plainfield North High School', 'count': 1}
    {'_id': 'Plainfield Academy', 'count': 1}
    {'_id': 'Highcrest Middle School', 'count': 1}
    {'_id': 'Troy Heritage Trail School', 'count': 1}
    {'_id': 'Beasey Academy', 'count': 1}
    {'_id': 'Charles Reed Elementary School', 'count': 1}
    {'_id': 'Plainfield South High School', 'count': 1}
    {'_id': 'Jehovah School', 'count': 1}
    {'_id': 'Dundee Middle School', 'count': 1}
    {'_id': 'Lakewood Falls Elementary School', 'count': 1}
    {'_id': 'Oswego East High School', 'count': 1}
    {'_id': 'Oswego High School', 'count': 1}
    {'_id': 'Saint Marie Goretti School', 'count': 1}
    {'_id': 'John F. Kennedy Elementary School', 'count': 1}
    {'_id': 'Waubonsie Valley High School', 'count': 1}
    {'_id': 'Jose de Diego Community Academy', 'count': 1}
    {'_id': 'Margaret Mead Junior High School', 'count': 1}
    {'_id': 'Nerge School', 'count': 1}
    {'_id': 'Ranch View Elementary School', 'count': 1}
    {'_id': 'Goodrich Elementary School', 'count': 1}
    {'_id': 'Naperville North High School', 'count': 1}
    {'_id': 'Madison Junior High School', 'count': 1}
    {'_id': 'Vernon Hills High School', 'count': 1}
    {'_id': 'MacArthur Elementary School', 'count': 1}
    {'_id': 'Friendship Junior High School', 'count': 1}
    {'_id': 'Bass School', 'count': 1}
    {'_id': 'Academy of Sciences', 'count': 1}
    {'_id': 'Troy Craughwell School', 'count': 1}
    {'_id': 'Union School Dist 81', 'count': 1}
    {'_id': 'Troy Hofer Elementary School', 'count': 1}
    {'_id': 'Troy Shorewood School', 'count': 1}
    {'_id': 'Plainfield Elementary School', 'count': 1}
    {'_id': 'Maine West High School', 'count': 1}
    {'_id': 'Saint Patrick High School', 'count': 1}
    {'_id': 'Proviso School', 'count': 1}
    {'_id': 'Glenbrook South High School', 'count': 1}
    {'_id': 'Jane Stenson Elementary School', 'count': 1}
    {'_id': 'Senn Metro Academy', 'count': 1}
    {'_id': 'Lillstreet Art Center', 'count': 1}
    {'_id': 'Portage Park Elementary School', 'count': 1}
    {'_id': 'Ballard School', 'count': 1}
    {'_id': 'Notre Dame High School for Boys', 'count': 1}
    {'_id': 'Nicholson School for Science and Math', 'count': 1}
    {'_id': 'Burbank Elementary School', 'count': 1}
    {'_id': 'Steeple Run Elementary School', 'count': 1}
    {'_id': 'J.N. Thorp Elementary School', 'count': 1}
    {'_id': 'Fairview South Elementary School', 'count': 1}
    {'_id': 'Fasman Yeshiva High School', 'count': 1}
    {'_id': 'Aldridge Elementary School', 'count': 1}
    {'_id': 'Saint Mary of the Woods School', 'count': 1}
    {'_id': 'Pullman Elementary School', 'count': 1}
    {'_id': 'Christopher School', 'count': 1}
    {'_id': 'Sawyer Elementary School', 'count': 1}
    {'_id': 'Eberhart School', 'count': 1}
    {'_id': 'Solon Robinson Elementary School', 'count': 1}
    {'_id': 'Chute Middle School', 'count': 1}
    {'_id': 'Cristo Rey Jesuit High School', 'count': 1}
    {'_id': 'Ryerson Elementary School', 'count': 1}
    {'_id': 'Glenbard South High School', 'count': 1}
    {'_id': 'Foreman High School', 'count': 1}
    {'_id': 'Chicago Latvian Krisjanis Barons School', 'count': 1}
    {'_id': 'Roy Elementary School', 'count': 1}
    {'_id': 'West Leyden High School', 'count': 1}
    {'_id': 'Mannheim School District 83 Admin Center', 'count': 1}
    {'_id': 'Mannhem Middle School', 'count': 1}
    {'_id': 'Walter Payton College Prep', 'count': 1}
    {'_id': 'Roycemore School', 'count': 1}
    {'_id': 'Jenner Academy for the Arts', 'count': 1}
    {'_id': 'John Middleton Elementary School', 'count': 1}
    {'_id': 'Schurz High School', 'count': 1}
    {'_id': 'Elmwood Park High School', 'count': 1}
    {'_id': 'Oakton Elementary School', 'count': 1}
    {'_id': 'De La Salle Institute', 'count': 1}
    {'_id': 'Oscar F. Mayer Elementary School', 'count': 1}
    {'_id': 'Hawthorne Scholastic Academy', 'count': 1}
    {'_id': 'Murphy Elementary School', 'count': 1}
    {'_id': 'Immaculate Heart of Mary School', 'count': 1}
    {'_id': 'Cleveland Elementary School', 'count': 1}
    {'_id': 'Gwendolyn Brooks Preparatory Academy', 'count': 1}
    {'_id': 'Blaine Elementary School', 'count': 1}
    {'_id': 'Bateman Elementary School', 'count': 1}
    {'_id': 'Disney Magnet Elementary School', 'count': 1}
    {'_id': 'Edgebrook Elementary School', 'count': 1}
    {'_id': 'Haugan Elementary School', 'count': 1}
    {'_id': 'Cecil A. Partee Transitional School', 'count': 1}
    {'_id': 'Waters Elementary School', 'count': 1}
    {'_id': 'Beaubien Elementary School', 'count': 1}
    {'_id': 'Costello School', 'count': 1}
    {'_id': 'Oliver McCracken Middle School', 'count': 1}
    {'_id': 'East Prairie Elementary School', 'count': 1}
    {'_id': 'Thomas Edison Elementary School', 'count': 1}
    {'_id': 'Niles North High School', 'count': 1}
    {'_id': 'New Trier High School', 'count': 1}
    {'_id': 'Saint Zachary School', 'count': 1}
    {'_id': 'Steger District Office', 'count': 1}
    {'_id': 'Columbia Central Middle School', 'count': 1}
    {'_id': 'Rise Chicago Heights School', 'count': 1}
    {'_id': 'SPEED', 'count': 1}
    {'_id': 'John L. Lukanic Middle School', 'count': 1}
    {'_id': 'Beverly Skoff Elementary', 'count': 1}
    {'_id': 'Lakeview Junior High School', 'count': 1}
    {'_id': 'Mackeben Elementary School', 'count': 1}
    {'_id': 'Robinson B Murphy Junior High School ', 'count': 1}
    {'_id': 'St Patrick Catholic School', 'count': 1}
    {'_id': 'Batavia School District 101 Administration Center', 'count': 1}
    {'_id': 'Roosevelt Middle School', 'count': 1}
    {'_id': 'Churchville Junior High School', 'count': 1}
    {'_id': 'South Loop Montessori School', 'count': 1}
    {'_id': 'Stuart School of Business', 'count': 1}
    {'_id': 'Dorothy Delacey Family Education Center', 'count': 1}
    {'_id': 'Saint Constance School', 'count': 1}
    {'_id': 'Bell-Graham Elementary', 'count': 1}
    {'_id': 'Westfield Community School', 'count': 1}
    {'_id': 'Algonquin Lakes Elementary', 'count': 1}
    {'_id': 'Hoover Wood Elementary', 'count': 1}
    {'_id': 'Harper High School', 'count': 1}
    {'_id': 'Louise White Elementary', 'count': 1}
    {'_id': 'Mill Creek Elementary', 'count': 1}
    {'_id': 'Lincoln Elementary', 'count': 1}
    {'_id': 'Nature Ridge Elementary', 'count': 1}
    {'_id': 'Corron Elementary', 'count': 1}
    {'_id': 'Gary Corner Youth Center', 'count': 1}
    {'_id': 'Eakin School', 'count': 1}
    {'_id': 'School No. 6', 'count': 1}
    {'_id': 'Kaneland John Stewart Elementary', 'count': 1}
    {'_id': 'Kaneland Blackberry Creek Elementary', 'count': 1}
    {'_id': 'Kaneland McDole Elementary', 'count': 1}
    {'_id': 'Heartland Elementary', 'count': 1}
    {'_id': 'Troy Middle School', 'count': 1}
    {'_id': 'Grand Prairie School', 'count': 1}
    {'_id': 'Homestead Elementary School', 'count': 1}
    {'_id': 'Miller Public School (historical)', 'count': 1}
    {'_id': 'Cuffe Elementary', 'count': 1}
    {'_id': 'Hurley Elementary School', 'count': 1}
    {'_id': 'Chapel of the Dunes School', 'count': 1}
    {'_id': 'Douglas MacArthur Elementary School', 'count': 1}
    {'_id': 'Woodson Elementary School', 'count': 1}
    {'_id': 'Hobart High School', 'count': 1}
    {'_id': 'Ivy Technical State College Northwest', 'count': 1}
    {'_id': 'Seventh Day Adventist School (historical)', 'count': 1}
    {'_id': 'Saint Monica School', 'count': 1}
    {'_id': 'Calumet College of Saint Joseph', 'count': 1}
    {'_id': 'Hammond Baptist Grade School', 'count': 1}
    {'_id': "Saint Joseph's College (historical)", 'count': 1}
    {'_id': 'Three Rivers School', 'count': 1}
    {'_id': 'Saint Francisci School (historical)', 'count': 1}
    {'_id': 'Pope John XXIII School', 'count': 1}
    {'_id': 'Saint Anthanasius School', 'count': 1}
    {'_id': 'Holy Trinity Hungarian Roman Catholic School', 'count': 1}
    {'_id': 'Assumption School of the Blessed Virgin', 'count': 1}
    {'_id': 'Special Education Learning Facility', 'count': 1}
    {'_id': 'Technical High School', 'count': 1}
    {'_id': 'Willowcreek Middle School', 'count': 1}
    {'_id': 'Calumet Baptist Schools', 'count': 1}
    {'_id': 'Merkley School', 'count': 1}
    {'_id': 'Providence Center', 'count': 1}
    {'_id': 'Lake Ridge Middle School', 'count': 1}
    {'_id': 'Hyles-Anderson College', 'count': 1}
    {'_id': 'Paul Saylor Elementary School', 'count': 1}
    {'_id': 'Saint Judes School (historical)', 'count': 1}
    {'_id': 'Saint Johns Seminary (historical)', 'count': 1}
    {'_id': 'Haan School (historical)', 'count': 1}
    {'_id': 'Sawyer College', 'count': 1}
    {'_id': 'Porter Lakes School', 'count': 1}
    {'_id': 'Valparaiso High School', 'count': 1}
    {'_id': 'Michael Grimmer Middle School', 'count': 1}
    {'_id': 'Kennedy-King Middle School', 'count': 1}
    {'_id': 'Portage Adult Education Center', 'count': 1}
    {'_id': 'Elm Elementary School', 'count': 1}
    {'_id': 'Wallace School', 'count': 1}
    {'_id': 'Highland Christian Academy', 'count': 1}
    {'_id': 'Harrison Middle School', 'count': 1}
    {'_id': 'Portage High School', 'count': 1}
    {'_id': 'Ready School', 'count': 1}
    {'_id': 'Lake County Development Center', 'count': 1}
    {'_id': 'Gavit School', 'count': 1}
    {'_id': 'Beiriger Elementary School', 'count': 1}
    {'_id': 'Ridgewood High School', 'count': 1}
    {'_id': 'Charles N Scott Middle School', 'count': 1}
    {'_id': 'Hammond School', 'count': 1}
    {'_id': 'McKinley School', 'count': 1}
    {'_id': 'Daniel Hale Williams Elementary School', 'count': 1}
    {'_id': 'Daniel Webster Elementary School', 'count': 1}
    {'_id': 'Lew Wallace High School', 'count': 1}
    {'_id': 'John H Vohr Elementary School', 'count': 1}
    {'_id': 'Tolleston Middle School', 'count': 1}
    {'_id': 'Saint Mark School', 'count': 1}
    {'_id': 'Richmond Intermediate School', 'count': 1}
    {'_id': 'Saint Bridget School', 'count': 1}
    {'_id': 'South Elgin High School', 'count': 1}
    {'_id': 'Ridge View Elementary School', 'count': 1}
    {'_id': 'Dunbar-Pulaski Middle School', 'count': 1}
    {'_id': 'Carl J Polk Elementary School', 'count': 1}
    {'_id': 'Oakdale Christian Academy', 'count': 1}
    {'_id': 'Pittman Square Elementary School', 'count': 1}
    {'_id': 'Vanderpoel Magnet School', 'count': 1}
    {'_id': 'Arbury Hills Elementary School', 'count': 1}
    {'_id': 'Arthur P Melton Elementary School', 'count': 1}
    {'_id': 'Horace Mann Elementary School', 'count': 1}
    {'_id': 'Lincoln Achievement Center', 'count': 1}
    {'_id': 'Kuny Elementary School', 'count': 1}
    {'_id': 'Ethel R Jones Elementary School', 'count': 1}
    {'_id': 'Washington Irving Elementary School', 'count': 1}
    {'_id': 'Benjamin Harrison Elementary School', 'count': 1}
    {'_id': 'Alexander Hamilton Elementary School', 'count': 1}
    {'_id': 'Bottles to Books', 'count': 1}
    {'_id': 'William Fegely Middle School', 'count': 1}
    {'_id': 'Henry S Evans Elementary School', 'count': 1}
    {'_id': 'George Earle Elementary School', 'count': 1}
    {'_id': 'Westcott Elementary School', 'count': 1}
    {'_id': 'David O Duncan Elementary School', 'count': 1}
    {'_id': 'Charles R Drew Elementary School', 'count': 1}
    {'_id': 'Frederick Douglass Elementary School', 'count': 1}
    {'_id': 'James Madison School', 'count': 1}
    {'_id': 'Chase Alternative Middle School', 'count': 1}
    {'_id': 'Mary M Bethune Early Child Development Center', 'count': 1}
    {'_id': 'Jane Addams School', 'count': 1}
    {'_id': 'Alfred Beckman Middle School', 'count': 1}
    {'_id': 'Grace McWayne Elementary', 'count': 1}
    {'_id': 'Benjamin Banneker Elementary School', 'count': 1}
    {'_id': 'Westmont Junior High School', 'count': 1}
    {'_id': 'George Bibich Elementary School', 'count': 1}
    {'_id': 'Hobart Middle School', 'count': 1}
    {'_id': 'Griffith Senior High School', 'count': 1}
    {'_id': 'Black Oak Elementary School', 'count': 1}
    {'_id': 'Mades-Johnstone School', 'count': 1}
    {'_id': 'Schiesher Elementary School', 'count': 1}
    {'_id': 'Schafer Elementary School', 'count': 1}
    {'_id': 'Nancy Hill Elementary School', 'count': 1}
    {'_id': 'Sarah Adams Elementary School', 'count': 1}
    {'_id': 'Sandburg Junior High School', 'count': 1}
    {'_id': 'Saint Bartholomew School', 'count': 1}
    {'_id': 'Archbishop Romer School', 'count': 1}
    {'_id': 'Medinah Primary School', 'count': 1}
    {'_id': 'Gads Hill Center Social Settlement', 'count': 1}
    {'_id': 'Rickover Junior High School', 'count': 1}
    {'_id': 'Price Elementary School', 'count': 1}
    {'_id': 'Sandridge School', 'count': 1}
    {'_id': 'Magic Mirror Learning Center', 'count': 1}
    {'_id': 'Crete-Monee High School', 'count': 1}
    {'_id': 'Indiana Elementary School', 'count': 1}
    {'_id': 'Chicago Institute of Technology', 'count': 1}
    {'_id': 'Protestant Reform School', 'count': 1}
    {'_id': 'Highland School', 'count': 1}
    {'_id': 'Hinsdale South High School', 'count': 1}
    {'_id': 'Saukview School', 'count': 1}
    {'_id': 'Algonquin Elementary School', 'count': 1}
    {'_id': 'Saint Liborius School', 'count': 1}
    {'_id': 'Montessori School - Near North', 'count': 1}
    {'_id': 'Saint Cletus School', 'count': 1}
    {'_id': 'Memorial Junior High School', 'count': 1}
    {'_id': 'York Community High School', 'count': 1}
    {'_id': 'Winston Churchill Elementary School', 'count': 1}
    {'_id': 'The Day School', 'count': 1}
    {'_id': "Saint Andrew's Lutheran School", 'count': 1}
    {'_id': 'Northern Seminary', 'count': 1}
    {'_id': 'Blair School', 'count': 1}
    {'_id': 'First Wesley Academy', 'count': 1}
    {'_id': 'Oak School', 'count': 1}
    {'_id': 'Old Mill School', 'count': 1}
    {'_id': 'Saint Josephs Seminary', 'count': 1}
    {'_id': 'Langston Hughes Elementary School', 'count': 1}
    {'_id': 'Jacques Marquette Elementary School', 'count': 1}
    {'_id': 'Southridge Elementary School', 'count': 1}
    {'_id': 'Lanier School (historical)', 'count': 1}
    {'_id': 'Hammerschmidt School', 'count': 1}
    {'_id': 'Queen of All Saints School', 'count': 1}
    {'_id': 'Glenbard West High School', 'count': 1}
    {'_id': 'Saint Isaac Jogues School', 'count': 1}
    {'_id': 'Whiting Junior-Senior High School', 'count': 1}
    {'_id': 'Westmoor Elementary School', 'count': 1}
    {'_id': 'Bromberek School', 'count': 1}
    {'_id': 'Sacred Heart Seminary', 'count': 1}
    {'_id': 'Thompson School', 'count': 1}
    {'_id': 'Domeier School', 'count': 1}
    {'_id': 'Ninos Heroes Community Academy', 'count': 1}
    {'_id': 'Palos South Middle School', 'count': 1}
    {'_id': 'Walden Elementary School', 'count': 1}
    {'_id': 'Twinbrook Elementary School', 'count': 1}
    {'_id': 'Ridge Circle Elementary School', 'count': 1}
    {'_id': 'Nixon Elementary School', 'count': 1}
    {'_id': 'Romper Room Day Care and Kindergarten', 'count': 1}
    {'_id': 'Green Valley School', 'count': 1}
    {'_id': 'Wheeler High School', 'count': 1}
    {'_id': 'Gower School', 'count': 1}
    {'_id': 'Tilden High School', 'count': 1}
    {'_id': 'Westdale Elementary School', 'count': 1}
    {'_id': 'Wheaton Christian Grammar School', 'count': 1}
    {'_id': 'River Forest Elementary School', 'count': 1}
    {'_id': 'Jackson Elementary School', 'count': 1}
    {'_id': 'Sunny Hill Elementary School', 'count': 1}
    {'_id': 'Farragut Career Academy', 'count': 1}
    {'_id': 'Todd Hall Elementary School', 'count': 1}
    {'_id': 'Rasmussen College - Aurora Campus', 'count': 1}
    {'_id': 'J H Freeman Elementary School', 'count': 1}
    {'_id': 'Anna McDonald Elementary School', 'count': 1}
    {'_id': 'Adlai E Stevenson High School', 'count': 1}
    {'_id': 'Cornerstone Christian School', 'count': 1}
    {'_id': 'Tennyson School', 'count': 1}
    {'_id': 'Willow Grove Elementary School', 'count': 1}
    {'_id': 'Parkwood Elementary School', 'count': 1}
    {'_id': 'Golf Middle School and Technology Center', 'count': 1}
    {'_id': 'Taft Elementary School', 'count': 1}
    {'_id': 'Rudolph Learning Center', 'count': 1}
    {'_id': 'Sawyer Business College', 'count': 1}
    {'_id': 'Albert Einstein Elementary School', 'count': 1}
    {'_id': 'Saint Gregory Preschool', 'count': 1}
    {'_id': 'Glenbard East High School', 'count': 1}
    {'_id': 'Mill Street Elementary School', 'count': 1}
    {'_id': 'Saint Hubert School', 'count': 1}
    {'_id': 'Thayer J Hill Middle School', 'count': 1}
    {'_id': 'Springman Junior High School', 'count': 1}
    {'_id': 'Brownie Hill School', 'count': 1}
    {'_id': 'Huff Elementary School', 'count': 1}
    {'_id': 'Whitman School', 'count': 1}
    {'_id': 'Cooper Elementary School', 'count': 1}
    {'_id': 'Louise White Elementary School', 'count': 1}
    {'_id': 'Sauk Elementary School', 'count': 1}
    {'_id': 'Higgins School', 'count': 1}
    {'_id': 'West Ridge School', 'count': 1}
    {'_id': 'Springbrook Elementary School', 'count': 1}
    {'_id': 'Walther School', 'count': 1}
    {'_id': 'James Ward Elementary School', 'count': 1}
    {'_id': 'McAuliffe Elementary School', 'count': 1}
    {'_id': 'Crossroads Elementary School', 'count': 1}
    {'_id': 'Juan Inez de la Cruz School', 'count': 1}
    {'_id': 'W W Walker Elementary School', 'count': 1}
    {'_id': 'W S Beaupre Elementary School', 'count': 1}
    {'_id': 'Woodland Heights Elementary School', 'count': 1}
    {'_id': 'Fairmount Elementary School', 'count': 1}
    {'_id': 'Sisters of Nazareth School', 'count': 1}
    {'_id': 'Cass Junior High School', 'count': 1}
    {'_id': 'Cambridge Lakes Learning Center', 'count': 1}
    {'_id': 'Cornell School', 'count': 1}
    {'_id': 'Morton College', 'count': 1}
    {'_id': 'Christ the King Seminary', 'count': 1}
    {'_id': 'Saint Marys of the Lake Seminary', 'count': 1}
    {'_id': 'Home Elementary School', 'count': 1}
    {'_id': 'Franklin Middle School', 'count': 1}
    {'_id': 'Lions Park Elementary School', 'count': 1}
    {'_id': 'Santa Maria School', 'count': 1}
    {'_id': 'Green Street School', 'count': 1}
    {'_id': 'Pierce Downer Elementary School', 'count': 1}
    {'_id': 'Olive Elementary School', 'count': 1}
    {'_id': 'Sculptors Guild', 'count': 1}
    {'_id': 'Edison Elementary School', 'count': 1}
    {'_id': "Young Women's Leadership Charter School", 'count': 1}
    {'_id': 'Vaughn Occupational High School', 'count': 1}
    {'_id': 'Trinity College', 'count': 1}
    {'_id': 'Laren School', 'count': 1}
    {'_id': 'Trinity Christian School', 'count': 1}
    {'_id': 'Washington Middle School', 'count': 1}
    {'_id': 'Benjamin School', 'count': 1}
    {'_id': 'Maryville Center for Children', 'count': 1}
    {'_id': 'Wilmot School', 'count': 1}
    {'_id': 'Strassburg Elementary School', 'count': 1}
    {'_id': 'Lincoln-Way East High School', 'count': 1}
    {'_id': 'Hanover Central Junior/Senior High School', 'count': 1}
    {'_id': 'Illinois Masonic Medical Center School of Nursing', 'count': 1}
    {'_id': 'Standard School', 'count': 1}
    {'_id': 'Saint Mary of Celle School', 'count': 1}
    {'_id': 'Thorn Grove School', 'count': 1}
    {'_id': 'Maryville City of Youth', 'count': 1}
    {'_id': 'Rotolo Middle School', 'count': 1}
    {'_id': 'Frankfort School', 'count': 1}
    {'_id': 'Saint Catherine of Alexandria School', 'count': 1}
    {'_id': 'Decatur Classical School', 'count': 1}
    {'_id': 'Porsser Vocational High School', 'count': 1}
    {'_id': 'Thornton High School', 'count': 1}
    {'_id': 'Saint Cyprian School', 'count': 1}
    {'_id': 'Thomas Middle School', 'count': 1}
    {'_id': 'Hitch Elementary School', 'count': 1}
    {'_id': 'Saint Linus School', 'count': 1}
    {'_id': 'Saint Luke School', 'count': 1}
    {'_id': 'Todd Elementary School', 'count': 1}
    {'_id': 'Marion Hills Seminary', 'count': 1}
    {'_id': 'Meadow Glens Elementary School', 'count': 1}
    {'_id': 'Saint Louis School', 'count': 1}
    {'_id': 'Saint Mary Perpetual Help High School', 'count': 1}
    {'_id': "Saint Lawrence-O'Toole School", 'count': 1}
    {'_id': 'Wheaton College', 'count': 1}
    {'_id': 'Our Saviour Lutheran School', 'count': 1}
    {'_id': 'Saint Matthew Lutheran School', 'count': 1}
    {'_id': 'Saint Michael High School', 'count': 1}
    {'_id': 'Maplewood School', 'count': 1}
    {'_id': 'Copland Manor Elementary School', 'count': 1}
    {'_id': 'Thomas School', 'count': 1}
    {'_id': 'Scott Joplin High School', 'count': 1}
    {'_id': 'Faulkner School', 'count': 1}
    {'_id': 'Downers Grove South High School', 'count': 1}
    {'_id': 'Mechanics Grove Elementary School', 'count': 1}
    {'_id': 'Saint Maurice School', 'count': 1}
    {'_id': 'Crickets Child and Infant Daycare Center', 'count': 1}
    {'_id': 'Howe Elementary School', 'count': 1}
    {'_id': 'Butler Junior High School', 'count': 1}
    {'_id': 'Saint Patricia School', 'count': 1}
    {'_id': 'Evergreen Park Elementary School', 'count': 1}
    {'_id': 'Metropolitan Business College', 'count': 1}
    {'_id': 'West Chicago Community High School', 'count': 1}
    {'_id': 'Saint Michael Central High School', 'count': 1}
    {'_id': 'Our Lady of Good Counsel School', 'count': 1}
    {'_id': 'Conley Elementary School', 'count': 1}
    {'_id': 'Saint Odilo School', 'count': 1}
    {'_id': 'Richard J Daley College', 'count': 1}
    {'_id': 'Guerin Prep High School', 'count': 1}
    {'_id': 'Presbyterian Theological Seminary', 'count': 1}
    {'_id': 'Ogden Elementary School', 'count': 1}
    {'_id': 'Stone Elementary School', 'count': 1}
    {'_id': 'St Stanislaus School', 'count': 1}
    {'_id': 'Evanston Township High School', 'count': 1}
    {'_id': 'West Northfield School', 'count': 1}
    {'_id': 'Jewel Middle School', 'count': 1}
    {'_id': 'Saint Simon School', 'count': 1}
    {'_id': 'Steindler School', 'count': 1}
    {'_id': 'Aurora Central High School', 'count': 1}
    {'_id': 'Horace Mann School', 'count': 1}
    {'_id': 'Harvard Elementary School', 'count': 1}
    {'_id': 'IIT Institute of Design', 'count': 1}
    {'_id': 'Saint Raymond De Penafort School', 'count': 1}
    {'_id': 'Saint Kilian School', 'count': 1}
    {'_id': 'Holy Trinity High School', 'count': 1}
    {'_id': 'Saint Symphorosa School', 'count': 1}
    {'_id': 'Divine Infant School', 'count': 1}
    {'_id': "O'Keefe Elementary School", 'count': 1}
    {'_id': 'Saint Albert School', 'count': 1}
    {'_id': 'Coles Elementary School', 'count': 1}
    {'_id': 'Hillel Torah North Suburban Day School', 'count': 1}
    {'_id': 'Sunset Ridge Elementary School', 'count': 1}
    {'_id': 'Peck Elementary School', 'count': 1}
    {'_id': 'Oak Park Elementary School', 'count': 1}
    {'_id': 'Saint Stephen School', 'count': 1}
    {'_id': 'Prairieview Elementary School', 'count': 1}
    {'_id': 'Stanley Hall School', 'count': 1}
    {'_id': 'Beth Israel School', 'count': 1}
    {'_id': 'Saints Peter and Paul High School', 'count': 1}
    {'_id': 'Saint Stanislaus School', 'count': 1}
    {'_id': 'Lane School', 'count': 1}
    {'_id': 'Joseph Academy', 'count': 1}
    {'_id': 'Shedd School', 'count': 1}
    {'_id': 'Fuller Elementary School', 'count': 1}
    {'_id': 'Richland Elementary School', 'count': 1}
    {'_id': 'Auburn-Gresham Preschool', 'count': 1}
    {'_id': 'Sumner Elementary School', 'count': 1}
    {'_id': 'Robert Frost School', 'count': 1}
    {'_id': 'J W Riley Elementary School', 'count': 1}
    {'_id': 'Dogwood School', 'count': 1}
    {'_id': 'Roberts Park School', 'count': 1}
    {'_id': 'Garnett School', 'count': 1}
    {'_id': 'Bontemps Elementary School', 'count': 1}
    {'_id': 'La Vergne School', 'count': 1}
    {'_id': 'Saint Ladislaus School', 'count': 1}
    {'_id': 'Bridgeport Academy West', 'count': 1}
    {'_id': 'Shiloh Academy', 'count': 1}
    {'_id': 'Sharp Corner School', 'count': 1}
    {'_id': 'Bridge School', 'count': 1}
    {'_id': "Saint Edmund's Episcopal Parochial School", 'count': 1}
    {'_id': 'Gregory Elementary School', 'count': 1}
    {'_id': 'Graves School', 'count': 1}
    {'_id': 'Nob Hill Elementary School', 'count': 1}
    {'_id': 'Bridgeport Academy North', 'count': 1}
    {'_id': 'Serena Hills Elementary School', 'count': 1}
    {'_id': 'Winston School', 'count': 1}
    {'_id': 'Brook Forest Elementary School', 'count': 1}
    {'_id': 'Illinois Barber College', 'count': 1}
    {'_id': "Saint Pascal's School", 'count': 1}
    {'_id': 'Reinberg Elementary School', 'count': 1}
    {'_id': 'Burr Elementary School', 'count': 1}
    {'_id': 'Sieden Prairie Elementary School', 'count': 1}
    {'_id': 'Naper Elementary School', 'count': 1}
    {'_id': 'James Hart Junior High School', 'count': 1}
    {'_id': 'C F Simmons Middle School', 'count': 1}
    {'_id': 'Shepard School', 'count': 1}
    {'_id': 'Siena High School', 'count': 1}
    {'_id': 'Fox Meadow Elementary', 'count': 1}
    {'_id': 'Saint Rita of Cascia School', 'count': 1}
    {'_id': 'Main Street School', 'count': 1}
    {'_id': 'Notre Dame High School', 'count': 1}
    {'_id': 'South Prospect Heights School', 'count': 1}
    {'_id': 'South Shore High School', 'count': 1}
    {'_id': 'Woodgate Elementary School', 'count': 1}
    {'_id': 'Saint Ethelreda School', 'count': 1}
    {'_id': 'Saint Colette School', 'count': 1}
    {'_id': 'Chicago International Charter School Longwood', 'count': 1}
    {'_id': 'Mozart Elementary School', 'count': 1}
    {'_id': 'Green Garden Elementary School', 'count': 1}
    {'_id': 'Hammond High School', 'count': 1}
    {'_id': 'IC Catholic Prep High School', 'count': 1}
    {'_id': 'Merry Go Round Nursery School', 'count': 1}
    {'_id': 'Hubbard Trail Junior High School', 'count': 1}
    {'_id': 'Oak Villa School', 'count': 1}
    {'_id': 'Richards High School', 'count': 1}
    {'_id': 'Saint Casimir High School', 'count': 1}
    {'_id': 'Ontarioville Elementary School', 'count': 1}
    {'_id': 'Norwood Park Elementary School', 'count': 1}
    {'_id': 'Saint Meland School', 'count': 1}
    {'_id': 'Saint Camillus School', 'count': 1}
    {'_id': 'Saint Jogues School', 'count': 1}
    {'_id': 'Hometown Elementary School', 'count': 1}
    {'_id': 'Jackson Language Academy', 'count': 1}
    {'_id': 'Martin Luther Educational Center', 'count': 1}
    {'_id': 'Saint Pius School', 'count': 1}
    {'_id': 'Basic Beginnings', 'count': 1}
    {'_id': 'Saint Blase School', 'count': 1}
    {'_id': 'Corliss High School', 'count': 1}
    {'_id': 'Transfiguration School', 'count': 1}
    {'_id': 'Saint Bernard School', 'count': 1}
    {'_id': 'Saint Beatrice School', 'count': 1}
    {'_id': 'W M Hadley Junior High School', 'count': 1}
    {'_id': "Saint John's Evangelical Lutheran School (historical)", 'count': 1}
    {'_id': 'Skokie Junior High School', 'count': 1}
    {'_id': 'Spring Wood Middle School', 'count': 1}
    {'_id': 'Calvary Academy', 'count': 1}
    {'_id': 'Luther High School', 'count': 1}
    {'_id': 'Cross School', 'count': 1}
    {'_id': 'Rupley Elementary School', 'count': 1}
    {'_id': 'Saint Kieran School', 'count': 1}
    {'_id': 'Saint Eulalia School', 'count': 1}
    {'_id': 'Yeshiva Migdal Torah', 'count': 1}
    {'_id': 'Saint Ferdinand School', 'count': 1}
    {'_id': 'Alcott Elementary School', 'count': 1}
    {'_id': 'East School', 'count': 1}
    {'_id': 'Saint Felicitas School', 'count': 1}
    {'_id': 'Sheridan School', 'count': 1}
    {'_id': 'Saint Gall School', 'count': 1}
    {'_id': 'Saint Dorothy School', 'count': 1}
    {'_id': 'Mollison Elementary School', 'count': 1}
    {'_id': 'Cook County Graduate School of Medicine', 'count': 1}
    {'_id': 'Henry Winkelman Elementary School', 'count': 1}
    {'_id': 'Saint Domitilla School', 'count': 1}
    {'_id': 'Hickory Bend Elementary School', 'count': 1}
    {'_id': 'Bond Elementary School', 'count': 1}
    {'_id': 'South Middle School', 'count': 1}
    {'_id': 'Saint Anthony School', 'count': 1}
    {'_id': 'Hoyne Elementary School', 'count': 1}
    {'_id': 'Midwest Academy', 'count': 1}
    {'_id': 'Sleepy Hollow Elementary School', 'count': 1}
    {'_id': 'Roxana School', 'count': 1}
    {'_id': 'Warren Park School', 'count': 1}
    {'_id': 'Smith Elementary School', 'count': 1}
    {'_id': 'Saint Anthony of Padua School', 'count': 1}
    {'_id': 'Grant White School', 'count': 1}
    {'_id': 'Williamsburg Elementary School', 'count': 1}
    {'_id': 'Namaste Charter School', 'count': 1}
    {'_id': 'Saint Casimir School', 'count': 1}
    {'_id': 'Grissom Elementary School', 'count': 1}
    {'_id': 'Gordon School', 'count': 1}
    {'_id': 'Northlake Middle School', 'count': 1}
    {'_id': 'Whittier Campus Kerr Middle School', 'count': 1}
    {'_id': 'Saint Eugene School', 'count': 1}
    {'_id': 'Parkview School', 'count': 1}
    {'_id': 'Saint John Vianney School', 'count': 1}
    {'_id': 'Glenbard North High School', 'count': 1}
    {'_id': 'Presentation School', 'count': 1}
    {'_id': 'Saint Gertrude School', 'count': 1}
    {'_id': 'Fox College', 'count': 1}
    {'_id': "Saint Helen's School", 'count': 1}
    {'_id': 'Henry Puffer School', 'count': 1}
    {'_id': 'Dumas Elementary School', 'count': 1}
    {'_id': 'Blessed Agnes School', 'count': 1}
    {'_id': 'Lisbon Grade School', 'count': 1}
    {'_id': 'Pottawatomie School', 'count': 1}
    {'_id': 'Adolph Link Elementary School', 'count': 1}
    {'_id': 'Posen Elementary School', 'count': 1}
    {'_id': 'Prairie State College', 'count': 1}
    {'_id': 'Revere Elementary School', 'count': 1}
    {'_id': 'Ridgefield School', 'count': 1}
    {'_id': 'New Horizon Center for the Developmentally Disabled', 'count': 1}
    {'_id': 'Palos Evangelical Lutheran School', 'count': 1}
    {'_id': 'Crete School', 'count': 1}
    {'_id': 'Queen of the Universe School', 'count': 1}
    {'_id': 'Southside School', 'count': 1}
    {'_id': 'Saint Raymonds School', 'count': 1}
    {'_id': 'Saint Scholastica High School', 'count': 1}
    {'_id': 'Delano Elementary School', 'count': 1}
    {'_id': 'Swartz School', 'count': 1}
    {'_id': 'Union Center Elementary School', 'count': 1}
    {'_id': 'Seguin School', 'count': 1}
    {'_id': 'Tiddley Wink Pre-School', 'count': 1}
    {'_id': 'Peabody Elementary School', 'count': 1}
    {'_id': 'Pilgrim Lutheran School', 'count': 1}
    {'_id': 'Wauconda High School', 'count': 1}
    {'_id': 'Fine Arts School of Music', 'count': 1}
    {'_id': 'Spring Trail Elementary School', 'count': 1}
    {'_id': 'Parker Community Academy', 'count': 1}
    {'_id': 'Saint Tarcissus School', 'count': 1}
    {'_id': 'Pioneer Elementary School', 'count': 1}
    {'_id': 'Orland Center School', 'count': 1}
    {'_id': 'Parks Elementary School', 'count': 1}
    {'_id': 'Woodbine Elementary School', 'count': 1}
    {'_id': 'Pleasant Ridge Elementary School', 'count': 1}
    {'_id': 'Roseland School', 'count': 1}
    {'_id': 'Saint Peter Lutheran School', 'count': 1}
    {'_id': 'Roosevelt High School', 'count': 1}
    {'_id': 'Crystal Lawns Elementary School', 'count': 1}
    {'_id': 'Richards Career Academy', 'count': 1}
    {'_id': 'Crane Technical Preparatory Common High School', 'count': 1}
    {'_id': 'Carmel High School', 'count': 1}
    {'_id': 'Lincoln Park Rehabilitation Center', 'count': 1}
    {'_id': 'Cook Avenue School', 'count': 1}
    {'_id': 'Plecher School', 'count': 1}
    {'_id': 'Saint Christopher School', 'count': 1}
    {'_id': 'Plainview School', 'count': 1}
    {'_id': 'Saint Patricks School', 'count': 1}
    {'_id': 'Davis Primary School', 'count': 1}
    {'_id': 'Paul Revere Elementary School', 'count': 1}
    {'_id': 'Fullerton Elementary School', 'count': 1}
    {'_id': 'Plato School', 'count': 1}
    {'_id': 'Hammond Elementary School', 'count': 1}
    {'_id': 'Piper School', 'count': 1}
    {'_id': 'Cassell Elementary School', 'count': 1}
    {'_id': 'Saint Ann Grade School', 'count': 1}
    {'_id': 'Bradwell Elementary School', 'count': 1}
    {'_id': 'York Center Elementary School', 'count': 1}
    {'_id': 'Saint Jerome School', 'count': 1}
    {'_id': 'Teddy Bear Pre-School', 'count': 1}
    {'_id': 'Rockland Elementary School', 'count': 1}
    {'_id': 'Saint Benedict High School', 'count': 1}
    {'_id': 'Saint James the Apostle School', 'count': 1}
    {'_id': 'Saint Fidelis School', 'count': 1}
    {'_id': 'Emmet Elementary School', 'count': 1}
    {'_id': 'Morton Grove School', 'count': 1}
    {'_id': 'Lolly Pop Nursery School and Kindergarten', 'count': 1}
    {'_id': "Saint Monica's School (historical)", 'count': 1}
    {'_id': 'Saint Andrew School', 'count': 1}
    {'_id': 'Lake Central High School', 'count': 1}
    {'_id': 'Saint Celestine School', 'count': 1}
    {'_id': 'Yorkville High School', 'count': 1}
    {'_id': 'Mansion High School', 'count': 1}
    {'_id': 'Crickets Child Day Care Center', 'count': 1}
    {'_id': 'Aptakisic Junior High School', 'count': 1}
    {'_id': 'Hess School', 'count': 1}
    {'_id': 'Lake Zurich Middle School South Campus', 'count': 1}
    {'_id': 'Oaklane School', 'count': 1}
    {'_id': 'Glenbrook Elementary School', 'count': 1}
    {'_id': 'Emmanuel School', 'count': 1}
    {'_id': 'Gloria Dei Evangelical Lutheran School', 'count': 1}
    {'_id': 'Palmer Elementary School', 'count': 1}
    {'_id': 'Greenman Elementary School', 'count': 1}
    {'_id': 'Golgotha School', 'count': 1}
    {'_id': 'Saint Joachims School', 'count': 1}
    {'_id': 'Solomon Schechter Day School', 'count': 1}
    {'_id': 'Balmoral Elementary School', 'count': 1}
    {'_id': 'Libby Elementary School', 'count': 1}
    {'_id': 'Saint Louis de Montfort School', 'count': 1}
    {'_id': 'High Ridge Knolls School', 'count': 1}
    {'_id': 'Spring Avenue School', 'count': 1}
    {'_id': 'Mount Assisi Academy', 'count': 1}
    {'_id': 'Stratford School', 'count': 1}
    {'_id': 'Army Trail Elementary School', 'count': 1}
    {'_id': 'Westminster Christian School', 'count': 1}
    {'_id': 'Fernwood Elementary School', 'count': 1}
    {'_id': 'Doctor Martin Luther King School', 'count': 1}
    {'_id': 'William McKinley Elementary School', 'count': 1}
    {'_id': 'Marconi Community Academy', 'count': 1}
    {'_id': 'Yorkfield School', 'count': 1}
    {'_id': 'J B Nelson Elementary School', 'count': 1}
    {'_id': 'Navajo Heights Elementary School', 'count': 1}
    {'_id': 'Sedan Prairie School', 'count': 1}
    {'_id': 'Burnside Scholastic Academy', 'count': 1}
    {'_id': 'Ravinia Elementary School', 'count': 1}
    {'_id': 'Quigley Preparatory Seminary South', 'count': 1}
    {'_id': 'Academy of Saint Martin DePorres Elementary School', 'count': 1}
    {'_id': 'Marion Hills School', 'count': 1}
    {'_id': 'Lake Shore Seventh Day Adventist School', 'count': 1}
    {'_id': 'Gemini Junior High School', 'count': 1}
    {'_id': 'Gasteyer School', 'count': 1}
    {'_id': 'Medinah Middle School', 'count': 1}
    {'_id': 'Soloman School', 'count': 1}
    {'_id': 'Gompers Junior High School', 'count': 1}
    {'_id': 'Plainfield CISD 202 School Site', 'count': 1}
    {'_id': 'Dearborn School', 'count': 1}
    {'_id': 'Chelsea School', 'count': 1}
    {'_id': 'WM B Orenic Intermediate School', 'count': 1}
    {'_id': 'Hickory Elementary School', 'count': 1}
    {'_id': 'Loyola Academy Sports Facility', 'count': 1}
    {'_id': 'Fulton School', 'count': 1}
    {'_id': 'Covington School', 'count': 1}
    {'_id': 'Hickory Hill School', 'count': 1}
    {'_id': 'Franciscan Convent', 'count': 1}
    {'_id': 'Courtenay Language Arts Center', 'count': 1}
    {'_id': 'Fairhaven School', 'count': 1}
    {'_id': 'John I Meister Elementary School', 'count': 1}
    {'_id': 'Thompson Junior High School', 'count': 1}
    {'_id': 'Corkery Elementary School', 'count': 1}
    {'_id': 'Maplebrook Elementary School', 'count': 1}
    {'_id': 'Joliet Junior College North Campus', 'count': 1}
    {'_id': 'Hubbard Woods Elementary School', 'count': 1}
    {'_id': 'Farragut Elementary School', 'count': 1}
    {'_id': 'Tinley Park High School', 'count': 1}
    {'_id': 'Goldsmith School', 'count': 1}
    {'_id': 'Our Savior School', 'count': 1}
    {'_id': 'William Hatch Elementary School', 'count': 1}
    {'_id': 'Key School', 'count': 1}
    {'_id': 'Wallace Aylesworth Elementary School', 'count': 1}
    {'_id': 'Rich South High School', 'count': 1}
    {'_id': 'Timothy School', 'count': 1}
    {'_id': 'Medinah Intermediate School', 'count': 1}
    {'_id': 'Orchard Drive Elementary School', 'count': 1}
    {'_id': 'Romona Elementary School', 'count': 1}
    {'_id': "Saint Andrew's School", 'count': 1}
    {'_id': 'Dr. Pedro Albizu Campos High School', 'count': 1}
    {'_id': 'Manley High School', 'count': 1}
    {'_id': 'Troy Crossroads School', 'count': 1}
    {'_id': 'Hammond Career Center', 'count': 1}
    {'_id': 'Hawthorn Junior High School', 'count': 1}
    {'_id': 'Crestwood School', 'count': 1}
    {'_id': 'Caroline Sibley Elementary School', 'count': 1}
    {'_id': 'Reba O. Steck Elementary School', 'count': 1}
    {'_id': 'Chicago Junior College Wright Branch', 'count': 1}
    {'_id': 'Loretto Convent', 'count': 1}
    {'_id': 'Westview Elementary School', 'count': 1}
    {'_id': 'Trinity Evangelical Lutheran School', 'count': 1}
    {'_id': 'Kelvin Grove Junior High School', 'count': 1}
    {'_id': 'Wentworth Junior High School', 'count': 1}
    {'_id': 'Christ the King Lutheran School', 'count': 1}
    {'_id': 'Mary Queen of Heaven School', 'count': 1}
    {'_id': 'Chicago Association for Retarded Children Residential Center',
     'count': 1}
    {'_id': 'Mount Greenwood Elementary School', 'count': 1}
    {'_id': 'Saint Mathews School', 'count': 1}
    {'_id': 'New Era School', 'count': 1}
    {'_id': 'Guggenheim Elementary School', 'count': 1}
    {'_id': 'Euclid Elementary School', 'count': 1}
    {'_id': 'Lace Elementary School', 'count': 1}
    {'_id': 'Saint Laurence Day Care Center', 'count': 1}
    {'_id': 'Nationwide Trucking School', 'count': 1}
    {'_id': 'Saint Josephat School & Hall', 'count': 1}
    {'_id': 'Little City Adult Vocational Service Center', 'count': 1}
    {'_id': 'Marycrest Elementary School', 'count': 1}
    {'_id': 'Rondout School', 'count': 1}
    {'_id': 'Cherry Hill School', 'count': 1}
    {'_id': 'Beveridge Elementary School', 'count': 1}
    {'_id': 'Aurora University', 'count': 1}
    {'_id': 'MacArthur School', 'count': 1}
    {'_id': 'Saint Daniel School', 'count': 1}
    {'_id': 'Nottingham School', 'count': 1}
    {'_id': 'Our Lady of Peace School', 'count': 1}
    {'_id': 'Lake in the Hills Elementary School', 'count': 1}
    {'_id': 'Belding Elementary School', 'count': 1}
    {'_id': 'Parks Middle School', 'count': 1}
    {'_id': 'World of Rainbows', 'count': 1}
    {'_id': 'Burtons Bridge School', 'count': 1}
    {'_id': 'General George Patton School', 'count': 1}
    {'_id': 'Robert E Clow Elementary School', 'count': 1}
    {'_id': 'Daniel Boone Elementary School', 'count': 1}
    {'_id': 'Willowcrest School', 'count': 1}
    {'_id': 'Hay Community Academy', 'count': 1}
    {'_id': 'Jack Hille School', 'count': 1}
    {'_id': 'Field Park Elementary School', 'count': 1}
    {'_id': 'Bright Elementary School', 'count': 1}
    {'_id': 'Kancon Magnet School', 'count': 1}
    {'_id': "Saint John's School", 'count': 1}
    {'_id': 'Salazar Bilingual Center', 'count': 1}
    {'_id': 'Crab Orchard Junior High School', 'count': 1}
    {'_id': 'Edgewood Middle School', 'count': 1}
    {'_id': 'Goodman Avenue School', 'count': 1}
    {'_id': 'Clarence E. Culver Middle School', 'count': 1}
    {'_id': 'Lenart School', 'count': 1}
    {'_id': 'Leggee Elementary School', 'count': 1}
    {'_id': 'May Watts Elementary School', 'count': 1}
    {'_id': 'Lords Park Elementary School', 'count': 1}
    {'_id': 'Willow School', 'count': 1}
    {'_id': 'Flower Career Academy High School', 'count': 1}
    {'_id': 'Saint Francis of Rome School', 'count': 1}
    {'_id': 'Elgin Academy', 'count': 1}
    {'_id': 'Indiana University Northwest', 'count': 1}
    {'_id': 'Jensen Scholastic Academy', 'count': 1}
    {'_id': 'Jungman Elementary School', 'count': 1}
    {'_id': 'Dorn Primary Center', 'count': 1}
    {'_id': 'Bell Elementary School', 'count': 1}
    {'_id': 'Western Avenue Elementary School', 'count': 1}
    {'_id': 'Gifford Elementary School', 'count': 1}
    {'_id': 'Westfield Elementary School', 'count': 1}
    {'_id': 'Kahler Middle School', 'count': 1}
    {'_id': 'Hilltop Elementary', 'count': 1}
    {'_id': 'Drexel Elementary School', 'count': 1}
    {'_id': 'EPIC Academy', 'count': 1}
    {'_id': 'Mizpah Seventh Day Adventist School', 'count': 1}
    {'_id': 'Kane County Regional Office of Education', 'count': 1}
    {'_id': 'Hirsch Metropolitan High School', 'count': 1}
    {'_id': 'Marra Collins South Preparatory School', 'count': 1}
    {'_id': 'Oakhill Elementary School', 'count': 1}
    {'_id': 'Tabernacle Christian Academy', 'count': 1}
    {'_id': 'S S Peter and Paul High School', 'count': 1}
    {'_id': 'Englewood Messiah Lutheran Headstart', 'count': 1}
    {'_id': 'Dempster Junior High School', 'count': 1}
    {'_id': 'Topsy Turby Nursery and Kindergarten', 'count': 1}
    {'_id': 'Ebinger Elementary School', 'count': 1}
    {'_id': 'Lundahl Junior High School', 'count': 1}
    {'_id': 'Brookwood Middle School', 'count': 1}
    {'_id': 'Saint Barbara School (Closed)', 'count': 1}
    {'_id': 'Tidye A Phillips Elementary School', 'count': 1}
    {'_id': 'Bethune School', 'count': 1}
    {'_id': 'Southwest School of Business', 'count': 1}
    {'_id': 'Old Post Elementary School', 'count': 1}
    {'_id': 'Deerpath Middle School', 'count': 1}
    {'_id': 'Saint Philip Basilica High School', 'count': 1}
    {'_id': 'Wauconda Middle School', 'count': 1}
    {'_id': 'Highland High School', 'count': 1}
    {'_id': 'Theodore Roosevelt High School', 'count': 1}
    {'_id': 'East View Elementary School', 'count': 1}
    {'_id': 'Aetna Elementary School', 'count': 1}
    {'_id': 'Merrillville High School', 'count': 1}
    {'_id': 'Edgar A Poe Elementary School', 'count': 1}
    {'_id': 'Elim Christian School', 'count': 1}
    {'_id': 'Cossitt Avenue Elementary School', 'count': 1}
    {'_id': 'Tanner Elementary School', 'count': 1}
    {'_id': 'Meadowview Elementary School', 'count': 1}
    {'_id': 'Daniel S. Wentworth Elementary School', 'count': 1}
    {'_id': 'Ames Middle School', 'count': 1}
    {'_id': 'Bunche Elementary School', 'count': 1}
    {'_id': 'Saint John of the Cross School', 'count': 1}
    {'_id': 'Edison Middle School', 'count': 1}
    {'_id': 'Saint Michael School', 'count': 1}
    {'_id': 'Hubert H Humphrey Middle School', 'count': 1}
    {'_id': 'Saint Willibrords School', 'count': 1}
    {'_id': 'Red Oak Elementary School', 'count': 1}
    {'_id': "Saint Martha's School", 'count': 1}
    {'_id': 'Benjamin Franklin Middle School', 'count': 1}
    {'_id': 'Concordia School', 'count': 1}
    {'_id': 'Deer Creek Junior High School', 'count': 1}
    {'_id': 'Ebenezer School', 'count': 1}
    {'_id': 'Hales Franciscan High School', 'count': 1}
    {'_id': 'McClaughry School', 'count': 1}
    {'_id': 'Gage Park High School', 'count': 1}
    {'_id': 'Saint Marys Nativity School', 'count': 1}
    {'_id': 'Mary E McDowell Elementary School', 'count': 1}
    {'_id': 'Bradley School', 'count': 1}
    {'_id': 'Chippewa School', 'count': 1}
    {'_id': 'Kensington Elementary School', 'count': 1}
    {'_id': 'Frank A Brodnicki Elementary School', 'count': 1}
    {'_id': 'Sunnydale Elementary School', 'count': 1}
    {'_id': 'Canterbury School', 'count': 1}
    {'_id': 'Saint Walter School', 'count': 1}
    {'_id': 'Saint Edwards High School', 'count': 1}
    {'_id': 'Saint Phillip School', 'count': 1}
    {'_id': 'Nightingale Elementary School', 'count': 1}
    {'_id': 'Healy Elementary School', 'count': 1}
    {'_id': 'Beacon Hill School', 'count': 1}
    {'_id': 'William H. King Elementary School', 'count': 1}
    {'_id': 'Cherokee Elementary School', 'count': 1}
    {'_id': 'Richard Byrd Elementary School', 'count': 1}
    {'_id': 'Chicago Math and Science Academy', 'count': 1}
    {'_id': 'John Foster Dulles School', 'count': 1}
    {'_id': 'Blackhawk Elementary School', 'count': 1}
    {'_id': 'C.M. Bardwell Elementary School', 'count': 1}
    {'_id': 'Oak Ridge School', 'count': 1}
    {'_id': 'Palos West Elementary School', 'count': 1}
    {'_id': 'Kildeer School', 'count': 1}
    {'_id': 'Lake Forest Country School', 'count': 1}
    {'_id': 'Saint Pauls Evangelical Lutheran School', 'count': 1}
    {'_id': 'Garfield School', 'count': 1}
    {'_id': 'Williams Academy', 'count': 1}
    {'_id': 'Bridgeview School', 'count': 1}
    {'_id': 'A. F. Ames Elementary School', 'count': 1}
    {'_id': 'Porter School (historical)', 'count': 1}
    {'_id': 'Fox Ridge Elementary School', 'count': 1}
    {'_id': 'Meadowood School', 'count': 1}
    {'_id': 'Herrick Junior High School', 'count': 1}
    {'_id': 'Berkley School', 'count': 1}
    {'_id': 'Rutledge High School', 'count': 1}
    {'_id': 'Aurora Christian School', 'count': 1}
    {'_id': 'Grace Lutheran School', 'count': 1}
    {'_id': 'Hill School', 'count': 1}
    {'_id': 'Forest Elementary School', 'count': 1}
    {'_id': 'Henderson School', 'count': 1}
    {'_id': 'Saint Lawrence School', 'count': 1}
    {'_id': 'Nativity of Our Saviour Catholic School', 'count': 1}
    {'_id': 'Central Road Elementary School', 'count': 1}
    {'_id': 'Zenon J Sykuta School', 'count': 1}
    {'_id': 'Ralph Bunche School', 'count': 1}
    {'_id': 'Saint Irenaeus School', 'count': 1}
    {'_id': 'Brentwood Elementary School', 'count': 1}
    {'_id': 'Shoesmith Elementary School', 'count': 1}
    {'_id': 'Willow Hill School', 'count': 1}
    {'_id': 'Emma Melzer School', 'count': 1}
    {'_id': 'West Side Junior High School', 'count': 1}
    {'_id': 'Rescue Missionary Christian School', 'count': 1}
    {'_id': 'De Vry Technical Institute', 'count': 1}
    {'_id': 'Gwendolyn Brooks Middle School', 'count': 1}
    {'_id': 'Morrill Elementary School', 'count': 1}
    {'_id': 'Plainfield Central High School', 'count': 1}
    {'_id': 'Waubonsee College-Yorkville Campus', 'count': 1}
    {'_id': 'Lincoln Park High School', 'count': 1}
    {'_id': 'Crown School', 'count': 1}
    {'_id': 'Campanelli Elementary School', 'count': 1}
    {'_id': 'Saint Mary of Perpetual Help Elementary School', 'count': 1}
    {'_id': 'Resurrection School', 'count': 1}
    {'_id': 'Tonti Elementary School', 'count': 1}
    {'_id': 'Waterbury Elementary School', 'count': 1}
    {'_id': 'Mulligan School', 'count': 1}
    {'_id': 'Bloom Community College', 'count': 1}
    {'_id': 'Coultrap Elementary School', 'count': 1}
    {'_id': 'Messiah School', 'count': 1}
    {'_id': 'Argo School', 'count': 1}
    {'_id': 'Oakland School', 'count': 1}
    {'_id': 'Monee Elementary School', 'count': 1}
    {'_id': 'Funston Elementary School', 'count': 1}
    {'_id': 'Fenton High School', 'count': 1}
    {'_id': 'Sauk Trail School', 'count': 1}
    {'_id': 'Hopewell School', 'count': 1}
    {'_id': 'Arbor Park Middle School', 'count': 1}
    {'_id': 'Sheppard North High School', 'count': 1}
    {'_id': 'Heritage Middle School', 'count': 1}
    {'_id': 'Masters Martial Arts Alliance', 'count': 1}
    {'_id': 'Middlefork Primary School', 'count': 1}
    {'_id': 'Oak Knoll Elementary School', 'count': 1}
    {'_id': 'Central Park School', 'count': 1}
    {'_id': 'Maria High School', 'count': 1}
    {'_id': 'Jackson Junior High School', 'count': 1}
    {'_id': 'Gompers Elementary School', 'count': 1}
    {'_id': 'Saint John Fisher School', 'count': 1}
    {'_id': 'Ivy Hill Elementary School', 'count': 1}
    {'_id': 'Calvary Temple School', 'count': 1}
    {'_id': 'Wolcott Elementary School', 'count': 1}
    {'_id': 'L D Brady Elementary School', 'count': 1}
    {'_id': 'Pine Bluff School', 'count': 1}
    {'_id': 'Park West Cooperative Nursery School', 'count': 1}
    {'_id': 'Oakton School', 'count': 1}
    {'_id': 'Emmanuel Christian School', 'count': 1}
    {'_id': 'Arcadia Elementary School', 'count': 1}
    {'_id': 'Glen Oaks Elementary School', 'count': 1}
    {'_id': 'Moody Bible Institute', 'count': 1}
    {'_id': 'Jones Elementary School', 'count': 1}
    {'_id': 'Chalmers School', 'count': 1}
    {'_id': 'Wood View Elementary School', 'count': 1}
    {'_id': 'Broadview Academy', 'count': 1}
    {'_id': 'Dixon Elementary School', 'count': 1}
    {'_id': 'Hoffman Elementary School', 'count': 1}
    {'_id': 'Holmes School', 'count': 1}
    {'_id': 'Peter Cottontail Day Nursery', 'count': 1}
    {'_id': 'Barat Campus DePaul University', 'count': 1}
    {'_id': 'Forest Ridge School', 'count': 1}
    {'_id': 'RISE - Worthridge School', 'count': 1}
    {'_id': 'Geneva School District 304', 'count': 1}
    {'_id': 'Armour Elementary School', 'count': 1}
    {'_id': 'Little Flower School', 'count': 1}
    {'_id': 'Diekman Elementary School', 'count': 1}
    {'_id': 'Saint Anthonys School', 'count': 1}
    {'_id': 'Christian School', 'count': 1}
    {'_id': 'Evers Elementary School', 'count': 1}
    {'_id': 'Shields Elementary School', 'count': 1}
    {'_id': 'Avoca West Elementary School', 'count': 1}
    {'_id': 'Abbott Middle School', 'count': 1}
    {'_id': 'Otter Creek Elementary School', 'count': 1}
    {'_id': 'Clearmont Elementary School', 'count': 1}
    {'_id': 'Harriet C Harris Private School', 'count': 1}
    {'_id': 'Crete-Monee Middle School', 'count': 1}
    {'_id': 'Fernway Park Elementary School', 'count': 1}
    {'_id': 'Glenside Middle School', 'count': 1}
    {'_id': 'Keller Gifted Magnet School', 'count': 1}
    {'_id': 'Lawson School', 'count': 1}
    {'_id': 'M Sheridan Magnet School', 'count': 1}
    {'_id': 'Mark Twain School', 'count': 1}
    {'_id': 'Saint Adrian School', 'count': 1}
    {'_id': 'Lieb School', 'count': 1}
    {'_id': 'Andrean High School', 'count': 1}
    {'_id': 'Daniel Burnham Elementary School', 'count': 1}
    {'_id': 'Century Oaks Elementary School', 'count': 1}
    {'_id': 'Saint Gregory High School', 'count': 1}
    {'_id': 'Summit Hill Junior High School', 'count': 1}
    {'_id': 'Childrens House Preschool', 'count': 1}
    {'_id': 'Loyola Academy', 'count': 1}
    {'_id': 'Heineman Middle School', 'count': 1}
    {'_id': 'Sunnyside Elementary School', 'count': 1}
    {'_id': 'Bert H Fulton Elementary School', 'count': 1}
    {'_id': 'Our Lady of Charity School', 'count': 1}
    {'_id': 'George L Myers Elementary School', 'count': 1}
    {'_id': 'Burns Elementary School', 'count': 1}
    {'_id': 'Edna Keith Elementary School', 'count': 1}
    {'_id': 'Midway Driving School', 'count': 1}
    {'_id': 'Dr. Bessie Rhodes Magnet School', 'count': 1}
    {'_id': 'Saint Mary of Czestochowa School', 'count': 1}
    {'_id': 'Wacker Elementary School', 'count': 1}
    {'_id': 'Lake Bluff Middle School', 'count': 1}
    {'_id': 'Saint John the Baptist School', 'count': 1}
    {'_id': 'Wentworth Elementary School', 'count': 1}
    {'_id': 'Reedswood School', 'count': 1}
    {'_id': 'Northside Catholic Academy', 'count': 1}
    {'_id': 'Columbia College Chicago', 'count': 1}
    {'_id': 'Brownell Elementary School', 'count': 1}
    {'_id': 'Muslim Education Center', 'count': 1}
    {'_id': 'Emmaus Bible School', 'count': 1}
    {'_id': 'Virgil I Bailey Elementary School', 'count': 1}
    {'_id': 'Marquardt Middle School', 'count': 1}
    {'_id': 'Fox River Grove Junior High School', 'count': 1}
    {'_id': 'Neil School', 'count': 1}
    {'_id': 'Franklin Park School', 'count': 1}
    {'_id': 'Countryside Elementary School', 'count': 1}
    {'_id': 'Churchill Elementary School', 'count': 1}
    {'_id': 'Gray M Sandborn Elementary School', 'count': 1}
    {'_id': 'Saucedo Scholastic Academy', 'count': 1}
    {'_id': 'Orchard Place Elementary School', 'count': 1}
    {'_id': 'Elm Junior High School', 'count': 1}
    {'_id': 'Bannockburn Elementary School', 'count': 1}
    {'_id': 'Saint Giles School', 'count': 1}
    {'_id': 'West Suburbs Christian School', 'count': 1}
    {'_id': 'Charles J Sahs Elementary School', 'count': 1}
    {'_id': 'Saint Sebastian Elementary School', 'count': 1}
    {'_id': 'Dundee High School', 'count': 1}
    {'_id': 'Carter Elementary School', 'count': 1}
    {'_id': 'Percy L. Julian High School', 'count': 1}
    {'_id': 'DePriest Elementary School', 'count': 1}
    {'_id': 'Audubon Elementary School', 'count': 1}
    {'_id': 'Chicago Ridge School', 'count': 1}
    {'_id': 'Lewis Elementary School', 'count': 1}
    {'_id': 'CAM Academy', 'count': 1}
    {'_id': 'The Learning Exchange', 'count': 1}
    {'_id': 'Holy Family Academy', 'count': 1}
    {'_id': 'Timothy Ball Elementary School (historical)', 'count': 1}
    {'_id': 'Burroughs School', 'count': 1}
    {'_id': 'Saint Susanna School', 'count': 1}
    {'_id': 'Chippewa Middle School', 'count': 1}
    {'_id': 'Bethel Elementary School', 'count': 1}
    {'_id': 'Goodlow School', 'count': 1}
    {'_id': 'Faxon School', 'count': 1}
    {'_id': 'McCarty Elementary School', 'count': 1}
    {'_id': 'Riverside Elementary School (historical)', 'count': 1}
    {'_id': 'Glenbrook North High School', 'count': 1}
    {'_id': 'Gregory School', 'count': 1}
    {'_id': 'A O Marshall Elementary School', 'count': 1}
    {'_id': 'Selans Beauty School', 'count': 1}
    {'_id': 'Park Junior High School', 'count': 1}
    {'_id': 'Morgan School', 'count': 1}
    {'_id': 'Chicago Parental School', 'count': 1}
    {'_id': 'Deneen Elementary School', 'count': 1}
    {'_id': 'Rachel Carson Elementary School', 'count': 1}
    {'_id': 'Christians School', 'count': 1}
    {'_id': 'George B Carpenter Elementary School', 'count': 1}
    {'_id': 'Woodland Academy of the Sacred Heart', 'count': 1}
    {'_id': 'Pros Arts Studio', 'count': 1}
    {'_id': 'Saint Bonaventure School', 'count': 1}
    {'_id': 'Wolcott School', 'count': 1}
    {'_id': 'Fremont Elementary School', 'count': 1}
    {'_id': 'Marshall Metro High School', 'count': 1}
    {'_id': 'Ambridge Elementary School', 'count': 1}
    {'_id': 'Lorimer School', 'count': 1}
    {'_id': 'Calvin Christian School', 'count': 1}
    {'_id': 'Henking Elementary School', 'count': 1}
    {'_id': 'US Grant Elementary School', 'count': 1}
    {'_id': 'Little Peoples Nursery School', 'count': 1}
    {'_id': 'George Rogers Clark Elementary School', 'count': 1}
    {'_id': 'Saint Margaret School', 'count': 1}
    {'_id': 'Coolidge Elementary School', 'count': 1}
    {'_id': 'Carl Sandburg Middle School', 'count': 1}
    {'_id': 'Palos Park School', 'count': 1}
    {'_id': 'Oak Park River Forest High School', 'count': 1}
    {'_id': 'Larsen Middle School', 'count': 1}
    {'_id': 'Fenger High School', 'count': 1}
    {'_id': 'John E Albright Middle School', 'count': 1}
    {'_id': 'Edwards High School', 'count': 1}
    {'_id': 'Stan H. Kaplan Education Center', 'count': 1}
    {'_id': 'Saint Helena School', 'count': 1}
    {'_id': 'A Vito Martinez Middle School', 'count': 1}
    {'_id': 'Cottage Grove Middle School', 'count': 1}
    {'_id': 'Ernie Pyle Elementary School', 'count': 1}
    {'_id': 'Mercy Hall', 'count': 1}
    {'_id': 'Salem School', 'count': 1}
    {'_id': 'Booth Tarkington Elementary School', 'count': 1}
    {'_id': 'Chicago Christian Academy', 'count': 1}
    {'_id': 'Homan Elementary School', 'count': 1}
    {'_id': 'Parkview Elementary School', 'count': 1}
    {'_id': 'Beecher High School', 'count': 1}
    {'_id': 'Kendall Elementary School', 'count': 1}
    {'_id': 'Cunningham Elementary School', 'count': 1}
    {'_id': 'Israel Elementary School', 'count': 1}
    {'_id': 'Laurel Hill Elementary School', 'count': 1}
    {'_id': 'Arlington Ridge School', 'count': 1}
    {'_id': 'Black Hawk Junior High School', 'count': 1}
    {'_id': 'Central Junior High School', 'count': 1}
    {'_id': 'Columbia School', 'count': 1}
    {'_id': 'Copeland Manor Elementary School', 'count': 1}
    {'_id': 'Whittler School', 'count': 1}
    {'_id': 'Ludwig Elementary School', 'count': 1}
    {'_id': 'Gresham School', 'count': 1}
    {'_id': 'William Beye Elementary School', 'count': 1}
    {'_id': 'Rockdale Elementary School', 'count': 1}
    {'_id': 'Franklin Elementary School', 'count': 1}
    {'_id': 'Alice Gustafson Elementary School', 'count': 1}
    {'_id': 'Philadelphia Church of God in Christ School', 'count': 1}
    {'_id': 'Zion Hill Day Care Center School', 'count': 1}
    {'_id': 'North Lawndale College Prep Charter - Christiana', 'count': 1}
    {'_id': 'Congress Park Elementary School', 'count': 1}
    {'_id': 'Donald E Gavit Middle/High School', 'count': 1}
    {'_id': 'Maine South High School', 'count': 1}
    {'_id': 'National College of Chiropractic', 'count': 1}
    {'_id': 'Wescott Elementary School', 'count': 1}
    {'_id': 'Thornton Fractional High School North', 'count': 1}
    {'_id': 'Blessed Sacrament School', 'count': 1}
    {'_id': 'Alexandre Dumas Child-Parent Center', 'count': 1}
    {'_id': 'Sauk Area Career Center', 'count': 1}
    {'_id': 'Worth Junior High School', 'count': 1}
    {'_id': 'Geneva Middle School North', 'count': 1}
    {'_id': 'Low School', 'count': 1}
    {'_id': 'John L Sipley Elementary School', 'count': 1}
    {'_id': 'Hawthorne School', 'count': 1}
    {'_id': 'Crawl School', 'count': 1}
    {'_id': 'John Mills Elementary School', 'count': 1}
    {'_id': 'Karel Havlicek Elementary School', 'count': 1}
    {'_id': 'Haven Middle School', 'count': 1}
    {'_id': 'Moos Elementary School', 'count': 1}
    {'_id': 'Saint Vincent Depaul High School Seminary', 'count': 1}
    {'_id': 'Harris School', 'count': 1}
    {'_id': 'Saint George Catholic School', 'count': 1}
    {'_id': 'Unity Catholic High School', 'count': 1}
    {'_id': 'Wheatley Child-Parent Education Center', 'count': 1}
    {'_id': 'Lakewood School', 'count': 1}
    {'_id': 'Prairie Junior High School', 'count': 1}
    {'_id': 'Gurrie Middle School', 'count': 1}
    {'_id': 'Central Alternative High School', 'count': 1}
    {'_id': 'Greenwood Elementary School', 'count': 1}
    {'_id': 'Nipper Career Education Center', 'count': 1}
    {'_id': 'Queen of Peace High School', 'count': 1}
    {'_id': 'Greene Elementary School', 'count': 1}
    {'_id': 'Walter F Fierke Education Center', 'count': 1}
    {'_id': 'Elcaballero Elegante School', 'count': 1}
    {'_id': 'Luther J Schilling School', 'count': 1}
    {'_id': 'Lester Elementary School', 'count': 1}
    {'_id': 'Harnew School', 'count': 1}
    {'_id': 'Chateaux Elementary School', 'count': 1}
    {'_id': 'Benedict the African School', 'count': 1}
    {'_id': 'Kipling Elementary School', 'count': 1}
    {'_id': 'Orr Community Academy High School', 'count': 1}
    {'_id': 'Garden School for the Handicapped', 'count': 1}
    {'_id': 'Chippewa Elementary School', 'count': 1}
    {'_id': 'Agustin Lara Academy', 'count': 1}
    {'_id': 'Raster Elementary School', 'count': 1}
    {'_id': 'Calhoun North Elementary School', 'count': 1}
    {'_id': 'Homewood-Flossmoor High School', 'count': 1}
    {'_id': 'Forest Glen Elementary School', 'count': 1}
    {'_id': 'Kerr Middle School', 'count': 1}
    {'_id': 'Springfield Elementary School', 'count': 1}
    {'_id': 'Horner School', 'count': 1}
    {'_id': 'Chicago Dance Center', 'count': 1}
    {'_id': 'Coolidge School', 'count': 1}
    {'_id': 'Lindblom Technical High School', 'count': 1}
    {'_id': 'Chaney School', 'count': 1}
    {'_id': 'Nettlehorst Elementary School', 'count': 1}
    {'_id': 'Wheaton Academy', 'count': 1}
    {'_id': 'Cooper Middle School', 'count': 1}
    {'_id': 'Hufford Junior High School', 'count': 1}
    {'_id': 'Gregory Middle School', 'count': 1}
    {'_id': 'Illinois School', 'count': 1}
    {'_id': 'Justice School', 'count': 1}
    {'_id': 'Saint Columba School', 'count': 1}
    {'_id': 'Cather Elementary School', 'count': 1}
    {'_id': 'Saint Jane de Chantal School', 'count': 1}
    {'_id': 'The Grove School', 'count': 1}
    {'_id': 'Elm Place School', 'count': 1}
    {'_id': 'Genesis Central School', 'count': 1}
    {'_id': 'Byford Elementary School', 'count': 1}
    {'_id': 'Jefferson Middle School', 'count': 1}
    {'_id': 'Lake Forest College', 'count': 1}
    {'_id': 'Community Consolidated District Office', 'count': 1}
    {'_id': 'Fox River Country Day School', 'count': 1}
    {'_id': 'Burley Elementary School', 'count': 1}
    {'_id': 'Arrowhead School', 'count': 1}
    {'_id': 'Lakeview Elementary School', 'count': 1}
    {'_id': 'South Ward School', 'count': 1}
    {'_id': 'Crystal Lake South High School', 'count': 1}
    {'_id': 'Lakewood Elementary School', 'count': 1}
    {'_id': 'Lake Zurich High School', 'count': 1}
    {'_id': 'Jack London Junior High School', 'count': 1}
    {'_id': 'Henry Ford II School', 'count': 1}
    {'_id': 'Manhattan Jr. High School', 'count': 1}
    {'_id': 'Ridge School', 'count': 1}
    {'_id': 'Lawn Manor School', 'count': 1}
    {'_id': 'Joliet Catholic Academy', 'count': 1}
    {'_id': 'Talala Elementary School', 'count': 1}
    {'_id': 'Mayo Elementary School', 'count': 1}
    {'_id': 'Onahan Elementary School', 'count': 1}
    {'_id': 'Tiny Tots Day Care Center', 'count': 1}
    {'_id': 'Rhodes Elementary School', 'count': 1}
    {'_id': 'McIntosh School', 'count': 1}
    {'_id': 'Eliza Kelly Elementary School', 'count': 1}
    {'_id': 'Indian Hills School', 'count': 1}
    {'_id': 'Kaneland John Shields Elementary', 'count': 1}
    {'_id': 'Lowrie Elementary School', 'count': 1}
    {'_id': 'Palisades School', 'count': 1}
    {'_id': 'Hope Academy School', 'count': 1}
    {'_id': 'Las Casas Occupational High School', 'count': 1}
    {'_id': 'Park View School', 'count': 1}
    {'_id': 'Nativity School', 'count': 1}
    {'_id': 'North Ridge School', 'count': 1}
    {'_id': 'Queen of Angels School', 'count': 1}
    {'_id': 'Westfield Junior High School', 'count': 1}
    {'_id': 'George T Wilkins School', 'count': 1}
    {'_id': 'Thomas Dooley Elementary School', 'count': 1}
    {'_id': 'Saint Anns School', 'count': 1}
    {'_id': 'Horizon Elementary School', 'count': 1}
    {'_id': 'Oak Ridge Elementary School', 'count': 1}
    {'_id': 'Galileo School', 'count': 1}
    {'_id': 'Illiana Christian High School', 'count': 1}
    {'_id': 'Mildred I Lavizzo Elementary School', 'count': 1}
    {'_id': 'Park Lawn School', 'count': 1}
    {'_id': 'Northwestern University Feinberg School of Medicine', 'count': 1}
    {'_id': 'Von Steuben Metropolitan High School', 'count': 1}
    {'_id': 'Saint Bellarmine School', 'count': 1}
    {'_id': 'Resurrection Lutheran School', 'count': 1}
    {'_id': 'Saint Procopius Elementary School', 'count': 1}
    {'_id': 'Bloom High School', 'count': 1}
    {'_id': 'Jerling Junior High School', 'count': 1}
    {'_id': 'Argo Community High School', 'count': 1}
    {'_id': 'Kohn School', 'count': 1}
    {'_id': 'G N Dieterich Elementary School', 'count': 1}
    {'_id': 'Faith Lutheran School', 'count': 1}
    {'_id': 'Kellar Junior High School', 'count': 1}
    {'_id': 'Eldon Ready Elementary School', 'count': 1}
    {'_id': 'Half Day School', 'count': 1}
    {'_id': 'Trinity International University', 'count': 1}
    {'_id': 'Nicholson Elementary School', 'count': 1}
    {'_id': 'First Bethlehem Evangelical Lutheran School', 'count': 1}
    {'_id': 'Mahalia Jackson Elementary School', 'count': 1}
    {'_id': 'Meadowdale Elementary School', 'count': 1}
    {'_id': 'Goose Lake School', 'count': 1}
    {'_id': 'Kimball Middle School', 'count': 1}
    {'_id': 'Jay Stream Middle School', 'count': 1}
    {'_id': 'East Chicago Central High School', 'count': 1}
    {'_id': 'Lewis University', 'count': 1}
    {'_id': 'Bunche School', 'count': 1}
    {'_id': 'Apostles Lutheran School', 'count': 1}
    {'_id': 'East DuPage School', 'count': 1}
    {'_id': 'Midwest Center for the Study of Oriental Medicine', 'count': 1}
    {'_id': 'Indian Grove Elementary School', 'count': 1}
    {'_id': 'Leo High School', 'count': 1}
    {'_id': 'Pope Elementary School', 'count': 1}
    {'_id': 'O W Huth Middle School', 'count': 1}
    {'_id': 'Brighton Park Elementary School', 'count': 1}
    {'_id': 'Saint Leo School', 'count': 1}
    {'_id': 'Bremen High School', 'count': 1}
    {'_id': 'Diesel Truck Driver Training School', 'count': 1}
    {'_id': 'Oliver W Holmes Middle School', 'count': 1}
    {'_id': 'Michelson School', 'count': 1}
    {'_id': 'Saint Rita School', 'count': 1}
    {'_id': 'Sherlock Elementary School', 'count': 1}
    {'_id': 'Hiawatha Elementary School', 'count': 1}
    {'_id': 'Meadowview School', 'count': 1}
    {'_id': 'Saint Timothy School', 'count': 1}
    {'_id': 'Saint Laurence School', 'count': 1}
    {'_id': 'Saint Catharine Laboure School', 'count': 1}
    {'_id': 'Cook Elementary School', 'count': 1}
    {'_id': 'South Haven Christian School', 'count': 1}
    {'_id': 'Scotch School', 'count': 1}
    {'_id': 'Cardenas Elementary School', 'count': 1}
    {'_id': 'Marmion Military Academy', 'count': 1}
    {'_id': 'Saint Norberts School', 'count': 1}
    {'_id': 'Frankfort Square Elementary School', 'count': 1}
    {'_id': 'Hendricks Elementary School', 'count': 1}
    {'_id': 'Our Lady of the Snows School', 'count': 1}
    {'_id': 'Superior Driving School', 'count': 1}
    {'_id': 'Scammon Elementary School', 'count': 1}
    {'_id': 'Lowell-Longfellow School', 'count': 1}
    {'_id': 'Proviso East High School', 'count': 1}
    {'_id': 'Countryside School', 'count': 1}
    {'_id': 'Concord Elementary School', 'count': 1}
    {'_id': 'Curtis School', 'count': 1}
    {'_id': 'Stockton Elementary School', 'count': 1}
    {'_id': 'Ruggles Elementary School', 'count': 1}
    {'_id': 'Saint Laurence High School', 'count': 1}
    {'_id': 'Jirka School', 'count': 1}
    {'_id': 'Arnold J Tyler Elementary School', 'count': 1}
    {'_id': 'Hynes Elementary School', 'count': 1}
    {'_id': 'A-Karrasel Nursery School and Kindergarten', 'count': 1}
    {'_id': 'Hephzibah Christian Academy', 'count': 1}
    {'_id': 'Taylor Elementary School', 'count': 1}
    {'_id': 'Prairie Grove Elementary School', 'count': 1}
    {'_id': 'Maddock Elementary School', 'count': 1}
    {'_id': 'Lincoln-Way Central High School', 'count': 1}
    {'_id': 'Portage Park Day Nursery', 'count': 1}
    {'_id': 'Lady of Peace School', 'count': 1}
    {'_id': 'Prospect High School', 'count': 1}
    {'_id': 'Glenn Hill School', 'count': 1}
    {'_id': 'Pilsen Community Academy', 'count': 1}
    {'_id': 'Fairmont Junior High School', 'count': 1}
    {'_id': 'Saint Stanislaus Kostka Grade School', 'count': 1}
    {'_id': 'Luther Burbank Elementary School', 'count': 1}
    {'_id': 'Brandt School', 'count': 1}
    {'_id': 'Deerfield School', 'count': 1}
    {'_id': 'Nazareth School', 'count': 1}
    {'_id': 'Hadley School for the Blind', 'count': 1}
    {'_id': 'Midwest Christian Academy', 'count': 1}
    {'_id': 'Von Humboldt Elementary School', 'count': 1}
    {'_id': 'Fabyan Elementary', 'count': 1}
    {'_id': 'Marian High School', 'count': 1}
    {'_id': 'Tolentine College', 'count': 1}
    {'_id': 'Canton Middle School', 'count': 1}
    {'_id': 'Markham Park Elementary School', 'count': 1}
    {'_id': 'Olivet Baptist Church Day Care Center', 'count': 1}
    {'_id': 'Forest Road Elementary School', 'count': 1}
    {'_id': 'Goodwin Elementary School', 'count': 1}
    {'_id': 'Saint Ailbe School', 'count': 1}
    {'_id': 'Herget Middle School', 'count': 1}
    {'_id': 'Maple Middle School', 'count': 1}
    {'_id': 'May Community Academy', 'count': 1}
    {'_id': 'Julius Hess School', 'count': 1}
    {'_id': 'Morton-Gingerwood Elementary School', 'count': 1}
    {'_id': 'Oak Terrace Elementary School', 'count': 1}
    {'_id': 'Study Progress School', 'count': 1}
    {'_id': 'Maryknoll Seminary', 'count': 1}
    {'_id': 'National College of Education Urban Campus', 'count': 1}
    {'_id': 'Park Manor Elementary School', 'count': 1}
    {'_id': 'Saint Gerald School', 'count': 1}
    {'_id': "O'Toole Elementary School", 'count': 1}
    {'_id': 'Stuart R Paddock Elementary School', 'count': 1}
    {'_id': 'Patton Elementary School', 'count': 1}
    {'_id': 'Elizabeth Ide Elementary School', 'count': 1}
    {'_id': 'Near North Special Education School', 'count': 1}
    {'_id': 'Valley View School', 'count': 1}
    {'_id': 'Phillip J Rock School', 'count': 1}
    {'_id': 'Illinois Mathematics and Science Academy', 'count': 1}
    {'_id': 'J T Manning Elementary School', 'count': 1}
    {'_id': 'Glen Kirk School', 'count': 1}
    {'_id': 'Nazareth Academy', 'count': 1}
    {'_id': 'V H Nelson Elementary School', 'count': 1}
    {'_id': 'Taka School of Martial Arts', 'count': 1}
    {'_id': 'Suder Montessori Magnet School', 'count': 1}
    {'_id': 'Our Lady of the Mount School', 'count': 1}
    {'_id': 'Dominican Priory', 'count': 1}
    {'_id': 'Protsman Elementary School', 'count': 1}
    {'_id': 'Our Lady of the Ridge School', 'count': 1}
    {'_id': 'Katz Corner School', 'count': 1}
    {'_id': 'Percy Julian Junior High School', 'count': 1}
    {'_id': 'McAuley School', 'count': 1}
    {'_id': 'Our Lady of Guadalupe School', 'count': 1}
    {'_id': 'Kennedy - King College', 'count': 1}
    {'_id': 'Orchard School', 'count': 1}
    {'_id': 'Peace School', 'count': 1}
    {'_id': 'Highland Day Care Center', 'count': 1}
    {'_id': 'Channing Memorial Elementary School', 'count': 1}
    {'_id': 'Frank Hall Elementary School', 'count': 1}
    {'_id': 'Roosevelt Junior High School', 'count': 1}
    {'_id': 'Palm School', 'count': 1}
    {'_id': 'Laraway Elementary School', 'count': 1}
    {'_id': 'Saints Peter and Paul Junior High School', 'count': 1}
    {'_id': 'Jane Addams Middle School', 'count': 1}
    {'_id': 'Mark Elementary School', 'count': 1}
    {'_id': 'Fenwick High School', 'count': 1}
    {'_id': 'Northview School', 'count': 1}
    {'_id': 'East Leyden High School', 'count': 1}
    {'_id': 'Reformed School', 'count': 1}
    {'_id': 'McLaren Elementary School', 'count': 1}
    {'_id': 'Suzuki Academy of Music', 'count': 1}
    {'_id': 'Palos School', 'count': 1}
    {'_id': 'Dett Elementary School', 'count': 1}
    {'_id': 'F E Peacock Junior High School', 'count': 1}
    {'_id': 'Evangelical Christian School', 'count': 1}
    {'_id': 'Saint Agnes School', 'count': 1}
    {'_id': 'Dunbar School', 'count': 1}
    {'_id': 'Saint Salomeas School', 'count': 1}
    {'_id': 'Gloria Dei School', 'count': 1}
    {'_id': 'Academy of Saint James College Preparatory School', 'count': 1}
    {'_id': 'Saint Clotildes School', 'count': 1}
    {'_id': 'Perkins School', 'count': 1}
    {'_id': 'Joseph T Kush School', 'count': 1}
    {'_id': 'A-Delta Driving School', 'count': 1}
    {'_id': 'Saint Alphonsus High School', 'count': 1}
    {'_id': 'Midwest Pre-School-South Commons', 'count': 1}
    {'_id': 'Highland Educational Day Care Center', 'count': 1}
    {'_id': 'Westmont School', 'count': 1}
    {'_id': 'Thomas A Edison Junior High School', 'count': 1}
    {'_id': 'Westmore Elementary School', 'count': 1}
    {'_id': 'Saint Gregory Grade School', 'count': 1}
    {'_id': 'Tate Woods Elementary School', 'count': 1}
    {'_id': 'Nichols Middle School', 'count': 1}
    {'_id': "Saint Luke's School", 'count': 1}
    {'_id': 'Spalding School', 'count': 1}
    {'_id': 'South School', 'count': 1}
    {'_id': 'Hampshire High School', 'count': 1}
    {'_id': 'Harold Reskin School', 'count': 1}
    {'_id': 'Tioga Elementary School', 'count': 1}
    {'_id': "Saint Walter's Catholic School", 'count': 1}
    {'_id': 'Schrage School', 'count': 1}
    {'_id': 'Ivanhoe Elementary School', 'count': 1}
    {'_id': 'Newton Yost Elementary School', 'count': 1}
    {'_id': 'Pleasant Lane Elementary School', 'count': 1}
    {'_id': 'Saint Paschals School', 'count': 1}
    {'_id': 'Overton Elementary School', 'count': 1}
    {'_id': 'Saint Anselm School', 'count': 1}
    {'_id': 'Saint Rita High School', 'count': 1}
    {'_id': 'Saint Petronille School', 'count': 1}
    {'_id': 'Saint John the Apostle School', 'count': 1}
    {'_id': 'Hickory Point Elementary School', 'count': 1}
    {'_id': 'Queen Bee School', 'count': 1}
    {'_id': 'Saint Joseph Seminary', 'count': 1}
    {'_id': 'Chesterfield Tom Thumb Day Care Center and Kindergarten School',
     'count': 1}
    {'_id': 'Shiloh Nursery', 'count': 1}
    {'_id': 'Saint Francis High School', 'count': 1}
    {'_id': 'Saint Clement School', 'count': 1}
    {'_id': 'Lake Forest Graduate School of Management', 'count': 1}
    {'_id': 'Stony Creek Elementary School', 'count': 1}
    {'_id': 'Assumption Blessed Virgin Mary-Saint Catherine of Genoa School',
     'count': 1}
    {'_id': 'Whistler Elementary School', 'count': 1}
    {'_id': 'Saint Damian School', 'count': 1}
    {'_id': 'Timothy Lutheran School', 'count': 1}
    {'_id': 'Nash Elementary School', 'count': 1}
    {'_id': 'Luther East High School', 'count': 1}
    {'_id': 'Benjamin Franklin School', 'count': 1}
    {'_id': 'Saint Germaine School', 'count': 1}
    {'_id': 'Saint Carthage School', 'count': 1}
    {'_id': 'Saint Mary Magdalen School', 'count': 1}
    {'_id': 'Saint Mary High School', 'count': 1}
    {'_id': 'Rich East High School', 'count': 1}
    {'_id': 'Black School', 'count': 1}
    {'_id': 'Anne M Jeans Elementary School', 'count': 1}
    {'_id': 'Scanlan School', 'count': 1}
    {'_id': 'Grove Elementary School', 'count': 1}
    {'_id': 'Churchill School', 'count': 1}
    {'_id': 'Worsham College', 'count': 1}
    {'_id': 'Lisbon School', 'count': 1}
    {'_id': 'Gower Middle School', 'count': 1}
    {'_id': 'Allen School', 'count': 1}
    {'_id': 'Shelby School', 'count': 1}
    {'_id': 'South Haven Elementary School', 'count': 1}
    {'_id': 'Kick School', 'count': 1}
    {'_id': 'Willow Creek Elementary School', 'count': 1}
    {'_id': 'Childrens Hour Pre-School Center', 'count': 1}
    {'_id': 'Noll School', 'count': 1}
    {'_id': 'Normandy Villa School', 'count': 1}
    {'_id': 'Wheaton North High School', 'count': 1}
    {'_id': 'Hillcrest High School', 'count': 1}
    {'_id': 'Heather Hill School', 'count': 1}
    {'_id': 'Terra Cotta School', 'count': 1}
    {'_id': 'Matteson Elementary School', 'count': 1}
    {'_id': 'Northlake School', 'count': 1}
    {'_id': 'Locke Elementary School', 'count': 1}
    {'_id': 'Lake Park School', 'count': 1}
    {'_id': 'First Lutheran School', 'count': 1}
    {'_id': 'Saint Isidore School', 'count': 1}
    {'_id': 'Doctor Charles E Gavin Elementary School', 'count': 1}
    {'_id': 'Indian Ridge School', 'count': 1}
    {'_id': 'Wagoner Elementary School', 'count': 1}
    {'_id': 'Hale Middle School', 'count': 1}
    {'_id': 'Salem Evangelical Lutheran School', 'count': 1}
    {'_id': 'Betsy Ross Elementary School', 'count': 1}
    {'_id': 'Polaris School for Individual Education', 'count': 1}
    {'_id': 'Caldwell Elementary School', 'count': 1}
    {'_id': 'Hamlin Upper Grade Center School', 'count': 1}
    {'_id': 'Greenwood School', 'count': 1}
    {'_id': 'The Peace and Education Coalition Alternative High School', 'count': 1}
    {'_id': 'Munhall Elementary School', 'count': 1}
    {'_id': 'Laura B Sprague School', 'count': 1}
    {'_id': 'Saint Thaddeus School', 'count': 1}
    {'_id': 'UIC College Prep', 'count': 1}
    {'_id': 'Lisle High School', 'count': 1}
    {'_id': 'Bloom Trail High School', 'count': 1}
    {'_id': 'Saint Simeon School', 'count': 1}
    {'_id': 'Cuffe School', 'count': 1}
    {'_id': 'Stanley Field Junior High School', 'count': 1}
    {'_id': 'Ashburn Lutheran School', 'count': 1}
    {'_id': 'Gooding Grove School', 'count': 1}
    {'_id': 'Byrne School', 'count': 1}
    {'_id': 'Oakwood Elementary School', 'count': 1}
    {'_id': 'Long Beach Elementary School', 'count': 1}
    {'_id': 'Boulder Hill Elementary School', 'count': 1}
    {'_id': 'Ericson Scholastic Academy', 'count': 1}
    {'_id': 'Circle Center Middle School', 'count': 1}
    {'_id': 'Southwest Elementary School', 'count': 1}
    {'_id': 'Fox Valley Bible School', 'count': 1}
    {'_id': 'Wild Rose Elementary School', 'count': 1}
    {'_id': 'Christa McAuliffe School', 'count': 1}
    {'_id': 'School of Saints', 'count': 1}
    {'_id': 'Saint Marys Catholic School', 'count': 1}
    {'_id': 'Canterbury Elementary School', 'count': 1}
    {'_id': 'Coventry School', 'count': 1}
    {'_id': 'Summit School', 'count': 1}
    {'_id': 'Calumet High School', 'count': 1}
    {'_id': 'Forest Trail Junior High School', 'count': 1}
    {'_id': 'Henry Ford Academy: Power House High', 'count': 1}
    {'_id': 'William A Wirt Senior High School', 'count': 1}
    {'_id': 'Algonquin Road Elementary School', 'count': 1}
    {'_id': 'Cary Junior High School', 'count': 1}
    {'_id': 'Medgar Evers Elementary School', 'count': 1}
    {'_id': 'Cary-Grove Community High School', 'count': 1}
    {'_id': 'Golfview Elementary School', 'count': 1}
    {'_id': 'Pleasant Dale North School', 'count': 1}
    {'_id': 'Lincoln Middle School', 'count': 1}
    {'_id': 'Living Waters Fellowship School', 'count': 1}
    {'_id': 'Gower West Elementary School', 'count': 1}
    {'_id': 'Helen Keller Elementary School', 'count': 1}
    {'_id': 'Wall School', 'count': 1}
    {'_id': 'Lew Wallace Elementary School', 'count': 1}
    {'_id': 'H C Storm Elementary School', 'count': 1}
    {'_id': 'Saint Scholastica School', 'count': 1}
    {'_id': 'Edgewood Elementary School', 'count': 1}
    {'_id': 'Ziebell School', 'count': 1}
    {'_id': 'Shabbona Middle School', 'count': 1}
    {'_id': 'Earl Pritchett School', 'count': 1}
    {'_id': 'Seth Paine Elementary School', 'count': 1}
    {'_id': 'Saint Wenceslaus School', 'count': 1}
    {'_id': 'Roslyn Road Elementary School', 'count': 1}
    {'_id': 'West Oak Middle School', 'count': 1}
    {'_id': 'May Whitney Elementary School', 'count': 1}
    {'_id': 'Twin Grove Junior High School', 'count': 1}
    {'_id': 'Adlai Stevenson School', 'count': 1}
    {'_id': 'Godino Francisco School', 'count': 1}
    {'_id': 'Oak Prairie Junior High School', 'count': 1}
    {'_id': 'Winnebago Elementary School', 'count': 1}
    {'_id': 'Hester Junior High School', 'count': 1}
    {'_id': 'Wesley Elementary School', 'count': 1}
    {'_id': 'Miller School', 'count': 1}
    {'_id': 'Western Trails Elementary School', 'count': 1}
    {'_id': 'Lily Lake Elementary School', 'count': 1}
    {'_id': 'L R Foster Elementary School', 'count': 1}
    {'_id': 'Roberto Clemente Community Academy', 'count': 1}
    {'_id': 'Incarnation School', 'count': 1}
    {'_id': 'James B. Farnsworth Elementary School', 'count': 1}
    {'_id': 'Flossmoor School', 'count': 1}
    {'_id': 'Stratford Junior High School', 'count': 1}
    {'_id': 'V Ralph Dosher Elementary School', 'count': 1}
    {'_id': 'F B McCord Elementary School', 'count': 1}
    {'_id': 'Anderson Elementary School', 'count': 1}
    {'_id': 'Pleasantdale South School', 'count': 1}
    {'_id': 'Valparaiso Technical Institute (historical)', 'count': 1}
    {'_id': 'Oak Forest High School', 'count': 1}
    {'_id': 'Ridge Central Elementary School', 'count': 1}
    {'_id': 'Dundee Highlands Elementary School', 'count': 1}
    {'_id': 'High Point Elementary School', 'count': 1}
    {'_id': 'Lieutenant Jospeh P Kennedy Junior School', 'count': 1}
    {'_id': 'Penn Elementary School', 'count': 1}
    {'_id': 'Bennett Elementary School', 'count': 1}
    {'_id': 'Josephinum High School', 'count': 1}
    {'_id': 'Everett F Kerr Intermediate School', 'count': 1}
    {'_id': 'Batavia High School', 'count': 1}
    {'_id': 'Highland Christian School', 'count': 1}
    {'_id': 'Korae School', 'count': 1}
    {'_id': 'Harold Washington School', 'count': 1}
    {'_id': 'Arnold W Kruse Education Center', 'count': 1}
    {'_id': 'Saint Gabriel High School', 'count': 1}
    {'_id': 'McGugan School', 'count': 1}
    {'_id': 'Trinity Christian College', 'count': 1}
    {'_id': 'South Suburban College', 'count': 1}
    {'_id': 'Alexanders Beauty School', 'count': 1}
    {'_id': 'Coleman Elementary School', 'count': 1}
    {'_id': 'Highlands School', 'count': 1}
    {'_id': 'West Chicago Middle School', 'count': 1}
    {'_id': 'Robert Morris College', 'count': 1}
    {'_id': 'Opera School of Chicago', 'count': 1}
    {'_id': 'Helen B Sandidge Elementary School', 'count': 1}
    {'_id': 'Marya Yates Elementary School', 'count': 1}
    {'_id': 'Webster Elementary School', 'count': 1}
    {'_id': 'Edwin Aldrin Elementary School', 'count': 1}
    {'_id': 'Niles Elementary School South', 'count': 1}
    {'_id': 'Lake Zurich Middle School', 'count': 1}
    {'_id': 'Kingsley Elementary School', 'count': 1}
    {'_id': 'Kirk Developmental Training Center', 'count': 1}
    {'_id': 'Schaumburg High School', 'count': 1}
    {'_id': 'Marion Jordan Elementary School', 'count': 1}
    {'_id': 'Saint Benedict Grade School', 'count': 1}
    {'_id': 'Hough Street Elementary School', 'count': 1}
    {'_id': 'Seventh-Day Adventist School', 'count': 1}
    {'_id': 'Hoover Math & Science Academy', 'count': 1}
    {'_id': 'Saint Boniface School', 'count': 1}
    {'_id': 'Independence Junior High School', 'count': 1}
    {'_id': 'Grove Avenue Elementary School', 'count': 1}
    {'_id': 'Cardinal Stritch High School', 'count': 1}
    {'_id': 'Michael Collins Elementary School', 'count': 1}
    {'_id': 'Aikido Center Midwest', 'count': 1}
    {'_id': 'Pickard Elementary School', 'count': 1}
    {'_id': 'Our Lady School', 'count': 1}
    {'_id': 'Pablo Casals School', 'count': 1}
    {'_id': 'Bernard J Ward Middle School', 'count': 1}
    {'_id': 'John R Tibbott Elementary School', 'count': 1}
    {'_id': 'Gray Elementary School', 'count': 1}
    {'_id': 'Ann Rutledge School', 'count': 1}
    {'_id': 'Marantha School', 'count': 1}
    {'_id': 'Lockport Township High School East', 'count': 1}
    {'_id': 'Ancona School', 'count': 1}
    {'_id': 'Edward J Tobin Elementary School', 'count': 1}
    {'_id': 'Lockport Township High School', 'count': 1}
    {'_id': 'Esperanza Elementary School', 'count': 1}
    {'_id': 'Hanover Countryside Elementary School', 'count': 1}
    {'_id': 'Lenas Artistic Beauty College', 'count': 1}
    {'_id': 'Dryden Elementary School', 'count': 1}
    {'_id': 'LeBallet Petit School of Dance', 'count': 1}
    {'_id': 'Field School', 'count': 1}
    {'_id': 'Heritage Elementary School', 'count': 1}
    {'_id': 'Hadley School', 'count': 1}
    {'_id': 'Virgil I Grissom Junior High School', 'count': 1}
    {'_id': 'Jamie McGee Elementary School', 'count': 1}
    {'_id': 'Haven Elementary School', 'count': 1}
    {'_id': 'Grace United Methodist Church', 'count': 1}
    {'_id': 'Saint Andrews School', 'count': 1}
    {'_id': 'Riverwoods School', 'count': 1}
    {'_id': "Lyon's Township High School North Campus", 'count': 1}
    {'_id': 'Technology Center of DuPage', 'count': 1}
    {'_id': 'Irene King Elementary School', 'count': 1}
    {'_id': 'Schmid Elementary School', 'count': 1}
    {'_id': 'Oliver W Holmes Elementary School', 'count': 1}
    {'_id': 'Saint Leonard School', 'count': 1}
    {'_id': 'Monroe Middle School', 'count': 1}
    {'_id': 'Oak Therapeutic School', 'count': 1}
    {'_id': 'Talman School', 'count': 1}
    {'_id': 'Saint Irenes School', 'count': 1}
    {'_id': 'George Washington Carver Elementary School', 'count': 1}
    {'_id': 'Collins South School', 'count': 1}
    {'_id': 'Benson Art Beat', 'count': 1}
    {'_id': 'Hearst Elementary School', 'count': 1}
    {'_id': 'Marist High School', 'count': 1}
    {'_id': 'Carrie Gosch Elementary School', 'count': 1}
    {'_id': 'Washington-Mc-Kinley Junior High School', 'count': 1}
    {'_id': 'Wauconda Elementary School', 'count': 1}
    {'_id': 'Brookdale Elementary School', 'count': 1}
    {'_id': 'Wendell Phillips Academy High School', 'count': 1}
    {'_id': 'West Elementary School', 'count': 1}
    {'_id': 'Saint Viator Elementary School', 'count': 1}
    {'_id': 'Kenneth E Neubert Elementary School', 'count': 1}
    {'_id': 'Admiral Richard E. Byrd Elementary School', 'count': 1}
    {'_id': 'Rogers Elementary School', 'count': 1}
    {'_id': 'Saint Xavier University - South Campus', 'count': 1}
    {'_id': 'North Junior High School', 'count': 1}
    {'_id': 'Yorkville Grade School', 'count': 1}
    {'_id': 'East Aurora High School', 'count': 1}
    {'_id': 'Evergreen Elementary School', 'count': 1}
    {'_id': 'Virginia Lake Elementary School', 'count': 1}
    {'_id': 'Thornton Fractional High School South', 'count': 1}
    {'_id': 'Triton College', 'count': 1}
    {'_id': 'Warren School', 'count': 1}
    {'_id': 'Highland Park High School', 'count': 1}
    {'_id': 'Amos Alonzo Stagg High School', 'count': 1}
    {'_id': 'Hawthorn South School', 'count': 1}
    {'_id': 'Sol School', 'count': 1}
    {'_id': 'Bailly Middle School', 'count': 1}
    {'_id': 'Echo School', 'count': 1}
    {'_id': 'Streamwood Elementary School', 'count': 1}
    {'_id': 'Columbus School', 'count': 1}
    {'_id': 'Kinzie School', 'count': 1}
    {'_id': 'Hanna Sacks Bais Yaakov High School', 'count': 1}
    {'_id': 'North Barrington Elementary School', 'count': 1}
    {'_id': 'East Elementary School', 'count': 1}
    {'_id': 'Stephen F. Gale Math and Science Academy', 'count': 1}
    {'_id': 'Thomas Jefferson Junior High School', 'count': 1}
    {'_id': 'Wilbur Wright College', 'count': 1}
    {'_id': 'Butterfield School', 'count': 1}
    {'_id': 'Elk Grove High School', 'count': 1}
    {'_id': 'Santa Lucia School', 'count': 1}
    {'_id': 'Saint Vincent Ferrer School', 'count': 1}
    {'_id': 'Judith Morton Johnston Elementary School', 'count': 1}
    {'_id': 'Elsie C Johnson Elementary School', 'count': 1}
    {'_id': 'East Aurora School District Office', 'count': 1}
    {'_id': 'Our Lady of Fatima School', 'count': 1}
    {'_id': 'Carol Stream Elementary School', 'count': 1}
    {'_id': 'Lincoln Hall Middle School', 'count': 1}
    {'_id': 'Conrad Fischer Elementary School', 'count': 1}
    {'_id': 'Carl Sandburg Elementary School', 'count': 1}
    {'_id': 'Ross Elementary School', 'count': 1}
    {'_id': 'Chicago Truck Driving School', 'count': 1}
    {'_id': 'Richard Craft Junior High School', 'count': 1}
    {'_id': 'Saint Isadore School', 'count': 1}
    {'_id': 'Eisenhower School', 'count': 1}
    {'_id': 'Roy De Shane Elementary School', 'count': 1}
    {'_id': 'Pheasant Ridge Primary School', 'count': 1}
    {'_id': 'Arbor View Elementary School', 'count': 1}
    {'_id': 'Bridgeport Catholic Academy', 'count': 1}
    {'_id': 'Belle Aire Elementary School', 'count': 1}
    {'_id': "Saint Bernardine's School", 'count': 1}
    {'_id': 'Earl Bedford School of Music', 'count': 1}
    {'_id': 'Daniel Wright Junior High School', 'count': 1}
    {'_id': 'Saint Dionysius School', 'count': 1}
    {'_id': 'Black Hawk Elementary School', 'count': 1}
    {'_id': 'Bower Elementary School', 'count': 1}
    {'_id': 'Bunnyland Developmental Day Care Center', 'count': 1}
    {'_id': 'Indian Knoll Elementary School', 'count': 1}
    {'_id': 'C I Johnson Elementary School', 'count': 1}
    {'_id': 'Reskin Elementary School', 'count': 1}
    {'_id': 'C E Miller Elementary School', 'count': 1}
    {'_id': 'Medinah Christian School', 'count': 1}
    {'_id': 'Ferson Creek School', 'count': 1}
    {'_id': 'Timothy Ball Elementary School', 'count': 1}
    {'_id': 'First Evangelical Lutheran School', 'count': 1}
    {'_id': "Mabel O'Donnell Elementary School", 'count': 1}
    {'_id': 'Joliet Twp. High School - Central Campus', 'count': 1}
    {'_id': 'Saint Johns Lutheran School', 'count': 1}
    {'_id': 'Wasco Elementary School', 'count': 1}
    {'_id': 'The Country School', 'count': 1}
    {'_id': 'Woodridge Elementary School', 'count': 1}
    {'_id': 'Saint Charles School', 'count': 1}
    {'_id': 'Lake Park High School West', 'count': 1}
    {'_id': 'Oglesby School', 'count': 1}
    {'_id': 'Banneker Elementary School', 'count': 1}
    {'_id': 'Mark Delay School', 'count': 1}
    {'_id': 'Roselle Middle School', 'count': 1}
    {'_id': 'John A Bannes Elementary School', 'count': 1}
    {'_id': 'El Sierra Elementary School', 'count': 1}
    {'_id': 'Taft High School', 'count': 1}
    {'_id': 'Morse-Beidler School', 'count': 1}
    {'_id': 'Americana Intermediate School', 'count': 1}
    {'_id': 'Giles High School', 'count': 1}
    {'_id': 'Academy of Saint Martin De Porres Elementary School', 'count': 1}
    {'_id': 'Miriam Daniels School', 'count': 1}
    {'_id': 'Corpus Christi School', 'count': 1}
    {'_id': 'Elmhurst College', 'count': 1}
    {'_id': 'Montessori School of South Shore', 'count': 1}
    {'_id': 'Galewood Pre-School and Day Care Center', 'count': 1}
    {'_id': 'Simpson Academy for Young Women', 'count': 1}
    {'_id': 'Mayfair Academy of Fine Arts', 'count': 1}
    {'_id': 'AERO Center', 'count': 1}
    {'_id': 'Thurgood Marshall Middle School', 'count': 1}
    {'_id': 'Old Town Triangle Art Center', 'count': 1}
    {'_id': 'Liberty Intermediate School', 'count': 1}
    {'_id': 'Prescott Elementary School', 'count': 1}
    {'_id': 'Komensky Elementary School', 'count': 1}
    {'_id': 'Oster-Oakview Middle School', 'count': 1}
    {'_id': 'Saint Agathas School', 'count': 1}
    {'_id': 'Le Cordon Bleu College of Culinary Arts', 'count': 1}
    {'_id': 'Lake Shore Montessori Day Care Center', 'count': 1}
    {'_id': 'Academy of Acupuncture', 'count': 1}
    {'_id': 'PADI International Instructors Training Center', 'count': 1}
    {'_id': 'Forest Park Individual Education School', 'count': 1}
    {'_id': 'Austin Career Education Center', 'count': 1}
    {'_id': 'Hillside School', 'count': 1}
    {'_id': 'Elmwood Junior High School', 'count': 1}
    {'_id': 'Ellsworth Elementary School', 'count': 1}
    {'_id': 'Austin Branch High School', 'count': 1}
    {'_id': 'Auburn Park Day Care Center', 'count': 1}
    {'_id': 'Niles West High School', 'count': 1}
    {'_id': 'Fieldcrest Elementary School', 'count': 1}
    {'_id': 'Robert Crown Elementary School', 'count': 1}
    {'_id': 'Paderewski Elementary School', 'count': 1}
    {'_id': 'Homewood Christian Academy', 'count': 1}
    {'_id': 'Thomas Jefferson School', 'count': 1}
    {'_id': 'Mays School', 'count': 1}
    {'_id': 'Mundelein Consolidated High School', 'count': 1}
    {'_id': 'Ashe School', 'count': 1}
    {'_id': 'Lake Forest High School', 'count': 1}
    {'_id': 'Elizabeth Blackwell Elementary School', 'count': 1}
    {'_id': 'Charles Quentin Elementary School', 'count': 1}
    {'_id': 'Saint Josephs School (historical)', 'count': 1}
    {'_id': 'Elwood Community Consolidated School', 'count': 1}
    {'_id': 'Ideal School', 'count': 1}
    {'_id': 'Taft School', 'count': 1}
    {'_id': 'Milne Grove Elementary School', 'count': 1}
    {'_id': 'Wilton Center Elementary School', 'count': 1}
    {'_id': 'Beecher Elementary School', 'count': 1}
    {'_id': 'Wheatland School', 'count': 1}
    {'_id': 'Indiana University Calumet Center', 'count': 1}
    {'_id': 'Gillespie Elementary School', 'count': 1}
    {'_id': 'Mokena Junior High School', 'count': 1}
    {'_id': 'Mokena Elementary School', 'count': 1}
    {'_id': 'Harry D. Jacobs High School', 'count': 1}
    {'_id': 'Blythe School', 'count': 1}
    {'_id': 'Incarnation Head Start Center', 'count': 1}
    {'_id': 'Theatre Shoppe Backstage', 'count': 1}
    {'_id': 'Robert C Hill Elementary School', 'count': 1}
    {'_id': 'Centennial School', 'count': 1}
    {'_id': 'Carrie Roundy Kindergarten', 'count': 1}
    {'_id': 'Taft Grade School', 'count': 1}
    {'_id': 'Chicago National College of Naprapathy', 'count': 1}
    {'_id': 'Chicago Academy', 'count': 1}
    {'_id': 'Greenbrier Elementary School', 'count': 1}
    {'_id': 'Cheltenham Day Care Nursery and Kindergarten', 'count': 1}
    {'_id': 'Henry W, Eggers Elementary - Middle School', 'count': 1}
    {'_id': 'Braeside Elementary School', 'count': 1}
    {'_id': 'Charles Harrison Mason Bible College', 'count': 1}
    {'_id': 'Highlands Junior High School', 'count': 1}
    {'_id': 'Saint Francis De Sales School', 'count': 1}
    {'_id': 'Mannheim School', 'count': 1}
    {'_id': 'Forest Park Early Childhood Center', 'count': 1}
    {'_id': 'Chatham Montessori School', 'count': 1}
    {'_id': 'W A Johnson Elementary School', 'count': 1}
    {'_id': 'Independence School', 'count': 1}
    {'_id': 'Mary Meyer School', 'count': 1}
    {'_id': 'Mid-America Beauty School', 'count': 1}
    {'_id': 'Laramie School', 'count': 1}
    {'_id': 'Cosmetologist Educational Institute', 'count': 1}
    {'_id': 'Carpentersville Middle School', 'count': 1}
    {'_id': 'Nathan Hale Primary School', 'count': 1}
    {'_id': 'Community Lutheran School', 'count': 1}
    {'_id': 'Cameron Elementary School', 'count': 1}
    {'_id': 'Public Art Workshop', 'count': 1}
    {'_id': 'Faith Hope and Charity School', 'count': 1}
    {'_id': 'Baum School', 'count': 1}
    {'_id': 'Dancers Delight Dance Studio', 'count': 1}
    {'_id': 'Anshe Emet Day School', 'count': 1}
    {'_id': 'Angel Land Nursery School', 'count': 1}
    {'_id': 'Anderson Academy', 'count': 1}
    {'_id': 'Bais Yaakov School', 'count': 1}
    {'_id': 'Athenaikon Hellenic School', 'count': 1}
    {'_id': 'Grand Avenue School', 'count': 1}
    {'_id': 'Bartlett Elementary School', 'count': 1}
    {'_id': 'Bristol Grade School', 'count': 1}
    {'_id': 'Seguin Training School', 'count': 1}
    {'_id': 'Worthwoods Elementary School', 'count': 1}
    {'_id': 'Socrates Greek-American Elementary School', 'count': 1}
    {'_id': 'Pace High School', 'count': 1}
    {'_id': 'South Shore Community Academy', 'count': 1}
    {'_id': 'Eastview Middle School', 'count': 1}
    {'_id': 'Austin Special Sheltered Work Center', 'count': 1}
    {'_id': 'Austin Special School and Sheltered Work Center', 'count': 1}
    {'_id': 'Austin School of Beauty Culture', 'count': 1}
    {'_id': 'Harlan Community Academy High School', 'count': 1}
    {'_id': 'Chelsea Elementary School', 'count': 1}
    {'_id': 'Basic Skills Institute', 'count': 1}
    {'_id': 'Enders-Salk Elementary School', 'count': 1}
    {'_id': 'Addison Trail High School', 'count': 1}
    {'_id': 'Cheder Lubavitch Girls School', 'count': 1}
    {'_id': 'Bethany Seminary', 'count': 1}
    {'_id': 'Lithuanian Institute of Education', 'count': 1}
    {'_id': 'Chicago School of Massage Theraphy', 'count': 1}
    {'_id': 'Western Avenue Junior High School', 'count': 1}
    {'_id': 'Joliet West High School', 'count': 1}
    {'_id': 'Clark Middle School', 'count': 1}
    {'_id': 'Choi Karate Institute', 'count': 1}
    {'_id': 'The Children Village', 'count': 1}
    {'_id': 'Chicago-Kent College of Law', 'count': 1}
    {'_id': 'Harry E Fry Elementary School', 'count': 1}
    {'_id': 'Saint Roman School', 'count': 1}
    {'_id': 'Borenquen Driving School', 'count': 1}
    {'_id': 'Bridgeport Academy Center', 'count': 1}
    {'_id': 'Brentwood Christian Academy', 'count': 1}
    {'_id': 'Bricklayers Apprentice School', 'count': 1}
    {'_id': 'Luis Munoz Marin Primary Center', 'count': 1}
    {'_id': 'Oak View Elementary School', 'count': 1}
    {'_id': 'Davis Development Center', 'count': 1}
    {'_id': 'DeVry Institute of Technology', 'count': 1}
    {'_id': 'Pirie Elementary School', 'count': 1}
    {'_id': 'Discovery Center', 'count': 1}
    {'_id': 'Saint Francis De Sales Grade School', 'count': 1}
    {'_id': 'Gage Park School', 'count': 1}
    {'_id': 'Developmental Institute', 'count': 1}
    {'_id': 'Crown Community Academy', 'count': 1}
    {'_id': 'Duke and Duchess Pre-School', 'count': 1}
    {'_id': 'Paul H Douglas Center or Environmental Education', 'count': 1}
    {'_id': 'Holy Cross Junior High School', 'count': 1}
    {'_id': 'Durso School', 'count': 1}
    {'_id': 'Presentation Adult Education School', 'count': 1}
    {'_id': 'Walter H Dyett Middle School', 'count': 1}
    {'_id': 'General Custer Elementary School', 'count': 1}
    {'_id': 'Edison School', 'count': 1}
    {'_id': 'Chicago Graphic Arts Institute', 'count': 1}
    {'_id': 'Maercker Elementary School', 'count': 1}
    {'_id': 'Grove Junior High School', 'count': 1}
    {'_id': 'Evangelical School of Nursing', 'count': 1}
    {'_id': 'Holy Redeemer School', 'count': 1}
    {'_id': 'Bethel Lutheran School', 'count': 1}
    {'_id': 'Budlong Elementary School', 'count': 1}
    {'_id': 'Linne Elementary School', 'count': 1}
    {'_id': 'Saint Kevin School', 'count': 1}
    {'_id': 'Terrace Elementary School', 'count': 1}
    {'_id': 'Village Art School', 'count': 1}
    {'_id': 'Blackhawk School of Art', 'count': 1}
    {'_id': 'Glen Oak School', 'count': 1}
    {'_id': 'Bethlehem School', 'count': 1}
    {'_id': 'Global Enterprises School of Law Enforcement', 'count': 1}
    {'_id': 'Gladness V Player Early Childhood Center', 'count': 1}
    {'_id': 'Giannini Music Center', 'count': 1}
    {'_id': 'Drummond Elementary School', 'count': 1}
    {'_id': 'Gladys Mae Dancing School', 'count': 1}
    {'_id': 'Martial Arts Systems Judo and Karate School', 'count': 1}
    {'_id': 'Union Township Middle School', 'count': 1}
    {'_id': 'Maternity of the Blessed Virgin Mary School', 'count': 1}
    {'_id': 'Hannum School', 'count': 1}
    {'_id': 'South Suburban Elementary School', 'count': 1}
    {'_id': 'Montessori Midwest Teacher Training Center', 'count': 1}
    {'_id': 'Durand Art Institute', 'count': 1}
    {'_id': 'Hinsdale Academy', 'count': 1}
    {'_id': 'Husmann Elementary School', 'count': 1}
    {'_id': 'Morse Elementary School', 'count': 1}
    {'_id': 'Mannheim High School', 'count': 1}
    {'_id': 'Saint Gerard-Majella School', 'count': 1}
    {'_id': 'Immaculata High School', 'count': 1}
    {'_id': 'Ippolito School of Cosmetology', 'count': 1}
    {'_id': 'Hapkido and Karate School', 'count': 1}
    {'_id': 'Hazel Green Elementary School', 'count': 1}
    {'_id': 'Coonley Elementary School', 'count': 1}
    {'_id': 'Deer Path Middle School', 'count': 1}
    {'_id': 'Frank C Whiteley Elementary School', 'count': 1}
    {'_id': 'Lubavitch Mesivta', 'count': 1}
    {'_id': 'Thomas A Edison Junior - Senior High School', 'count': 1}
    {'_id': 'Hanover Highlands Elementary School', 'count': 1}
    {'_id': 'Hodgkins Elementary School', 'count': 1}
    {'_id': 'North Shore Country Day School', 'count': 1}
    {'_id': 'Teddy Bear Pre-School Number 3', 'count': 1}
    {'_id': 'Kennedy High School', 'count': 1}
    {'_id': 'Kiddie Play School', 'count': 1}
    {'_id': 'Keller Junior High School', 'count': 1}
    {'_id': 'Louisa May Alcott School', 'count': 1}
    {'_id': 'First Baptist Christian School', 'count': 1}
    {'_id': 'Thomas A Edison Elementary School', 'count': 1}
    {'_id': 'H.H. Conrady Junior High School', 'count': 1}
    {'_id': 'Listening Skills Training Center', 'count': 1}
    {'_id': 'Grande Park Elementary', 'count': 1}
    {'_id': 'Lincoln Technical Institute', 'count': 1}
    {'_id': 'Fairview North School', 'count': 1}
    {'_id': 'John Marshall Law School', 'count': 1}
    {'_id': 'Berger-Vandenberg Elementary School', 'count': 1}
    {'_id': 'Lathrop Elementary School', 'count': 1}
    {'_id': 'Hubbard High School', 'count': 1}
    {'_id': 'Immanuel Lutheran Church', 'count': 1}
    {'_id': 'Jeanine Schultz Memorial School', 'count': 1}
    {'_id': 'Jane Adams Junior High School', 'count': 1}
    {'_id': 'William H Seward Communication Arts Academy', 'count': 1}
    {'_id': 'Illinois Park Elementary School', 'count': 1}
    {'_id': 'South Park Elementary School', 'count': 1}
    {'_id': 'J B Kennedy Elementary School', 'count': 1}
    {'_id': 'Plum Grove Junior High School', 'count': 1}
    {'_id': 'James W Shelton Senior School', 'count': 1}
    {'_id': 'MacArthur Middle School', 'count': 1}
    {'_id': 'Saint Bronislava School', 'count': 1}
    {'_id': 'Cumberland Elementary School', 'count': 1}
    {'_id': 'Envision Unlimited Westtown Training Center', 'count': 1}
    {'_id': 'Frank L Baum School', 'count': 1}
    {'_id': 'Franciscan Sisters School', 'count': 1}
    {'_id': 'Plamondon Elementary School', 'count': 1}
    {'_id': 'Clark E School of Beauty Culture', 'count': 1}
    {'_id': 'Collins High School', 'count': 1}
    {'_id': 'Higgins Community Academy', 'count': 1}
    {'_id': 'Wayne Elementary School', 'count': 1}
    {'_id': 'Saint Ludmilla School', 'count': 1}
    {'_id': 'Briargate Elementary School', 'count': 1}
    {'_id': 'Saint Malachy School', 'count': 1}
    {'_id': 'Prince of Peace Lutheran School', 'count': 1}
    {'_id': 'Foreman Elementary School', 'count': 1}
    {'_id': 'Job Training Institute', 'count': 1}
    {'_id': 'Richards Vocational High School', 'count': 1}
    {'_id': 'Alied Institute of Technology', 'count': 1}
    {'_id': 'Rand Junior High School', 'count': 1}
    {'_id': "O'Neill Middle School", 'count': 1}
    {'_id': 'Precious Blood School', 'count': 1}
    {'_id': 'Saint Charles Lwango School', 'count': 1}
    {'_id': 'Saint Bede School', 'count': 1}
    {'_id': 'Puerto Rican High School', 'count': 1}
    {'_id': 'Saint Dominic School', 'count': 1}
    {'_id': 'Sherwood Music School', 'count': 1}
    {'_id': 'Rosemont Elementary School', 'count': 1}
    {'_id': 'Rivers Trails Middle School', 'count': 1}
    {'_id': 'Johnson Elementary School', 'count': 1}
    {'_id': 'Cicero Elementary School', 'count': 1}
    {'_id': 'Independence Elementary School', 'count': 1}
    {'_id': 'Rush University', 'count': 1}
    {'_id': 'Redeemer School', 'count': 1}
    {'_id': 'Wood Oaks Junior High School', 'count': 1}
    {'_id': 'Walter R Sundling Junior High School', 'count': 1}
    {'_id': 'The Reading House', 'count': 1}
    {'_id': 'Westchester Primary School', 'count': 1}
    {'_id': 'John Wood Elementary School', 'count': 1}
    {'_id': 'Robina Lyle Elementary School', 'count': 1}
    {'_id': 'Wildwood Elementary School', 'count': 1}
    {'_id': 'Saint Adalbert School', 'count': 1}
    {'_id': 'Columbia Elementary School', 'count': 1}
    {'_id': 'Green Bay Road School', 'count': 1}
    {'_id': 'Saint Francis Cabrini Learning Center', 'count': 1}
    {'_id': 'Saint Elizabeth School', 'count': 1}
    {'_id': 'Saint Elizabeth Headstart', 'count': 1}
    {'_id': 'Saint Clara Headstart', 'count': 1}
    {'_id': 'Pierce School of International Studies', 'count': 1}
    {'_id': 'Forest Park Middle School', 'count': 1}
    {'_id': 'Hinsdale Middle School', 'count': 1}
    {'_id': 'Saint Cyrils School', 'count': 1}
    {'_id': 'Charles J Caruso Junior High School', 'count': 1}
    {'_id': 'Our Lady of Sorrows School', 'count': 1}
    {'_id': 'Oxford Community Center for Academics', 'count': 1}
    {'_id': 'Brian Piccolo Specialty School', 'count': 1}
    {'_id': 'Infant Jesus of Prague School', 'count': 1}
    {'_id': 'Portias Piano Methods School', 'count': 1}
    {'_id': 'Tilton Elementary School', 'count': 1}
    {'_id': 'Peiraikon Hellenic School', 'count': 1}
    {'_id': 'Keeler School', 'count': 1}
    {'_id': 'L H Day School', 'count': 1}
    {'_id': 'Faraday Elementary School', 'count': 1}
    {'_id': 'Mundelein College Lab Preschool and Kindergarten', 'count': 1}
    {'_id': 'Illinois Lutheran High School', 'count': 1}
    {'_id': 'Morton Career Academy', 'count': 1}
    {'_id': 'Saint Thomas of Canterbury Elementary School', 'count': 1}
    {'_id': 'Morton East High School', 'count': 1}
    {'_id': 'Thornridge High School', 'count': 1}
    {'_id': 'Laura S Ward Elementary School', 'count': 1}
    {'_id': 'Lawrence Hall School for Boys', 'count': 1}
    {'_id': 'Pulaski International School', 'count': 1}
    {'_id': 'Wheeling High School', 'count': 1}
    {'_id': 'Pals International School of Beauty Culture', 'count': 1}
    {'_id': 'George Rogers Clark Middle - High School', 'count': 1}
    {'_id': 'Arnett C Lines Elementary School', 'count': 1}
    {'_id': 'Nathan Hale Intermediate School', 'count': 1}
    {'_id': 'Naguib School of Sculpture', 'count': 1}
    {'_id': 'Loyola Law School', 'count': 1}
    {'_id': 'Wildwood School', 'count': 1}
    {'_id': 'Gary School', 'count': 1}
    {'_id': 'Logan Day Care Center for Retarded Children', 'count': 1}
    {'_id': 'Herzl Child-Parent Center', 'count': 1}
    {'_id': 'Roque De Duprey Elementary School', 'count': 1}
    {'_id': 'Holy Martyrs School', 'count': 1}
    {'_id': 'Hawthorn Center School', 'count': 1}
    {'_id': 'Saint Francis Xavier Roman Catholic School', 'count': 1}
    {'_id': 'Northwest Suburban School', 'count': 1}
    {'_id': 'Northwestern Business College', 'count': 1}
    {'_id': 'North Park Elementary School', 'count': 1}
    {'_id': 'Willowbrook Elementary School', 'count': 1}
    {'_id': 'Nu-Tek School of Beauty Culture', 'count': 1}
    {'_id': 'James B Eads Elementary School', 'count': 1}
    {'_id': 'Olive Child-Parent Center', 'count': 1}
    {'_id': 'Englewood High School', 'count': 1}
    {'_id': 'Oak Glen Elementary School', 'count': 1}
    {'_id': 'Park Vernon Learning Academy', 'count': 1}
    {'_id': 'Emerson Middle School', 'count': 1}
    {'_id': 'Palos East Elementary School', 'count': 1}
    {'_id': 'Sward Elementary School', 'count': 1}
    {'_id': 'Adlai Stevenson Elementary School', 'count': 1}
    {'_id': 'Carleton W Washburne School', 'count': 1}
    {'_id': 'Saratoga Elementary School', 'count': 1}
    {'_id': 'Dole Learning Center', 'count': 1}
    {'_id': 'Heritage Lakes Elementary School', 'count': 1}
    {'_id': 'Elgin Campus National - Louis University', 'count': 1}
    {'_id': 'Homer Iddings Elementary School', 'count': 1}
    {'_id': 'Northbrook Junior High School', 'count': 1}
    {'_id': 'Solomon Schecter School', 'count': 1}
    {'_id': 'Melody Elementary School', 'count': 1}
    {'_id': 'Alcuin Montessori School', 'count': 1}
    {'_id': 'Millennium Elementary School', 'count': 1}
    {'_id': 'Quigley Seminary', 'count': 1}
    {'_id': 'Prairie View Junior High School', 'count': 1}
    {'_id': 'Flossmoor Hills Elementary School', 'count': 1}
    {'_id': 'Saint Lukes School', 'count': 1}
    {'_id': 'Gospel Chapel', 'count': 1}
    {'_id': 'Bronzeville Lighthouse Charter School', 'count': 1}
    {'_id': 'Saint Emily School', 'count': 1}
    {'_id': 'Apollo Elementary School', 'count': 1}
    {'_id': 'Bible Baptist Christian Academy', 'count': 1}
    {'_id': 'Felician Sisters School', 'count': 1}
    {'_id': 'G Stanley Hall Elementary School', 'count': 1}
    {'_id': 'Fellowship Christian Academy', 'count': 1}
    {'_id': 'Minooka Elementary School', 'count': 1}
    {'_id': 'Trinity High School', 'count': 1}
    {'_id': 'Our Lady of the Wayside School', 'count': 1}
    {'_id': 'Harper College Northeast Center', 'count': 1}
    {'_id': 'Rowena Kyle Elementary School', 'count': 1}
    {'_id': 'James Edward School', 'count': 1}
    {'_id': 'Mother McAuley High School', 'count': 1}
    {'_id': 'Brook View School', 'count': 1}
    {'_id': 'Woodbine School', 'count': 1}
    {'_id': 'Hinton Elementary School', 'count': 1}
    {'_id': 'Christian Life College', 'count': 1}
    {'_id': 'Columbus Manor School', 'count': 1}
    {'_id': 'Pioneer School', 'count': 1}
    {'_id': 'George Williams College Education Center', 'count': 1}
    {'_id': 'Willows Academy', 'count': 1}
    {'_id': 'Lexington Elementary School', 'count': 1}
    {'_id': 'Wing It School', 'count': 1}
    {'_id': 'Walther Lutheran High School', 'count': 1}
    {'_id': 'Greenbrook Elementary School', 'count': 1}
    {'_id': 'Dujardin Elementary School', 'count': 1}
    {'_id': 'Well Home', 'count': 1}
    {'_id': 'Sienna High School', 'count': 1}
    {'_id': 'Sandburg Elementary School', 'count': 1}
    {'_id': 'West Suburban School', 'count': 1}
    {'_id': 'Brunswick Elementary School', 'count': 1}
    {'_id': 'Ravenswood Elementary School', 'count': 1}
    {'_id': 'Governors State University', 'count': 1}
    {'_id': 'Wesleyan Missionary Academy', 'count': 1}
    {'_id': 'Maywood Elementary School', 'count': 1}
    {'_id': 'Shabanee School', 'count': 1}
    {'_id': 'Anne Fox Elementary School', 'count': 1}
    {'_id': 'Westside Preparatory School', 'count': 1}
    {'_id': 'John Hersey High School', 'count': 1}
    {'_id': 'Wilhelm K Roentgen School', 'count': 1}
    {'_id': 'Morton West High School', 'count': 1}
    {'_id': 'Wharton School', 'count': 1}
    {'_id': 'Southtown Day Care Center', 'count': 1}
    {'_id': 'Southside Language Center', 'count': 1}
    {'_id': 'South Shore Pre-School', 'count': 1}
    {'_id': 'Saint Francis de Sales High School', 'count': 1}
    {'_id': 'Worth Elementary School', 'count': 1}
    {'_id': 'Hoosier Boys Town', 'count': 1}
    {'_id': 'Tanksons Martial Arts Academy', 'count': 1}
    {'_id': 'Peter Hoy School', 'count': 1}
    {'_id': 'Ted Liss Studio', 'count': 1}
    {'_id': '7th Day Adventist North Shore School', 'count': 1}
    {'_id': 'Glen Grove Elementary School', 'count': 1}
    {'_id': 'Southwest Cooperative Pre-School', 'count': 1}
    {'_id': 'Special Religious Education', 'count': 1}
    {'_id': 'Sisters of Notre Dame School', 'count': 1}
    {'_id': 'Junior Hall School', 'count': 1}
    {'_id': 'Saint Mark Headstart Center', 'count': 1}
    {'_id': 'Institute of Islamic Education', 'count': 1}
    {'_id': 'Truth-Child Parent Center', 'count': 1}
    {'_id': 'Three Kittens Day Nursery and Kindergarten', 'count': 1}
    {'_id': 'Greeley Elementary School', 'count': 1}
    {'_id': 'Thurgood Marshall Elementary School', 'count': 1}
    {'_id': 'Telshe Yeshiva', 'count': 1}
    {'_id': 'River Forest Junior-Senior High School', 'count': 1}
    {'_id': 'Elsie Wadsworth Elementary School', 'count': 1}
    {'_id': 'Saint Mary of Nazareth Hospital School of Nursing', 'count': 1}
    {'_id': 'Brisk Rabbinical College', 'count': 1}
    {'_id': 'Saint Mels Grade School', 'count': 1}
    {'_id': 'School of Ukrainian Studies', 'count': 1}
    {'_id': 'Meadowbrook Elementary School', 'count': 1}
    {'_id': 'Terry Town Nursery School and Kindergarten', 'count': 1}
    {'_id': 'Second Chance Tutoring', 'count': 1}
    {'_id': 'Sears YMCA Day Care Center', 'count': 1}
    {'_id': 'Saint Therese School', 'count': 1}
    {'_id': 'SaMer Sewing Center', 'count': 1}
    {'_id': 'Satellite School', 'count': 1}
    {'_id': 'Belmont-Cragin Community Area School', 'count': 1}
    {'_id': 'Epiphany School', 'count': 1}
    {'_id': 'Saint Hilary School', 'count': 1}
    {'_id': 'Galapagos Charter School', 'count': 1}
    {'_id': 'Glenview New Church School', 'count': 1}
    {'_id': 'Yale Elementary School', 'count': 1}
    {'_id': 'Ruth Page Foundation School of Dance', 'count': 1}
    {'_id': 'Maplewood Elementary School', 'count': 1}
    {'_id': 'Lloyd Elementary School', 'count': 1}
    {'_id': 'Living Word Christian Academy', 'count': 1}
    {'_id': "Saint Paul's School", 'count': 1}
    {'_id': 'Saint Basil School', 'count': 1}
    {'_id': 'Saint Alexis School', 'count': 1}
    {'_id': 'Isaac Fox School', 'count': 1}
    {'_id': 'Joliet - Lockport Seventh Day Adventist School', 'count': 1}
    {'_id': 'Orland Park Elementary School', 'count': 1}
    {'_id': 'Harvey Academic Preparatory Center', 'count': 1}
    {'_id': "Saint Joseph's Catholic School", 'count': 1}
    {'_id': 'Saint Denis School', 'count': 1}
    {'_id': 'Quin School', 'count': 1}
    {'_id': 'Wilco Career Center', 'count': 1}
    {'_id': 'Orland Junior High School', 'count': 1}
    {'_id': 'Mitchell Elementary School', 'count': 1}
    {'_id': 'Diamond Lake Elementary School', 'count': 1}
    {'_id': 'Christian Hills School', 'count': 1}
    {'_id': 'Otis Elementary School', 'count': 1}
    {'_id': 'Scarlet Oak Elementary School', 'count': 1}
    {'_id': 'Saint Columbkille School', 'count': 1}
    {'_id': 'Saint Joseph Parish School', 'count': 1}
    {'_id': 'Stone Church Christian Academy', 'count': 1}
    {'_id': 'Jahn Elementary School', 'count': 1}
    {'_id': 'Doctor School', 'count': 1}
    {'_id': 'Quentin Road Christian School', 'count': 1}
    {'_id': 'Joseph L Block Junior High School', 'count': 1}
    {'_id': 'Lee L Caldwell Elementary School', 'count': 1}
    {'_id': 'George Leland Elementary School', 'count': 1}
    {'_id': 'Lindop School', 'count': 1}
    {'_id': 'Indiana Vocational - Technical College', 'count': 1}
    {'_id': 'Dulles School', 'count': 1}
    {'_id': 'Ernest R Elliott Elementary School', 'count': 1}
    {'_id': 'Henry P Fieler Elementary School', 'count': 1}
    {'_id': 'Joliet Academy', 'count': 1}
    {'_id': 'Glen Park School', 'count': 1}
    {'_id': 'Warren G Harding Elementary School', 'count': 1}
    {'_id': 'Hayes-Leonard Elementary School', 'count': 1}
    {'_id': 'Saint Edmund School', 'count': 1}
    {'_id': 'Hosford Park Elementary School', 'count': 1}
    {'_id': 'Kolling Elementary School', 'count': 1}
    {'_id': 'Alain L Locke Elementary School', 'count': 1}
    {'_id': 'Edgar L Miller Elementary School', 'count': 1}
    {'_id': 'Morton Senior High School', 'count': 1}
    {'_id': 'Morton Elementary School', 'count': 1}
    {'_id': 'Spring Hills Elementary School', 'count': 1}
    {'_id': 'Horace S Norton Elementary School', 'count': 1}
    {'_id': 'Donoghue Elementary School', 'count': 1}
    {'_id': 'Peifer Elementary School', 'count': 1}
    {'_id': 'Lane Technical High School', 'count': 1}
    {'_id': 'Purdue University-Calumet', 'count': 1}
    {'_id': 'Ashburn Community Area Academy', 'count': 1}
    {'_id': 'Saint Adalherts School', 'count': 1}
    {'_id': 'Saint Catherine of Siena School', 'count': 1}
    {'_id': 'Saint Hedricks School', 'count': 1}
    {'_id': 'A L Spohn Elementary/Middle School', 'count': 1}
    {'_id': 'Ellington Elementary School', 'count': 1}
    {'_id': 'West Side High School', 'count': 1}
    {'_id': 'Riley Elementary School', 'count': 1}
    {'_id': 'Valparaiso High School (historical)', 'count': 1}
    {'_id': 'Beecher School', 'count': 1}
    {'_id': 'Whittier School', 'count': 1}
    {'_id': 'Boone Grove Elementary School', 'count': 1}
    {'_id': 'Crisman Elementary School', 'count': 1}
    {'_id': 'Chicago Christian High School', 'count': 1}
    {'_id': 'Boone Grove Junior-Senior High School', 'count': 1}
    {'_id': 'Saint Edward School', 'count': 1}
    {'_id': 'Kilmer Elementary School', 'count': 1}
    {'_id': 'Pierce Middle School', 'count': 1}
    共有学校 2839 所
    {'_id': 'Central Middle School', 'count': 2}
    {'_id': 'Algonquin Middle School', 'count': 2}
    {'_id': 'Highland Middle School', 'count': 2}
    {'_id': 'Barrington Middle School', 'count': 2}
    {'_id': 'Dirksen Middle School', 'count': 1}
    {'_id': 'Frederick Douglass Middle School', 'count': 1}
    {'_id': 'Hinsdale Middle School', 'count': 1}
    {'_id': 'Ames Middle School', 'count': 1}
    {'_id': 'Irving Park Middle School', 'count': 1}
    {'_id': 'Colonel John Wheeler Middle School', 'count': 1}
    {'_id': 'Golf Middle School and Technology Center', 'count': 1}
    {'_id': 'Kaneland Harter Middle School', 'count': 1}
    {'_id': 'Attea Middle School', 'count': 1}
    {'_id': 'Gregory R. Fischer Middle School', 'count': 1}
    {'_id': 'Robert Taft Middle School', 'count': 1}
    {'_id': 'Glenn Westlake Middle School', 'count': 1}
    {'_id': 'Miriam G. Canter Middle School', 'count': 1}
    {'_id': 'Highcrest Middle School', 'count': 1}
    {'_id': 'Jewel Middle School', 'count': 1}
    {'_id': 'Haines Middle School', 'count': 1}
    {'_id': 'Kenyon Woods Middle School', 'count': 1}
    {'_id': 'John Middleton Elementary School', 'count': 1}
    {'_id': 'Oliver McCracken Middle School', 'count': 1}
    {'_id': 'Heineman Middle School', 'count': 1}
    {'_id': 'A Vito Martinez Middle School', 'count': 1}
    {'_id': 'Brookwood Middle School', 'count': 1}
    {'_id': 'Eastview Middle School', 'count': 1}
    {'_id': 'Dundee Middle School', 'count': 1}
    {'_id': 'Hubert H Humphrey Middle School', 'count': 1}
    {'_id': 'West Oak Middle School', 'count': 1}
    {'_id': 'Oliver W Holmes Middle School', 'count': 1}
    {'_id': 'Ellis Middle School', 'count': 1}
    {'_id': 'Circle Center Middle School', 'count': 1}
    {'_id': 'Clarence E. Culver Middle School', 'count': 1}
    {'_id': 'Hale Middle School', 'count': 1}
    {'_id': 'Canton Middle School', 'count': 1}
    {'_id': 'Emerson Middle School', 'count': 1}
    {'_id': 'O W Huth Middle School', 'count': 1}
    {'_id': 'South Middle School', 'count': 1}
    {'_id': 'Gregory Middle School', 'count': 1}
    {'_id': 'A L Spohn Elementary/Middle School', 'count': 1}
    {'_id': 'Kerr Middle School', 'count': 1}
    {'_id': 'Thompson Middle School', 'count': 1}
    {'_id': 'Carl Sandburg Middle School', 'count': 1}
    {'_id': 'Marquardt Middle School', 'count': 1}
    {'_id': 'Shabbona Middle School', 'count': 1}
    {'_id': 'Heritage Middle School', 'count': 1}
    {'_id': 'Carpentersville Middle School', 'count': 1}
    {'_id': 'Monroe Middle School', 'count': 1}
    {'_id': 'Schrum Memorial Middle School', 'count': 1}
    {'_id': 'Franklin Middle School', 'count': 1}
    {'_id': 'Jane Addams Middle School', 'count': 1}
    {'_id': 'Whittier Campus Kerr Middle School', 'count': 1}
    {'_id': 'Washington Middle School', 'count': 1}
    {'_id': 'Chase Alternative Middle School', 'count': 1}
    {'_id': "O'Neill Middle School", 'count': 1}
    {'_id': 'Edison Middle School', 'count': 1}
    {'_id': 'Thomas Middle School', 'count': 1}
    {'_id': 'Kimball Middle School', 'count': 1}
    {'_id': 'Schiller Middle School', 'count': 1}
    {'_id': 'Chippewa Middle School', 'count': 1}
    {'_id': 'Gurrie Middle School', 'count': 1}
    {'_id': 'Oster-Oakview Middle School', 'count': 1}
    {'_id': 'Gower Middle School', 'count': 1}
    {'_id': 'Rotolo Middle School', 'count': 1}
    {'_id': 'Jefferson Middle School', 'count': 1}
    {'_id': 'Abbott Middle School', 'count': 1}
    {'_id': 'Larsen Middle School', 'count': 1}
    {'_id': 'Westview Hills Middle School', 'count': 1}
    {'_id': 'Westchester Middle School', 'count': 1}
    {'_id': 'Crete-Monee Middle School', 'count': 1}
    {'_id': 'Lake Zurich Middle School', 'count': 1}
    {'_id': 'Lake Zurich Middle School South Campus', 'count': 1}
    {'_id': 'Geneva Middle School North', 'count': 1}
    {'_id': 'Gwendolyn Brooks Middle School', 'count': 1}
    {'_id': 'John L. Lukanic Middle School', 'count': 1}
    {'_id': 'Thurgood Marshall Middle School', 'count': 1}
    {'_id': 'Spring Wood Middle School', 'count': 1}
    {'_id': 'Dunbar-Pulaski Middle School', 'count': 1}
    {'_id': 'Parks Middle School', 'count': 1}
    {'_id': 'Lincoln Hall Middle School', 'count': 1}
    {'_id': 'Bernard J Ward Middle School', 'count': 1}
    {'_id': 'Lake Ridge Middle School', 'count': 1}
    {'_id': 'Tefft Middle School', 'count': 1}
    {'_id': 'Maple Middle School', 'count': 1}
    {'_id': 'Prairie Knolls Middle School', 'count': 1}
    {'_id': 'Chute Middle School', 'count': 1}
    {'_id': 'Charles N Scott Middle School', 'count': 1}
    {'_id': 'Benjamin Franklin Middle School', 'count': 1}
    {'_id': 'Lincoln Middle School', 'count': 1}
    {'_id': 'Medinah Middle School', 'count': 1}
    {'_id': 'Haven Middle School', 'count': 1}
    {'_id': 'C F Simmons Middle School', 'count': 1}
    {'_id': 'Henry W, Eggers Elementary - Middle School', 'count': 1}
    {'_id': 'Middlefork Primary School', 'count': 1}
    {'_id': 'Henry W Cowherd Middle School', 'count': 1}
    {'_id': 'Walter H Dyett Middle School', 'count': 1}
    {'_id': 'Cottage Grove Middle School', 'count': 1}
    {'_id': 'Roosevelt Middle School', 'count': 1}
    {'_id': 'Edgewood Middle School', 'count': 1}
    {'_id': 'West Chicago Middle School', 'count': 1}
    {'_id': 'John E Albright Middle School', 'count': 1}
    {'_id': 'Deer Path Middle School', 'count': 1}
    {'_id': 'Thayer J Hill Middle School', 'count': 1}
    {'_id': 'William Fegely Middle School', 'count': 1}
    {'_id': 'Jay Stream Middle School', 'count': 1}
    {'_id': 'Bailly Middle School', 'count': 1}
    {'_id': 'Michael Grimmer Middle School', 'count': 1}
    {'_id': 'Mannhem Middle School', 'count': 1}
    {'_id': 'Glenside Middle School', 'count': 1}
    {'_id': 'Columbia Central Middle School', 'count': 1}
    {'_id': 'Roselle Middle School', 'count': 1}
    {'_id': 'Lake Bluff Middle School', 'count': 1}
    {'_id': 'Wauconda Middle School', 'count': 1}
    {'_id': 'Wilbur Wright Middle School', 'count': 1}
    {'_id': 'Arbor Park Middle School', 'count': 1}
    {'_id': 'Cooper Middle School', 'count': 1}
    {'_id': 'Granger Middle School', 'count': 1}
    {'_id': 'MacArthur Middle School', 'count': 1}
    {'_id': 'Clark Middle School', 'count': 1}
    {'_id': 'Rivers Trails Middle School', 'count': 1}
    {'_id': 'Northlake Middle School', 'count': 1}
    {'_id': 'George Rogers Clark Middle - High School', 'count': 1}
    {'_id': 'Donald E Gavit Middle/High School', 'count': 1}
    {'_id': 'Harrison Middle School', 'count': 1}
    {'_id': 'Kahler Middle School', 'count': 1}
    {'_id': 'Palos South Middle School', 'count': 1}
    {'_id': 'Herget Middle School', 'count': 1}
    {'_id': 'Pierce Middle School', 'count': 1}
    {'_id': 'Hobart Middle School', 'count': 1}
    {'_id': 'Forest Park Middle School', 'count': 1}
    {'_id': 'Alfred Beckman Middle School', 'count': 1}
    {'_id': 'Wredling Middle School', 'count': 1}
    {'_id': 'Tolleston Middle School', 'count': 1}
    {'_id': 'Kennedy-King Middle School', 'count': 1}
    {'_id': 'Nichols Middle School', 'count': 1}
    {'_id': 'Union Township Middle School', 'count': 1}
    {'_id': 'Deerpath Middle School', 'count': 1}
    {'_id': 'Willowcreek Middle School', 'count': 1}
    {'_id': 'Troy Middle School', 'count': 1}
    中学共有 140 所
    

middle学校数据经由以下24名用户提交，最多提交次数83次，大部分都提交1个条。数据贡献集中在'iandees' 与 'Umbugbene'.针对用户iandees进行分析，得知该用户在各类数据节点都有贡献，贡献度最高的是完善了39483个node节点数据，并且提交了1925条学校信息和自行车出租(bicycle_rental)信息。以上三项是该用户在芝加哥开放数据中贡献最多的部分


```python

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



```

    ---------------------------------根据amenity=school,统计提交人情况统计设施次数----------------------------------------------
    {'_id': 'iandees', 'count': 83}
    {'_id': 'Umbugbene', 'count': 29}
    {'_id': 'mpinnau', 'count': 5}
    {'_id': 'Kristian M Zoerhoff', 'count': 5}
    {'_id': 'Sundance', 'count': 3}
    {'_id': 'bbmiller', 'count': 1}
    {'_id': 'GXCEB0TOSM', 'count': 1}
    {'_id': 'TMLutas', 'count': 1}
    {'_id': 'Drew2324', 'count': 1}
    {'_id': 'OSMF Redaction Account', 'count': 1}
    {'_id': 'JaapK', 'count': 1}
    {'_id': 'Eliyak', 'count': 1}
    {'_id': 'Steven Vance', 'count': 1}
    {'_id': 'mappy123', 'count': 1}
    {'_id': 'Geo_Liz', 'count': 1}
    {'_id': 'patester24', 'count': 1}
    {'_id': '42429', 'count': 1}
    {'_id': 'BeatlesZeppelinRush', 'count': 1}
    {'_id': 'DaBunny', 'count': 1}
    {'_id': 'lgoughenour', 'count': 1}
    {'_id': 'Thyais Meade', 'count': 1}
    {'_id': 'JWAddison', 'count': 1}
    {'_id': 'jbk123', 'count': 1}
    {'_id': 'Forest Gregg', 'count': 1}
    共有 24 名用户提交
    


```python

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
```

    ---------------------------------根据user=iandees,统计提交人情况统计设施次数----------------------------------------------
    {'_id': 'node', 'count': 39483}
    {'_id': 'way', 'count': 3435}
    {'_id': 'relation', 'count': 7}
    iandees在 3 类节点提交数据
    
    
    {'_id': None, 'count': 39683}
    {'_id': 'school', 'count': 1925}
    {'_id': 'bicycle_rental', 'count': 298}
    {'_id': 'grave_yard', 'count': 206}
    {'_id': 'restaurant', 'count': 153}
    {'_id': 'fast_food', 'count': 151}
    {'_id': 'place_of_worship', 'count': 121}
    {'_id': 'post_office', 'count': 87}
    {'_id': 'parking', 'count': 72}
    {'_id': 'hospital', 'count': 61}
    {'_id': 'cafe', 'count': 26}
    {'_id': 'bank', 'count': 21}
    {'_id': 'pub', 'count': 20}
    {'_id': 'fuel', 'count': 19}
    {'_id': 'pharmacy', 'count': 10}
    {'_id': 'bicycle_parking', 'count': 8}
    {'_id': 'post_box', 'count': 7}
    {'_id': 'bar', 'count': 6}
    {'_id': 'gym', 'count': 5}
    {'_id': 'bench', 'count': 5}
    {'_id': 'parking_entrance', 'count': 4}
    {'_id': 'fire_station', 'count': 3}
    {'_id': 'car_wash', 'count': 3}
    {'_id': 'theatre', 'count': 3}
    {'_id': 'car_sharing', 'count': 3}
    {'_id': 'veterinary', 'count': 2}
    {'_id': 'insurance', 'count': 2}
    {'_id': 'charging_station', 'count': 2}
    {'_id': 'dentist', 'count': 2}
    {'_id': 'library', 'count': 2}
    {'_id': 'car_rental', 'count': 2}
    {'_id': 'kindergarten', 'count': 2}
    {'_id': 'toilets', 'count': 1}
    {'_id': 'clinic', 'count': 1}
    {'_id': 'ice_cream', 'count': 1}
    {'_id': 'dance_theater', 'count': 1}
    {'_id': 'hookah_lounge', 'count': 1}
    {'_id': 'auto_impound', 'count': 1}
    {'_id': 'spa', 'count': 1}
    {'_id': 'telephone', 'count': 1}
    {'_id': 'atm', 'count': 1}
    {'_id': 'shop', 'count': 1}
    {'_id': 'cinema', 'count': 1}
    iandees在 43 种amenity设施种类下提交
    

#### 业务分析实现后的数据建议
数据格式相对固定，但是数据源还是存在很多不规范的缩写，随意性很强。比如addr.CT,Rd,rd类似的大小写区分不规范，在数据使用之前需要进行手工处理重新归类。数据分类使用: 作为分隔符感觉不是很合理，既然xml文件是否更应该充分利用xml的格式特定进行处理，虽然层次多，但可以做到更明显。过去一般都针对几十MB的xml进行全文档树结构加载，因此局限性很大。本次试用iterparse效果远比全树加载好。
xml文件在使用过程中对详细的字段应用方式没有很明确的说明，基本是参考相关案例和项目练习内容进行的编写，并且在不断试错中进行修改猜得到相对完整的数据拆分方法。但依旧不确认所进行的数据清洗是否已全面覆盖必要数据项

#### 建议及预期效果
##### 建议1
数据单位统一，数据变量(tag)规范化
所有数据格式应当统一，各类标签内的字符串应当合理使用相同的缩写，而不能自成一套
数据单位需要统一，虽然本次统计数据没有涉及到太多数值类参数，但根据相关项目和案例介绍，数值类数据中由于缺少约束，一定会出现"800"和"800m"并存，zipcode出现非数字字母的情况。因此在数据采集录入时，建议针对相关字段进行数据约束，保存之前检查数据合法性，如联系电话符合当地区号-电话长度等。缩写识别后给出统一代替或者修改

##### 建议二
单个数据文件中贡献度的差异
众人拾柴火焰高，目前可见很多数据的提交集中在某一些人或者某几个人身上，这种现象表达出openstreetmap中数据来源单一性，是否可能集中表现了几位义务贡献者的意志，以及很多详细的更多维度的数据描述还没有人提供。我相信这个标准四海内皆准。中国地图之前我下载过，单个文件远没有芝加哥城这么大，印象中之前尝试过下载香港中文数据，以降低数据理解难度，但后续由于找不到源，还是采用了一开始下载的芝加哥全数据。而香港地图大小貌似也大于北京地图，而实际情况来看，北京市全市数据内容理论上会接近芝加哥城市或至少大于香港地图数据。如何推动提升贡献者活跃度以及提供何种便利的数据采集方式是将来会面临的问题。比如在当前发展环境下，是否可以采用手机数据收集、实时反馈的形式进行标记，利用国内微信、国外line等工具的LBS特性由用户主动方便的提交所在地点数据集，通过这种方式能够迅速补充各国各地的相关数据。目前我了解到的Mapsme很有可能采用的就是openstreetmap地图。如果能够得到更多的数据补充，作为旅游者手中相对方便的离线地图更有益处，或者说通过这种旅游工具让更多游客自发上传数据内容

#### 项目参考说明
历史学生完成的优秀案例

https://github.com/baumanab/udacity_mongo_github/tree/master/final_project

数据内存占用的性能评价

https://pycoders-weekly-chinese.readthedocs.io/en/latest/issue6/processing-xml-in-python-with-element-tree.html

数据处理查询的技能点,包括mongo,xml处理形式

https://stackoverflow.com/search?q=python+pymongo
https://stackoverflow.com/questions/tagged/python+xml+et


```python

```
