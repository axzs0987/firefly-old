from compile_notebook.read_ipynb import read_ipynb
from compile_notebook.LR_matching import Feeding
from compile_notebook.LR_matching import LR_run

import configparser
import pymysql
import numpy as np

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

def get_code_txt(path):
    cot_txt = ""
    lis = read_ipynb(path)
    # LR matching
    lis = Feeding(lis)
    lis = LR_run(lis)
    for paragraph in lis:
        # print(item)
        for item in paragraph['code']:
            if item:
                if (item[0] == '!') or (item[0] == '<' or (item[0] == '%')):
                    continue
            temp = item + '\n'
            cot_txt += temp
    return cot_txt

def create_connection():
    global CONFIG
    db_host = CONFIG.get('database', 'host')
    db_user = CONFIG.get('database', 'user')
    db_passwd = CONFIG.get('database', 'passwd')
    db_dataset = CONFIG.get('database', 'dataset')
    db = pymysql.connect(db_host, db_user, db_passwd, db_dataset, charset='utf8')
    cursor = db.cursor()
    return cursor,db

def insert_db(table, column_list, value_list):
    cursor,db = create_connection()
    sql = "INSERT INTO "
    sql += table
    sql += " ("
    count = 0
    for i in column_list:
        sql += i
        if count != len(column_list) - 1:
            sql += ','
            count += 1
        else:
            sql += ')'
    sql += " VALUES ("
    count = 0
    for i in value_list:
        if type(i).__name__ == 'int':
            sql += str(i)
        else:
            i = str(i)
            if i[-1] == '\n':
                i = i[0:-1]
            if i[0] == '\'' and i[-1] == '\'':
                i = i[1:-1]

            if '\'' in i:
                i = i.replace('\'','\\\'')

            if '\"' in i:
                i = i.replace('\"','\\\"')

            if i[0] != '\'' or i[-1] != '\'':
                sql = sql + '\'' + i + '\''
            else:
                sql += i

        if count != len(value_list)-1:
            sql += ','
            count += 1
        else:
            sql += ')'

    try:
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        print("\033[0;32;40m\tsql fail\033[0m")
        print(e)
        return "ERROR"
       # Rollback in case there is any error
        db.rollback()

    # 关闭数据库连接
    db.close()
    return "SUCCEED"

def update_db(table, old_column, new_value, condition_column, compare_operator, condition_value):
    cursor, db = create_connection()
    sql = "UPDATE " + table + " SET " + old_column + " = " + new_value + " WHERE " + condition_column + compare_operator + condition_value
    try:
        cursor.execute(sql)
        db.commit()
    except:
        print("\033[0;32;40m\tsql fail\033[0m")
        print(e)
        db.rollback()
        return "ERROR"
    db.close()
    return "SUCCEED"

def add_result(notebook_id, type, content):
    column_list = ["notebook_id","tyoe","content"]
    value_list = [notebook_id, type, content]
    return insert_db("result", column_list, value_list)

def check_model(notebook_id):
    cursor, db = create_connection()
    sql = "SELECT * FROM model WHERE notebook_id=" + str(notebook_id)
    cursor.execute(sql)
    sql_res = cursor.fetchall()
    is_in = False
    for row in sql_res:
        is_in = True
        break
    return is_in


def add_model(notebook_id, model_type):
    global CONFIG

    model_type_list_str = CONFIG.get("models", "model_task")
    model_type_list_str = model_type_list_str[1:-1]
    model_type_list = model_type_list_str.split(',')
    new_model_type_list = []
    for i in model_type_list:
        new_model_type_list.append(int(i[-1]))
    task_type = new_model_type_list[model_type-1]

    is_in = check_model(notebook_id)
    if is_in == True:
        value_list = [notebook_id, model_type, task_type]
        column_list = ["notebook_id", "model_type", "task_type"]
        return insert_db("model", column_list, value_list)
    else:
        return "ALREADY EXIST"

def add_operator(notebook_id, rank, data_object, operator, physic_operation, parameter_code_dict, parameter_type_dict):
    global CONFIG
    logic_operation = eval(CONFIG.get('operators', 'operations'))[operator]['logic_operations']
    value_list = [
        notebook_id,
        rank,
        logic_operation,
        data_object,
        physic_operation,
        operator
    ]
    column_list = [
        "notebook_id",
        "rank",
        "logic_operation",
        "data_object",
        "physic_operation",
        "operator"
    ]
    parameter_keys = eval(CONFIG.get('operators', 'operations'))[operator]['params']
    for i in range(0, len(parameter_keys)): #遍历这个操作下的所有参数名
        if(parameter_keys[i] in parameter_code_dict and parameter_keys[i] in parameter_type_dict): #如果传进来的参数字典包含这个字段
            column_name = "parameter_" + str(i+1)
            column_list.append(column_name + '_code')
            column_list.append(column_name + '_type')
            column_list.append(column_name + '_name')
            value_list.append(parameter_code_dict[parameter_keys[i]])
            value_list.append(parameter_type_dict[parameter_keys[i]])
            value_list.append(parameter_keys[i])

    return insert_db("operator", column_list, value_list)

def add_sequence_from_walk_logs(walk_logs, save_path):
    if walk_logs['is_img'] == True:
        print("\033[0;33;40m\timage dataset pass\033[0m")
        return
    if len(walk_logs['operator_sequence'])==0:
        print("\033[0;33;40m\tsequence length is 0\033[0m")
        return
    if len(walk_logs['models'])==0:
        print("\033[0;33;40m\tmodel number is 0\033[0m")
        return

    notebook_id = walk_logs['notebook_id']
    for model in walk_logs['models']:
        res1 = add_model(notebook_id, model)
    if res1 == 'ERROR':
        return res1
    count = 1
    for operator_node in walk_logs['operator_sequence']:
        res2 = add_operator(notebook_id, count, operator_node["data_object"], operator_node["operator_name"], operator_node['physic_operation'], operator_node['parameter_code'], operator_node['parameter_type'])
        count += 1
        if res2 == 'ERROR':
            return res2

    np.save(save_path + '/' + walk_logs['notebook_title'] + '.npy', walk_logs)
    res3 = update_db("notebook", "add_sequence", '1', 'id', "=", str(walk_logs["notebook_id"]))
    if res3 == 'ERROR':
        return res2

    print("\033[0;32;40m\tsucceed\033[0m")
    return "SUCCEED"
def get_batch_notebook_info():
    cursor, db = create_connection()
    sql = "SELECT id,title FROM notebook WHERE add_sequence=0"
    cursor.execute(sql)
    sql_res = cursor.fetchall()
    result = []
    for row in sql_res:
        notebook_info = (row[0],row[1])
        result.append(notebook_info)
    return result

if __name__ == '__main__':
    CONFIG = configparser.ConfigParser()
    CONFIG.read('config.ini')
    model_dic = eval(CONFIG.get('operators', 'operations'))
    print(type(model_dic))