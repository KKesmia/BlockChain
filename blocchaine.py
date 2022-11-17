import hashlib
from pade.misc.utility import display_message, start_loop, call_later
from pade.acl.messages import ACLMessage
from pade.core.agent import Agent
from pade.acl.aid import AID
import random, time


a2 = AID(name = 'agent_player_{}@localhost:{}'.format(1002, 1002))
a3 = AID(name = 'agent_player_{}@localhost:{}'.format(1003, 1003))
a4 = AID(name = 'agent_player_{}@localhost:{}'.format(1000+4, 1000+4))


class transaction:
    def __init__(self, acteur_1, acteur_2, date, montant):
        self.acteur_1 = acteur_1
        self.acteur_2 = acteur_2
        self.date = date
        self.montant = montant
    
    def __str__(self):
        return "Transaction: Date " + self.date + " between " + str(self.acteur_1) + " et " + str(self.acteur_2) + " montant: " + str (self.montant);


class block:
    def __init__(self, id, transactions = None):
        self.id = id
        self.transactions = transactions
        self.block_suivant = None
        self.block_precedent = None
     
    def __str__(self):
        ret = ""
        for i in self.transactions:
            ret = ret + "\n" + str(i)

        return ret
        

class block_chaine:
    def __init__(self, premier_block):
        self.premier_block = premier_block
        pass

    def add_block(self):
        pass

class acteur(Agent):
    def __init__(self, aid):
        super(acteur, self).__init__(aid=aid)
        self.aid = aid
        self.list_aid_acteurs = None
        # Adresse du premier block
        self.block_chaine = None
    
    def on_start(self):
        super(acteur, self).on_start()
        call_later(15, self.sending_message)

    def sending_message(self):
        message = ACLMessage(ACLMessage.INFORM)
        for act in list_aid_acteurs:
            if self.aid.localname != act.name:
                message.add_receiver(act)
        message.set_content('Round/')
        self.send(message)

    def react(self, message):
        super(acteur, self).react(message)
        if message.sender.name in [i.name for i in self.list_aid_acteurs]:
            mes = str(message.content)
            display_message(self.aid.localname, mes)
    

    def rechercher_hash(self, block):
        new_proof = random.random()
        check_proof = False
         
        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(str(new_proof**2) + str(block)).encode()).hexdigest()
            if hash_operation[:5] == '00000':
                check_proof = True
            else:
                new_proof = random.random()
                 
        return new_proof, hash_operation  

    def verifier_block(self, new_block):
        next = self.premier_block
        while (next.block_suivant != None):
            next = next.block_suivant

        next.block_suivant = new_block

    def envoyer_transaction(self):    
        pass

    def recevoir_transaction(self):
        pass

    def __str__(self):
        return "Acteur_" + str(self.id)

if __name__ == '__main__':
    compte_acteur = 4
    list_acteurs = list()
    list_aid_acteurs = list()

    for i in range(compte_acteur):
        a = AID(name = 'agent_player_{}@localhost:{}'.format(1000+i, 1000+i))
        list_acteurs.append(acteur(a))
        list_aid_acteurs.append(a)

    for act in list_acteurs:
        act.list_aid_acteurs = list_aid_acteurs

    start_loop(list_acteurs)



"""
if __name__ == "__main__":
    actor = acteur(1)
    bchaine = block_chaine(block(1, transactions=[transaction(actor, actor, "16/11/2022", 10000)]))
    actor.block_chaine = bchaine
    print(actor.rechercher_hash(bchaine.premier_block))"""