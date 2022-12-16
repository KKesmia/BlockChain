import requests
import os
import webbrowser
import asyncio

# from threading import Thread
# import os

# ports =["8080","8090",'8100']

# def runserver(port):
#     # path = os.path.join(os.getcwd(),"my_block_chain")
#     # print(path)
#     # os.chdir(path)
#     print("------------------")
#     os.system("python my_block_chain/manage.py runserver "+port)

# # for port in ports :
# #     threading.Thread(target=runserver(port)).start()
# for port in ports :
#     Thread(target=runserver,args=(port,)).start()
#     print("this will be printed immediately")




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