#!/usr/bin/env python

import json

j = json.load(file("default-fixture.json"))

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
    if item["model"] == "users.user":
	del item["fields"]["pubkey"]
	del item["fields"]["name"]
	del item["fields"]["password"]
	count += 1

print("Num rows updated: {}".format(count))
json.dump(j, file("default-fixture.json", 'w'))
print("Overwrote file")
