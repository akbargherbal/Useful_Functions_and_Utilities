'''Split the huge json file named huge_json.json;  10 smaller json files.'''
import json
with open('huge_json.json') as f:
    data = json.load(f)
    for i in range(10):
        with open('smaller_json_'+str(i)+'.json', 'w') as outfile:
            json.dump(data[i*100000:(i+1)*100000], outfile)