#!/usr/bin/env python

import gzip
import json

FIXTURE_FILE = "users-fixture-1.json.gz"

# To inspect, run:
#   gunzip -c badges-fixture-1.json.gz | less -S

with gzip.GzipFile(FIXTURE_FILE, 'r') as f: 
    lines = f.readlines()

j = json.loads("\n".join(lines))

#  Example json: [
#      {
#          "fields": {
#              "activity": 0,
#              "badges": 0,
#              "pubkey": "1@lvh.me",
#              "flair": "",
#              "is_active": true,
#              "is_admin": true,
#              "is_staff": true,
#              "last_login": "2016-02-27T22:26:52.910Z",
#              "name": "Biostar Community",
#              "new_messages": 0,
#              "password": "pbkdf2_sha256$12000$bEkiJEzVCY7n$59fsvwdMjY/Dy4bwdTwonL2Qq14saOq8Uboay5WwyzA=",
#              "score": 0,
#              "site": null,
#              "status": 1,
#              "type": 2
#          },
#          "model": "users.user",
#          "pk": 1
#      },

count = 0
for item in j:
	item["fields"]["is_fake_test_data"] = True
	count += 1
print("Num rows updated: {}".format(count))

with gzip.GzipFile(FIXTURE_FILE, 'w') as f: 
    f.write(
        json.dumps(j, indent=2)
    )
print("Overwrote file")
