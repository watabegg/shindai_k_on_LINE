import pandas

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