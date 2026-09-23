import json
import yaml
import sys


mode = sys.argv[1]

config_file = sys.argv[2]

best_file = sys.argv[3]


with open(config_file) as f:
    config = yaml.safe_load(f)



if mode == "auto":

    with open(best_file) as f:
        params = json.load(f)


else:

    params = config["dada2"]["manual"]



print(params["trim_left_f"])
print(params["trim_left_r"])
print(params["trunc_len_f"])
print(params["trunc_len_r"])
print(params["max_ee_f"])
print(params["max_ee_r"])