# python manage.py runserver 8080 

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests
import time
from random import random , randint
import json
from schedule import Scheduler
import sys
import threading
import hashlib
import asyncio
from datetime import datetime

class Transaction:
    def __init__(self, acteur_1=None, acteur_2=None, date=None, montant=None) :
        self.acteur_1 = acteur_1
        self.acteur_2 = acteur_2
        self.date = date
        self.montant = montant
    
    def __str__(self):
        return "Transaction: Date " + str(self.date) + " Entre " + str(self.acteur_1) + " et " + str(self.acteur_2) + " montant: " + str (self.montant)

    # Function that instantiates a transaction from a str 
    def from_str(self, str):
        str = str.split(" ")
        self.acteur_1 = str[4]
        self.acteur_2 = str[6]
        self.date = str[2]
        self.montant = int(str[8])
        return self
    def from_dict(self, dict):
        self.acteur_1 = dict['acteur_1']
        self.acteur_2 = dict['acteur_2']
        self.date = dict['date']
        self.montant = dict['montant']
        return self

class Block:
    def __init__(self, id, transactions = None):
        self.id = id
        self.transactions = transactions
        self.block_suivant = None
        self.block_precedent = None
     
    def __str__(self):
        ret = ""
        for i in self.sort():
            ret = ret + "\n" + str(i)
        return ret
    
    def __len__(self) :
        return(len(self.transactions))

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def sort(self):
        # Sort the transactions by acteur_1
        self.transactions = sorted(self.transactions, key=lambda transaction: transaction.acteur_1)
        return self.transactions

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
class Block_chaine:
    def __init__(self):
        self.liste_blocks = [] 
        pass

    def ajouter_block(self, block):
        block.id = self.liste_blocks[-1].id + 1
        self.liste_blocks.append(block)

    def __str__(self):
        ret = ""
        for i in self.liste_blocks:
            ret = ret + "\n" + str(i)
        return ret
    def __len__(self) :
        return(len(self.liste_blocks))

# Init the variables

clients = ['8080', '8090', '8100']
liste_transactions = []
global block_courant 
block_courant = Block(0 , [])
global my_block_chaine
my_block_chaine = Block_chaine()
# Ajouter le premier block
premier_block = Block(0 , [])
for act in clients :
        liste_transactions.append(Transaction(act, act, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 100))
my_block_chaine.liste_blocks.append(premier_block)


def index(request):
    return JsonResponse({'foo':'bar'})

def generate_transaction():
    # Generate random transaction
    tr = {
        'acteur_1': 'acteur_1',
        'acteur_2': 'acteur_2',
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'montant': randint(1,10)
    }
    return tr

def test(request):
    response = generate_transaction()
    # Print the result
    print("#########################")
    print(response)
    print("#########################")
    return JsonResponse({'transaction':response})

def receive_transaction(request):
    print("Je recois une transaction" + str(sys.argv[-1]))
    # # Get the port i am using
    # print(sys.argv[-1])
    # Get the data  from the GET request and cast it to a dict from json
    response = json.loads(request.body)
    # Ajouter la transaction au block courant
    block_courant.add_transaction(Transaction().from_dict(response))
    # Print le block courant
    # print("#########################")
    # print(str(block_courant))
    # print("#########################")

    return HttpResponse(status=200)

def broadcast_block(nonce , le_hash, block):
    for entry in clients:
        # Je ne broadcast pas le nonce et le block à moi même
        if True :#entry != sys.argv[-1]:
            try :
                response = requests.get("http://127.0.0.1:"+entry+"/kd_coin/receive_nonce", json={'nonce':nonce , 'hash':le_hash , 'block':block})
                print("----------- J'ai envoyé un nonce a " + entry + " -----------")
            except:
                pass

