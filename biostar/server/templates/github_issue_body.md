{% load server_tags %}{{ main_body }}
---
This issue is synchronized with the following Q&A post:
{{ post_url }}

Original author of the post is:
{% gravatar author 82 %}
{{ author.name }}
