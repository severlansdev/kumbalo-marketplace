import os
import sys

def handler(request):
    return {
        "statusCode": 200,
        "body": str({
            "cwd": os.getcwd(),
            "root_listdir": os.listdir("."),
            "sys_path": sys.path,
            "api_listdir": os.listdir("api") if os.path.exists("api") else "api not found"
        })
    }
