# agent_example_1.py
# A simple hello agent in PADE!
from pade.misc.utility import display_message, start_loop, call_later
from pade.acl.messages import ACLMessage
from pade.core.agent import Agent
from pade.acl.aid import AID
import random, time



class AgentePlayer(Agent):
    def __init__(self, aid, aid_juge, players):
        super(AgentePlayer, self).__init__(aid=aid)
        display_message(self.aid.localname, '===== Joined!')
        self.aid_juge = aid_juge
        self.players = players
        self.aid = aid

    def on_start(self):
        super(AgentePlayer, self).on_start()

    def sending_message(self):
        message = ACLMessage(ACLMessage.INFORM)
        message.add_receiver( self.aid_juge )
        value = random.randint(1,3)
        display_message(self.aid.localname, 'Sending value {}...'.format(self.aid_juge))
        message.set_content(str(value))
        self.send(message)

    def react(self, message):
        super(AgentePlayer, self).react(message)
        if message.sender.name == self.aid_juge.name:
            mes = str(message.content)
            if mes.startswith("Round"):
                #current_sum = int( mes.split("/")[1] )
                self.sending_message()



class AgentJuge(Agent):
    def __init__(self, aid, players = 4):
        super(AgentJuge, self).__init__(aid=aid)
        self.aid = aid
        self.players = players
        display_message(self.aid.localname, '===== Welcome to Black Jack =====')
        self.agents_aids = list()
        self.agents = self.Black_jack_game()
        self.agents = [self]+ self.agents
        self.current_sum = 0
        self.round = 1
        self.per_round = 0
        self.game_end = False

    def on_start(self):
        super(AgentJuge, self).on_start()
        display_message(self.aid.localname, '=====  Let thee game Begin  =====')
        call_later(10.0, self.kick_off)

    def kick_off(self):
        if(self.current_sum < 21):
            display_message(self.aid.localname, '=====        Round {}        ====='.format(self.round))
            self.round += 1
            self.sending_message()
        else:
            while(True):
                pass
        
    def sending_message(self):
        message = ACLMessage(ACLMessage.INFORM)
        for i in self.agents_aids:
            message.add_receiver(i)
        message.set_content('Round/'+ str(self.current_sum))
        self.send(message)


    def react(self, message):

        super(AgentJuge, self).react(message)
        if message.sender.name in [i.name for i in self.agents_aids]:
            mes = str(message.content)
            self.per_round += 1
            self.current_sum += int(mes)
            display_message(self.aid.localname, '{} sent value {}; current sum {}'.format(message.sender.name, mes, self.current_sum))
            if (self.current_sum >= 21 and not self.game_end ):
                display_message(self.aid.localname, '=====  Winner {} ====='.format(message.sender.name))
                display_message(self.aid.localname, '=====  The Game ends here!  =====')
                self.game_end = True
            if self.per_round == len(self.agents_aids):
                self.per_round = 0
                time.sleep(5)
                self.kick_off()


    def Black_jack_game(self):
        agents = list()
        c = 0
        for i in range(self.players):
            port = 2000 + c
            agent_name = 'agent_player_{}@localhost:{}'.format(port, port)
            agente = AgentePlayer(AID(name = agent_name), self.aid , self.players)
            agents.append(agente)
            self.agents_aids.append(agente.aid)
            c += 1
        return agents


if __name__ == '__main__':
    Game_name = 'agent_juge@localhost:{}'.format(1000)
    Agent_juge = AgentJuge(AID(name = Game_name), 2)
    start_loop(Agent_juge.agents)

