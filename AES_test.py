import re

url = "https://results.advancedeventsystems.com/event/PTAwMDAwMzczMzE90"
match = re.search(r'/event/([^/]+)$', url)
event_id = match.group(1) if match else None
print(event_id)