def receive_nonce(request):
    global block_courant
    global my_block_chaine
    # Reset le block courant pour arreter la recherche du hash
    block_attente = block_courant
    block_courant = Block(0 , [])
    print("Je recois un nonce " + str(sys.argv[-1]))
    
    # Get the data  from the GET request and cast it to a dict from json
    response = json.loads(request.body)
    dict_tr = json.loads(response["block"])
    liste_trs = []

    # Caster vers une liste de transactions
    for tr in dict_tr["transactions"]:
        tt1 = Transaction(tr["acteur_1"] , tr["acteur_2"] , tr["date"] , tr["montant"])
        liste_trs.append(tt1)
    # Reconstruire le block
    block_a_tester = Block(0 , liste_trs)
    print(block_a_tester)

    # Si le nonce est valide
    if hashlib.sha256(str(str(response["nonce"]**2) + str(block_a_tester)).encode()).hexdigest() == response["hash"]:
        print("+++++++++++ Nonce valide")
        # Ajouter le block à la chaine
        my_block_chaine.ajouter_block(block_a_tester)

        print("Ma chaine est de taille "+str(len(my_block_chaine)))

        # Reset le block courant
        block_courant = Block(0 , [])
    else :
        print("------------ Nonce invalide")
        # Reset le block courant
        block_courant = block_attente
    return HttpResponse(status=200)

def loop(request):
    # while True:
    #     print("J'envoie une transaction")
    #     # Generate random transaction
    #     tr = generate_transaction()
    #     # Send the transaction to all the nodes in local network
    #     for entry in clients:
    #         try :
    #             response = requests.get("http://127.0.0.1:"+entry+"/kd_coin/receive_transaction", json=tr)
    #             # print(response)
    #         except:
    #             pass
    #     # sleep for a random time
    #     time.sleep(randint(5,7))
   #Lancer le thread qui envoie des transactions en permanence
    thread_envoie_transactions = threading.Thread(target=send_transactions)
    thread_envoie_transactions.start() 

    # Lancer le thread qui cherche le hash
    thread_recherche_hash = threading.Thread(target=rechercher_hash)
    thread_recherche_hash.start()

    return HttpResponse(status=200)

def send_transactions():
    while True:
        print("J'envoie une transaction" + str(sys.argv[-1]))
        # Generate random transaction
        tr = generate_transaction()
        # Send the transaction to all the nodes in local network
        for entry in clients:
            try :
                response = requests.get("http://127.0.0.1:"+entry+"/kd_coin/receive_transaction", json=tr)
                # print(response)
            except:
                pass
        # sleep for a random time
        time.sleep(randint(5,10))

def rechercher_hash():
        nonce = random()
        le_hash = "1111111111"
        global block_courant
        global my_block_chaine
        count = 0

        # while  not global_stop:
        #     if len(block_courant) >=5 :
        #         # print("Je cherche un hash pour le block courant "+str(len(block_courant)))
        #         le_hash = hashlib.sha256(
        #             str(str(nonce**2) + str(block_courant)).encode()).hexdigest()
        #         if le_hash[:5] == '00000':
        #             global_stop = True
        #             print("J'ai trouve le bon nonce " + str(sys.argv[-1]) )
        #             broadcast_block(nonce , le_hash, block_courant)
        #             # Reset le block courant
        #             block_courant = Block(0 , [])
        #             # Ajouter le block courant à la chaine

        #             # Reset global_stop
        #             global_stop = False
        #         else:
        #             nonce = random()
        while True :
            if len(block_courant) >=5 :
                while le_hash[:6] != '000000' :
                    nonce = random()
                    le_hash = hashlib.sha256(
                            str(str(nonce**2) + str(block_courant)).encode()).hexdigest()
                    count += 1
                print("J'ai trouve le bon nonce " + str(sys.argv[-1]) +" apres "+str(count)+" iterations")
                # broadcast_block(nonce , le_hash, block_courant)
                if str(sys.argv[-1]) == "8080" :
                    requests.get("http://127.0.0.1:8090/kd_coin/receive_nonce", json={'nonce':nonce , 'hash':le_hash , 'block':block_courant.json()})
                    print("------ envoyé    au 8090 ------")
                else :
                    requests.get("http://127.0.0.1:8080/kd_coin/receive_nonce", json={'nonce':nonce , 'hash':le_hash , 'block':block_courant.json()})
                    print("------ envoyé    au 8080 ------")
                # Ajouter le block courant à la chaine
                my_block_chaine.ajouter_block(block_courant)
                print("Ma chaine est de taille "+str(len(my_block_chaine)))
                # Reset le block courant
                block_courant = Block(0 , [])
                # Reset les variables
                le_hash = "1111111111"
                count = 0

        return nonce, le_hash 

# if __name__ != "__main__":
#     print("hello")
