from otree.api import Currency as c, currency_range
from . import pages
from ._builtin import Bot
from otree.api import Submission
from .models import Constants
import random


class PlayerBot(Bot):
    def play_round(self):
        if self.round_number <= self.session.config["num_rounds"]:
            yield Submission(pages.dPGG_Decision,
                             dict(contribution=random.randint(int(self.player.endowment/2),
                                                              int(self.player.endowment/3*3))
                                  ),
                             check_html=False)
            if self.round_number == Constants.belief_elicitation_round:
                yield pages.dPGG_Belief, dict(belief=random.randint(int(self.player.endowment/2),
                                                                    self.player.endowment)
                                              )
            if self.round_number == self.session.config["num_rounds"]:
                yield pages.dPGG_Results