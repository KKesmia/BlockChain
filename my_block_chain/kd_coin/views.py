# python manage.py runserver 8080 

from multiprocessing.resource_sharer import stop
import os
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests
import time
from random import random , randint, choice
import json
import sys
import threading
import hashlib
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
    
    def reset(self):
        self.id = 0
        self.transactions = [Transaction("_", sys.argv[-1], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 6)]

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
        self.solde = dict()
        pass

    def eval(self, block = None):
        if block == None:
            for tr in self.liste_blocks[0].transactions:
                self.solde.setdefault(tr.acteur_1, tr.montant) 
            print(self.solde.items())
        else:
            for tr in block.transactions:
                try:
                    sender = self.solde[tr.acteur_1]
                except:
                    self.solde.setdefault(tr.acteur_2, self.solde[tr.acteur_2] + tr.montant)
                    continue
                receiver = self.solde[tr.acteur_2]
                if sender - tr.montant <= 0:
                    return False
                else:
                    self.solde.setdefault(tr.acteur_1, sender - tr.montant)
                    self.solde.setdefault(tr.acteur_2, receiver + tr.montant)
        return True

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
clients_ = ['8080', '8090'] 
clients_.remove(sys.argv[-1])
liste_transactions = []
global block_courant 
block_courant = Block(0, [])
block_courant.reset()
global my_block_chaine
global my_stop
my_block_chaine = Block_chaine()
# Ajouter le premier block
premier_block = Block(0 , [])
for act in clients[:2]:
    liste_transactions.append(Transaction(act, act, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 100))
premier_block.transactions = liste_transactions
my_block_chaine.liste_blocks.append(premier_block)
my_block_chaine.eval(None)

def index(request):
    return JsonResponse({'foo':'bar'})

def generate_transaction():
    # Generate random transaction
    
    tr = {
        'acteur_1': sys.argv[-1],
        'acteur_2': choice(clients_),
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'montant': randint(1, 10)
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
    print("Je recois une transaction je suis " + str(sys.argv[-1]))
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
        if entry != sys.argv[-1]:
            try :
                response = requests.get("http://127.0.0.1:"+entry+"/kd_coin/receive_nonce", json={'nonce':nonce , 'hash':le_hash , 'block':block_courant.json()})
                print("----------- J'ai envoyé un nonce a " + entry + " -----------")
            except:
                pass

def receive_nonce(request):
    global block_courant
    global my_block_chaine
    global my_stop
    my_stop = True # arreter le thread de recherche de nonce
    print("Je recois un nonce " + str(sys.argv[-1]))
    
    # Get the data  from the GET request and cast it to a dict from json
    response = json.loads(request.body)
    dict_tr = json.loads(response["block"])
    liste_trs = []

    # Caster vers une liste de transactions
    for tr in dict_tr["transactions"]:
        liste_trs.append( Transaction(tr["acteur_1"] , tr["acteur_2"] , tr["date"] , tr["montant"]) )

    # Reconstruire le block
    block_a_tester = Block(0 , liste_trs)
    print(block_a_tester)

    # Si le nonce est valide
    if hashlib.sha256(str(str(response["nonce"]**2) + str(block_a_tester)).encode()).hexdigest() == response["hash"] and my_block_chaine.eval(block_a_tester):
        print("+++++++++++ Nonce valide")
        # Ajouter le block à la chaine
        my_block_chaine.ajouter_block(block_a_tester)

        print("Ma chaine est de taille "+str(len(my_block_chaine)))

        # Reset le block courant
        block_courant.reset()
    else :
        print("------------ Nonce invalide")
        # Reset le block courant
        block_courant.reset()

    thread_recherche_hash = threading.Thread(target=rechercher_hash)
    thread_recherche_hash.start()

    return HttpResponse(status=200)

def loop(request):

   #Lancer le thread qui envoie des transactions en permanence
    thread_envoie_transactions = threading.Thread(target=send_transactions)
    thread_envoie_transactions.start() 

    # Lancer le thread qui cherche le hash
    thread_recherche_hash = threading.Thread(target=rechercher_hash)
    thread_recherche_hash.start()

    return HttpResponse(status=200)

def send_transactions():
    while True:
        time.sleep(randint(1, 4))
        
        print("J'envoie une transaction, je suis  " + str(sys.argv[-1]))
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
        time.sleep(randint(1, 4))

def rechercher_hash():
    nonce = random()
    le_hash = "1111111111"
    global block_courant
    global my_block_chaine
    global my_stop
    count = 0
    my_stop = False
    while not my_stop:
        nonce = random()
        if len(block_courant.transactions) > 1:
            le_hash = hashlib.sha256(str(str(nonce**2) + str(block_courant)).encode()).hexdigest()
                
        count += 1
        if le_hash[:5] == '00000':
            my_stop = True
            print("J'ai trouve le bon nonce " + str(sys.argv[-1]) +" apres "+str(count)+" iterations")
            print(block_courant)
            broadcast_block(nonce , le_hash, block_courant)
            
            # Ajouter le block courant à la chaine
            if my_block_chaine.eval(block_courant):
                my_block_chaine.ajouter_block(block_courant)
                print("Ma chaine est de taille "+str(len(my_block_chaine)))
            else:
                print("Block non valide")
            # Reset le block courant
            block_courant.reset()
            # Reset les variables
            count = 0
            

