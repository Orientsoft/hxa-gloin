

for i in range(100):
    num = 2638+i
    print(num)
    a=f'L210405{num}.045.MMI'
    f=open(a,'w')
    f.write('1')