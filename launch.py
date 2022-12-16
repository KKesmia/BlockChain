import requests
import os
import webbrowser
import asyncio

# # RUNSERVER
# async def runserver():
#     path = os.path.join(os.getcwd(),"my_block_chain")
#     print(path)
#     os.chdir(path)
#     os.system("python manage.py runserver 8080")
# # OPEN BROWSER
# def openproject():
#     webbrowser.open_new_tab("http://127.0.0.1:8080/index")
# # EXECUTE PROGRAM
# async def main():
#     task1 = asyncio.create_task(runserver())
#     openproject()
#     await task1

# asyncio.run(main())

# Send a request to start the loop
response = requests.get("http://127.0.0.1:8080/kd_coin/loop")
response = requests.get("http://127.0.0.1:8090/kd_coin/loop")