# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 23:27:06 2019
@author: Qinliang Xue
"""
import json


def read_ipynb(path):
    '''input a ipynb path,
    output a list(dic)'''
    # ipynb file is a json structure filex
    listdic = []
    with open(path, 'r', encoding='utf-8') as f:
        cells = json.load(f)['cells']
    for i in range(len(cells)):
        if i == 0 and cells[i]['cell_type'] != 'markdown':  # means notebook starting
            dic = {'text': 'This is the start of notebook.', 'code': []}
            for j in range(i, len(cells)):
                if cells[j]['cell_type'] == 'markdown':
                    i = j - 1
                    break
                elif cells[j]['cell_type'] == 'code':
                    codestr = ''.join(cells[j]['source'])
                    dic['code'].append(codestr)
            listdic.append(dic)
        if cells[i]['cell_type'] == 'markdown': #match all the codes in one markdown block
            dic = {'text': ''.join(cells[i]['source']), 'code': []}
            for j in range(i + 1, len(cells)):
                if cells[j]['cell_type'] == 'markdown':
                    i = j - 1
                    break
                elif cells[j]['cell_type'] == 'code':
                    codestr = ''.join(cells[j]['source'])
                    dic['code'].append(codestr)
            listdic.append(dic)
    return listdic


def ipynb2py(ipypath, pypath):
    '''input a ipynb path,
    create a python file from this ipynb file'''
    with open(ipypath, 'r', encoding='utf-8') as f:
        cells = json.load(f)['cells']
    wstr = ''
    for i in range(len(cells)):
        if cells[i]['cell_type'] == 'markdown':
            for j in cells[i]['source']:
                wstr += ('# ' + j)
            wstr += '\n\n'
        elif cells[i]['cell_type'] == 'code':
            wstr += "# In[" + str(cells[i]['execution_count']) + "]\n\n"
            for j in cells[i]['source']:
                wstr += j
            wstr += '\n\n'
    with open(pypath, "w", encoding='utf-8') as f:
        f.write(wstr)

def get_code_txt(path):
    cot_txt = ""
    lis = read_ipynb(path)
    for paragraph in lis:
        for item in paragraph['code']:
            if item:
                if(item[0] == '!') or (item[0] == '<' or (item[0] == '%')):
                    continue
            temp = item + '\n'
            cot_txt += temp

    return cot_txt
if __name__ == '__main__':
    print(get_code_txt("./data/dummies-for-dummies.ipynb"))