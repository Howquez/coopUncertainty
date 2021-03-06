from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)

import math
import random
import time

author = "Hauke Roggenkamp"

doc = """
Dynamic Public Goods Game where the current round's earnings determine the next round's endowment
"""


class Constants(BaseConstants):
    name_in_url = "dPGG"
    players_per_group = 3
    num_others_per_group = players_per_group - 1
    num_rounds = 15
    initial_endowment = 20
    efficiency_factor = 1.25 # (MPCR) Marginal Per Capita Return per round
    rate_of_return = (efficiency_factor - 1)*100

    safe_rounds = 2 # number of rounds without any risk
    threshold = 0.5 # fraction of a group's endowment that has to be contributed such that no disaster can occur
    belief_elicitation_round = 1
    elicitation_bonus = 10 # points
    timeout = 3 # minutes
    patience = 6 # minutes
    patience_bonus = 10 # points



class Subsession(BaseSubsession):
    def creating_session(self):
        if self.round_number == 1:
            for p in self.get_players():
                p.participant.vars["belief_elicitation_round"] = Constants.belief_elicitation_round
                p.participant.vars["endowments"] = []
                p.participant.vars["stock"] = []
                p.participant.vars["euros"] = []
                p.participant.vars["is_dropout"] = False
                p.participant.vars["is_residual_player"] = False
                if not "wait_page_arrival" in p.participant.vars:
                    p.participant.vars["wait_page_arrival"] = time.time()

    def group_by_arrival_time_method(self, waiting_players):
        if len(waiting_players) >= Constants.players_per_group:
            return waiting_players[:Constants.players_per_group]
        for player in waiting_players:
            player.wait_time_left = int(math.ceil(Constants.patience - (time.time() - player.participant.vars['wait_page_arrival']) / 60))
            if player.waiting_too_long():
                player.participant.vars["is_residual_player"] = True
                # make a single-player group.
                return [player]



class Group(BaseGroup):

    EWE = models.BooleanField(initial=False, doc="if true, extreme weather event occurred")
    disaster = models.BooleanField(initial=False, doc="if true, the EWE has negative effects on stock ")
    total_contribution = models.IntegerField(doc="sum of contributions in this round")
    average_contribution = models.FloatField(doc="average contribution in this round")
    individual_share = models.IntegerField(doc="individual share each player receives from this round's contributions")
    bot_active = models.BooleanField(doc="denotes whether player in group dropped out such that a bot takes over", initial = False)
    wealth = models.IntegerField(doc="sum of endowments at the beginning of a round")


    def set_group_variables(self):
        if len(self.get_players()) == Constants.players_per_group:
            self.total_contribution = sum([p.contribution for p in self.get_players()])
            self.average_contribution = round(self.total_contribution / Constants.players_per_group, 2)
            self.individual_share = int(math.ceil(self.total_contribution * Constants.efficiency_factor / Constants.players_per_group))
            self.wealth = sum([p.endowment for p in self.get_players()])
            # alternatively, define wealth as the last round's stock
            # self.wealth = sum([p.stock for p in self.in_round(self.round_number - 1).get_players()])

    def set_disaster(self):
        # random risk lottery
        if self.round_number > Constants.safe_rounds:
            if self.session.config["risk"] > random.uniform(0, 1):
                self.EWE = True
                if self.total_contribution < Constants.threshold * self.wealth:
                    self.disaster = True

    def set_payoffs(self):

        # call  methods
        self.set_group_variables()
        self.set_disaster()

        # calculate player-level-variables
        for p in self.get_players():
            # players who were stuck on the initial wait page due to group member's drop outs have 0-earnings as well as
            # little bonus implemented as a payoff in the last round
            if p.participant.vars["is_residual_player"]:
                p.stock = 0
                p.gain = 0
                p.payoff = 0
                # give them a patience bonus
                if self.round_number == self.session.config["num_rounds"]:
                    p.payoff = c(Constants.patience_bonus)
            # all the others essentially earn their gains (which can be negative)
            else:
                p.gross_gain = self.individual_share - p.contribution

                p.stock = p.endowment + p.gross_gain

                # implement basic disaster damage
                if self.disaster:
                    p.stock = int(math.ceil(p.stock * 0.5))

                p.gain = p.stock - p.endowment

                # p.participant.vars["stock"].append(round(p.stock*self.session.config["real_world_currency_per_point"], 1))
                p.participant.vars["stock"].append(p.stock)
                p.participant.vars["euros"].append(c(p.stock).to_real_world_currency(self.session))


                # payoff
                if p.round_number == 1:
                    p.payoff = c(p.stock)
                else:
                    p.payoff = c(p.gain)

                # Make sure participants do not earn anything if they drop out in four steps:
                #1: if they are marked as a dropout, they shouldn't earn anything
                if p.is_dropout:
                    if self.round_number < self.session.config["num_rounds"]:
                        p.payoff = c(0)
                #2: in their last round, also substract the participationn fee
                    else:
                        p.payoff = c(- self.session.config["participation_fee"]/self.session.config["real_world_currency_per_point"])
                #3: substract all the money they earned prior to dropping out
                if self.round_number > 1:
                    if not p.is_dropout == p.in_round(self.round_number - 1).is_dropout:
                        p.payoff = -p.endowment

            # add payoff if belief was correct
            if self.round_number == Constants.belief_elicitation_round:
                others_average_contribution = (self.total_contribution - p.contribution) / Constants.num_others_per_group
                # vars for Outro
                p.participant.vars["correct_guess"] = False
                p.participant.vars["others_average_contribution"] = others_average_contribution
                p.participant.vars["belief"] = p.belief
                p.participant.vars["belief_bonus"] = c(Constants.elicitation_bonus).to_real_world_currency(self.session)
                # actual payoff operation
                if p.belief > others_average_contribution * 0.9 and p.belief < others_average_contribution * 1.1:
                    p.payoff = c(p.payoff + Constants.elicitation_bonus)
                    p.participant.vars["correct_guess"] = True


class Player(BasePlayer):

    review_instructions = models.IntegerField(doc="Counts the number of times a player reviews instructions.",
                                              initial=0,
                                              blank=True)

    wait_time_left = models.IntegerField(doc="denotes the time a player has to wait for others to arrive on WaitPage")
    endowment = models.IntegerField(doc="the player's endowment in this round (equals her stock of last round)")
    contribution = models.IntegerField(min=0, doc="the player's contribution in this round")
    belief = models.IntegerField(min=0, doc="the player's belief about the other player's average contribution")
    gross_gain = models.IntegerField(doc="each round's gross earnings as the difference of the individual_share and the player's contribution")
    gain = models.IntegerField(doc="each round's net earnings as the difference between stock and endowment (incorporating possible damage)")
    stock = models.IntegerField(doc="accumulated earnings of played rounds")
    is_dropout = models.BooleanField(doc="denotes whether player dropped out", initial = False)

    def start(self):
        if self.round_number == 1:
            self.endowment = Constants.initial_endowment
        else:
            self.endowment = int(self.in_round(self.round_number - 1).stock)
        self.participant.vars["endowments"].append(self.endowment)


    def contribution_max(self):
        if self.round_number == 1:
            return Constants.initial_endowment
        else:
            return self.in_round(self.round_number - 1).stock

    def waiting_too_long(self):
        return time.time() - self.participant.vars['wait_page_arrival'] > Constants.patience * 60
