# pade start-runtime --port 20000 blocchaine.py 

import hashlib
from pade.misc.utility import display_message, start_loop, call_later
from pade.acl.messages import ACLMessage
from pade.core.agent import Agent
from pade.acl.aid import AID
import random, time
import threading
import concurrent.futures

global global_stop
global_stop = False

 
class Transaction:
    def __init__(self, acteur_1=None, acteur_2=None, date=None, montant=None) :
        self.acteur_1 = acteur_1
        self.acteur_2 = acteur_2
        self.date = date
        self.montant = montant
    
    def __str__(self):
        return "Transaction: Date " + self.date + " Entre " + str(self.acteur_1.name[:17]) + " et " + str(self.acteur_2.name)[:17] + " montant: " + str (self.montant)

    # Function that instantiates a transaction from a str 
    def from_str(self, str):
        str = str.split(" ")
        self.acteur_1 = AID(str[4])
        self.acteur_2 = AID(str[6])
        self.date = str[2]
        self.montant = int(str[8])
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
    
    def sort(self):
        # Sort the transactions by acteur_1
        self.transactions = sorted(self.transactions, key=lambda transaction: transaction.acteur_1.name)
        return self.transactions
    

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

class Acteur(Agent):
    def __init__(self, aid):
        super(Acteur, self).__init__(aid=aid)
        self.aid = aid
        self.list_aid_acteurs = None
        self.block_provisoire = Block(0, [])
        # Adresse du premier block
        self.block_chaine = Block_chaine()
    
    def on_start(self):
        super(Acteur, self).on_start()
        call_later(10, self.broadcast_transaction)

    def broadcast_transaction(self):
        message = ACLMessage(ACLMessage.INFORM)
        for act in list_aid_acteurs:
            if self.aid.localname != act.name:
                message.add_receiver(act)
        # Generer une transaction   
        tr = Transaction(self.aid, random.choice(self.list_aid_acteurs), time.strftime("%d/%m/%Y"), random.randint(1, 100))
        message.set_content(str(tr))
        # Ajouter sa propre transaction au block provisoire car les agents ne réagissent pas à leurs propres messages
        self.block_provisoire.transactions.append(tr)
        self.send(message)
    
    def broadcast_hash_trouve(self, nonce , hash_operation):
        message = ACLMessage(ACLMessage.PROPOSE)
        for act in list_aid_acteurs:
            if self.aid.localname != act.name:
                message.add_receiver(act)
        message.set_content(str(nonce) +" "+ str(hash_operation))
        self.send(message)

    def react(self, message):
        super(Acteur, self).react(message)
        if message.sender.name in [i.name for i in self.list_aid_acteurs]:
            if message.performative == ACLMessage.INFORM:
                mes = str(message.content)
                tr = Transaction().from_str(mes)
                self.block_provisoire.transactions.append(tr)
                if len(self.block_provisoire.transactions) == len(self.list_aid_acteurs):
                    # display_message(self.aid.localname, str(self.block_provisoire))
                    # Order les transactions 
                    self.block_provisoire.sort()
                    # Calculer le hash du block dans un thread séparé
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(self.rechercher_hash, self.block_provisoire)
                        # display the results
                        nonce, hash_operation = future.result()
                        display_message(self.aid.localname, "Nonce: " + str(nonce) + " Hash: " + str(hash_operation))

                    # Broadcast le hash trouvé
                    if hash_operation is not None:
                        self.broadcast_hash_trouve(nonce, hash_operation)

            # Un acteur a trouvé le hash du block
            if message.performative == ACLMessage.PROPOSE:

                mes = str(message.content)
                nonce, hash_operation = mes.split(" ")
                self.verifier_block(float(nonce), hash_operation)

            # display_message(self.aid.localname, 'mes')
    

    def rechercher_hash(self, block):
        nonce = random.random()
        check_proof = False
        global global_stop
        hash_operation = None 

        while check_proof is False and  not global_stop:
            hash_operation = hashlib.sha256(
                str(str(nonce**2) + str(block)).encode()).hexdigest()
            if hash_operation[:5] == '00000':
                check_proof = True
                global_stop = True
                display_message(self.aid.localname, "J'ai trouve")
            else:
                nonce = random.random()
        if check_proof == False :
            hash_operation = None
        return nonce, hash_operation  

    def verifier_block(self, nonce, hash_operation):
        # Vérifier que le hash du block est valide
        if hashlib.sha256(str(str(nonce**2) + str(self.block_provisoire)).encode()).hexdigest() == hash_operation:
            display_message(self.aid.localname, "Le hash du block est valide")
            # Ajouter le block à la chaine
            self.ajouter_block(self.block_provisoire)
            # Afficher la chaine
            display_message(self.aid.localname, str(self.block_chaine))
            # Créer un nouveau block provisoire
            self.block_provisoire = Block(0, [])
        else:
            display_message(self.aid.localname, "Le hash du block n'est pas valide")
            # Rechercher un nouveau hash
            nonce, hash_operation = self.rechercher_hash(self.block_provisoire)
            # Diffuser le nouveau hash
            self.broadcast_hash_trouve(nonce, hash_operation)

    def ajouter_block(self, new_block):
        self.block_chaine.ajouter_block(new_block)

    def __str__(self):
        return "Acteur_" + str(self.id)

if __name__ == '__main__':
    compte_acteur = 4
    list_acteurs = list()
    list_aid_acteurs = list()

    # Instancier les acteurs 
    for i in range(compte_acteur):
        a = AID(name = 'agent_player_{}@localhost:{}'.format(1000+i, 1000+i))
        list_acteurs.append(Acteur(a))
        list_aid_acteurs.append(a)

    # Donner les adresses des acteurs aux acteurs
    for act in list_acteurs:
        act.list_aid_acteurs = list_aid_acteurs

    # Instancier le premier block
    premier_block = Block(0)
    # Chaque acteur se donne 100 à lui même 
    liste_transactions = []
    for act in list_acteurs :
        liste_transactions.append(Transaction(act.aid, act.aid, time.strftime("%d/%m/%Y"), 100))

    premier_block.transactions = liste_transactions

    # Donner le premier block aux acteurs
    for act in list_acteurs :
        act.block_chaine.liste_blocks.append(premier_block)

    # Lancer les acteurs
    start_loop(list_acteurs)



"""
if __name__ == "__main__":
    actor = acteur(1)
    bchaine = block_chaine(block(1, transactions=[transaction(actor, actor, "16/11/2022", 10000)]))
    actor.block_chaine = bchaine
    print(actor.rechercher_hash(bchaine.premier_block))"""
