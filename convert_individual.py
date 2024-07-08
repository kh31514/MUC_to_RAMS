from helper_functions import *
import jsonlines
import json

ind = 102

if __name__ == "__main__":
    f = open('data/MUC_raw/MUC_consolidation.json')
    data = json.load(f)

    with jsonlines.open('data/MUC_converted/indices/MUC_'+str(ind)+'.json', mode='a') as writer:
        writer.write(convert_by_ind(data, ind))

    f.close()
