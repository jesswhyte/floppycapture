import os

os.system("curl https://onesearch.library.utoronto.ca/onesearch/"+args.call+
"////ajax? | jq .books.result.records[0].title")




