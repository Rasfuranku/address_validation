import usaddress
try:
    print(usaddress.parse("07055 130 jackson st"))
except Exception as e:
    print(e)
