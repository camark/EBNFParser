
import re
token = re.compile('|'.join(['\}','\|','\{','\]','\\n','\[','\:\=','\:\:\=','\+','\*','\)','\(','"[\w|\W]*?"','[a-zA-Z_][a-zA-Z0-9]*','\d+'])).findall
