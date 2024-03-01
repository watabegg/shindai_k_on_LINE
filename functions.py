import pandas, itertools

def part_str(data): # パートの配列を日本語に直す関数
    part = pandas.read_csv("./templates/part.csv", header=None).values.tolist()
    part_str = ''
    if len(data) != len(part[0]):
        for i in range(0,len(data)):
            part_str = part_str + part[0][part[1].index(data[i])] + ','

        return part_str[:-1]
    
    else:
        return 'バンド練習'
    
def part_prd(data):
    part_prd = 1
    try:
        for num in data:
            part_prd *= int(num)
    except ValueError as e:
        return f'パート入力エラー:{e}', 500

    return part_prd

def part_prime(comp_list): # SQLからfetchした生の二次元パート配列を因数分解して一次元にして返す
    part = pandas.read_csv("./templates/part.csv", header=None).values.tolist()
    reserved_part = []
    for i in comp_list:
        for j in part[1]:
            if i[0] % j == 0:
                reserved_part.append(j)
    
    result = [0 if x in reserved_part else x for x in part[1]]
    return result