#!/usr/bin/env python

import json

j = json.load(file("default-fixture.json"))

new_list = []
count_keep = 0
count_drop = 0
for item in j:
    if item["model"] != "posts.postview":
	new_list.append(item)
	count_keep += 1
    else:
	count_drop += 1

print("Num rows removed: {}".format(count_drop))
print("Num rows kept: {}".format(count_keep))
json.dump(new_list, file("default-fixture.json", 'w'))
print("Overwrote file")
