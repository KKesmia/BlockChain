# pade start-runtime blocchaine.py 
import hashlib
from pade.misc.utility import display_message, start_loop, call_later
from pade.acl.messages import ACLMessage
from pade.core.agent import Agent
from pade.acl.aid import AID
import random, time
import threading
import concurrent.futures


class Transaction:
    def __init__(self, acteur_1=None, acteur_2=None, date=None, montant=None) :
        self.acteur_1 = acteur_1
        self.acteur_2 = acteur_2
        self.date = date
        self.montant = montant
    
    def __str__(self):
        return "Transaction: Date " + self.date + " Entre " + str(self.acteur_1.name) + " et " + str(self.acteur_2.name) + " montant: " + str (self.montant)

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

    def update_block(self, block):
        transactions_a_jour = list()
        self.sort()
        block.sort()
        for i_tr, j_tr in zip(self.transactions, block.transactions):
            if str(i_tr) != str(j_tr):
                transactions_a_jour
            pass
        pass

    def from_str(self, input):
        self.transactions = list()
        string_transactions = input.split("\n")
        for str_tr in string_transactions:
            try:
                tr = Transaction()
                self.transactions.append(tr.from_str(str_tr))
            except:
                pass
        pass

    def sort(self):
        # Sort the transactions
        self.transactions = sorted(self.transactions, key=lambda transaction: str(transaction))
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
    """
        azez
    """
    global_stop = False

    def __init__(self, aid):
        super(Acteur, self).__init__(aid=aid)
        self.aid = aid
        self.list_aid_acteurs = None
        self.block_provisoire = Block(0, [])
        # Adresse du premier block
        self.block_chaine = Block_chaine()
        self.thread_echange = None
        self.status = "idle"
    
    def echanger(self):
        self.status = "trading"
        while True:
            if self.status == "trading":
                message = ACLMessage(ACLMessage.INFORM)
                for act in self.list_aid_acteurs:
                    if self.aid.localname != act.name:
                        message.add_receiver(act)
                # Generer une transaction   
                tr = Transaction(self.aid, random.choice(self.list_aid_acteurs), time.strftime("%d/%m/%Y"), random.randint(1, 100))
                message.set_content(str(tr))
                # Ajouter sa propre transaction au block provisoire car les agents ne réagissent pas à leurs propres messages

                self.block_provisoire.transactions.append(tr)
                self.send(message)
                time.sleep(random.randint(5, 10))
            else:
                break

    def on_start(self):
        super(Acteur, self).on_start()
        display_message(self.aid.localname, "hey wtf!")
        call_later(0, self.broadcast_transaction_)

    def broadcast_transaction_(self):
        Acteur.global_stop = False
        self.thread_echange = threading.Thread(target=self.echanger)
        self.thread_echange.start()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.rechercher_hash, self.block_provisoire)
            # display the results
            nonce, hash_operation = future.result()
        
        # Broadcast le hash trouvé
        if hash_operation is not None:
            self.broadcast_hash_trouve(nonce, hash_operation)
            # implementation de verification de block
            self.verifier_block(float(nonce), hash_operation, finder=True)
    
    def broadcast_hash_trouve(self, nonce , hash_operation):
        message = ACLMessage(ACLMessage.PROPOSE)
        for act in self.list_aid_acteurs:
            if self.aid.localname != act.name:
                message.add_receiver(act)
        message.set_content(str(nonce) +"#"+ str(hash_operation)+ "#"+ str(self.block_provisoire))
        self.send(message)

    def react(self, message):
        super(Acteur, self).react(message)
        if message.sender.name in [i.name for i in self.list_aid_acteurs]:
            if message.performative == ACLMessage.INFORM:
                mes = str(message.content)
                if mes != "":
                    tr = Transaction().from_str(mes)
                    self.block_provisoire.transactions.append(tr)
                        
            # Un acteur a trouvé le hash du block
            if message.performative == ACLMessage.PROPOSE:
                self.status = "checking"
                mes = str(message.content)
                nonce, hash_operation, str_transactions = mes.split("#")
                self.verifier_block(float(nonce), hash_operation, str_transactions)
    

    def rechercher_hash(self, block):
        nonce = random.random()
        check_proof = False
        while check_proof is False and  not Acteur.global_stop:
            self.block_provisoire.sort()
            hash_operation = hashlib.sha256(
                str(str(nonce**2) + str(block)).encode()).hexdigest()
            if hash_operation[:5] == '00000':
                check_proof = True
                Acteur.global_stop = True
                display_message(self.aid.localname, "J'ai trouve un hash.")
            else:
                nonce = random.random()
        if check_proof == False :
            hash_operation = None
        return nonce, hash_operation  

    def verifier_block(self, nonce, hash_operation, str_transactions=None, finder=False):

        if finder == True:
            # Dans le cas ou celui qui a trouvé le bon hash verifie la liste des transactions qui n est pas encore implementé
            # donc on suppose que c est tous le temps correct
            self.ajouter_block(self.block_provisoire )
            self.block_provisoire = Block(0, [])
            self.broadcast_transaction_()
            return 

        # Vérifier que le hash du block est valide
        proposed_block = Block(id=0)
        proposed_block.from_str(str_transactions)
        
        if hashlib.sha256(str(str(nonce**2) + str(proposed_block)).encode()).hexdigest() == hash_operation:
            display_message(self.aid.localname, "Le hash du block est valide")
            # Ajouter le block à la chaine
            self.ajouter_block(proposed_block)
            # re-initialiser le block provisoire
            self.block_provisoire.update_block(proposed_block)
            self.broadcast_transaction_()
        else:
            display_message(self.aid.localname, "Le hash du block n'est pas valide, reprennons la recherche")
            self.broadcast_transaction_()

    def ajouter_block(self, new_block):
        self.block_chaine.ajouter_block(new_block)

    def __str__(self):
        return "Acteur_" + str(self.id)


class Superviseur(Agent):
    def __init__(self, aid, players=4):
        super(Superviseur, self).__init__(aid=aid)
        self.aid = aid
        self.players = players
        self.acteurs = self.kick_off()
        self.agents = [self] + self.acteurs
        self.list_aid_acteurs = [x.aid for x in self.acteurs]
        

    def kick_off(self):
        list_aid_acteurs = list()
        list_acteurs = list()

        # Instancier les acteurs 
        for i in range(self.players):
            a = AID(name = 'agent_player_{}@localhost:{}'.format(1001+i, 1001+i))
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
            liste_transactions.append(Transaction(self.aid, act.aid, time.strftime("%d/%m/%Y"), 100))
        premier_block.transactions = liste_transactions
        # Donner le premier block aux acteurs
        for act in list_acteurs :
            act.block_chaine.liste_blocks.append(premier_block)
        
        return list_acteurs

    def on_start(self):
        super(Superviseur, self).on_start()
        call_later(10, self.broadcast_check())

    def broadcast_check(self):
        while True:
            message = ACLMessage(ACLMessage.INFORM)
            for act in self.list_aid_acteurs:
                message.add_receiver(act)
            message.set_content("check")
            self.send(message)
            time.sleep(5)

    def react(self, message):
        super(Superviseur, self).react(message)
        if message.sender.name in [i.name for i in self.list_aid_acteurs]:
            pass


if __name__ == '__main__':
    Game_name = 'agent_superviseur@localhost:{}'.format(1000)
    Agent_superviseur = Superviseur(AID(name = Game_name), 3)
    start_loop(Agent_superviseur.agents)




