#!/usr/bin/env python

import json

j = json.load(file("default-fixture.json"))

#  Example json: [
#    {
#        "fields": {
#            "date_joined": "2014-04-29T15:02:11.528Z",
#            "digest_prefs": 2,
#            "flag": 0,
#            "info": "",
#            "last_login": "2016-02-27T21:58:35.134Z",
#            "location": "State College, USA",
#            "message_prefs": 3,
#            "my_tags": "",
#            "opt_in": false,
#            "scholar": "",
#            "tags": [],
#            "twitter_id": "",
#            "user": 2,
#            "uuid": "9428b06c8c04f25b5abf95d8354b2571",
#            "watched_tags": "",
#            "website": ""
#        },
#        "model": "users.profile",
#        "pk": 2
#    },
#  ]

count = 0
for item in j:
    if item["model"] == "users.profile":
	del item["fields"]["location"]
	del item["fields"]["twitter_id"]
	count += 1

print("Num rows updated: {}".format(count))
json.dump(j, file("default-fixture.json", 'w'))
print("Overwrote file")
