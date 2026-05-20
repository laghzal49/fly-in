import re

txt = "The rain in Spain stays mainly in the plain"
x = re.search("^The.*Spain$", txt)
print(x.group())