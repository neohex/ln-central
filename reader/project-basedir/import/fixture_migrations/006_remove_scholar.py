#!/usr/bin/env python

import json

j = json.load(file("default-fixture.json"))

count = 0
for item in j:
    if item["model"] == "users.profile":
	del item["fields"]["scholar"]
	count += 1

print("Num rows updated: {}".format(count))
json.dump(j, file("default-fixture.json", 'w'))
print("Overwrote file")
