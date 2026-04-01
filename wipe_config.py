import json, os
cfg_file = "config/config.json"
if os.path.exists(cfg_file):
    with open(cfg_file, "r") as f:
        data = json.load(f)
    if "chat_key" in data: data["chat_key"] = ""
    if "embed_key" in data: data["embed_key"] = ""
    with open(cfg_file, "w") as f:
        json.dump(data, f)
