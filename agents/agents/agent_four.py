from agents.template_agent.template_agent import TemplateAgent

import random, time
from collections import Counter
from typing import cast

from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel
from geniusweb.actions.Accept import Accept
from geniusweb.actions.Offer import Offer
from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Settings import Settings
from geniusweb.issuevalue.Bid import Bid
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)

class AgentFour(TemplateAgent):
    """
    A simple party that places random bids and accepts when it receives an offer
    with sufficient utility.
    """

    def __init__(self):
        super().__init__()

        self.best_bid = (None, float('-inf'))
        self.last_bid = None
        self.utility_value = 0.9
        self.reservation_value = 0.6

    def notifyChange(self, info):
        super().notifyChange(info)

        if isinstance(info, Settings):
            # Create a list of all bids and sort them based on their utility function value.
            self.all_bids = [ (bid, self._profile.getProfile().getUtility(bid)) for bid in AllBidsList(self._profile.getProfile().getDomain()) ]
            self.all_bids = [ x for x in self.all_bids if x[1] > self.reservation_value ]
            self.all_bids.sort(key=lambda x:x[1], reverse=True)

            # Create the frequency opponent model.
            self.opponent_model = FrequencyOpponentModel.create().With(self._profile.getProfile().getDomain(), None)

        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            if isinstance(action, Offer):
                # Update the last bid and the opponent model.
                self.last_bid = cast(Offer, action).getBid()
                self.opponent_model = self.opponent_model.WithAction(action, self._progress)

                # Lower our reservation value over time, not allowing opponents to use it against us.
                self.reservation_value = 0.9 - (1 - self.progress())**2 * 0.3

    def getDescription(self) -> str:
        return "Agent 4"

    def _myTurn(self):
        # Determine what action we need to propose.
        action = Accept(self._me, self.last_bid) if self._isGood(self.last_bid) else Offer(self._me, self._findBid())
        self.getConnection().send(action)

    def _isGood(self, bid: Bid):
        return bid and self._profile.getProfile().getUtility(bid) > self.utility_value

    def _findBid(self):
        # If there is no previous bid, return our best bid.
        if self.last_bid is None:
            return self.all_bids.pop(0)[0]

        if self.progress() > 0.95:
            return self.best_bid[0]

        # Update our best received bid.
        if self.best_bid[1] < self._profile.getProfile().getUtility(self.last_bid):
            self.best_bid = (self.last_bid, self._profile.getProfile().getUtility(self.last_bid))

        # Generate all the bids with a high enough utility value.
        good_bids = [ b for b in self.all_bids if b[1] > self.utility_value ]

        # If no good enough bids exist, lower our utility value and return our best bid.
        if not good_bids:
            self.utility_value = max(self.utility_value - 0.02, self.reservation_value)
            return self.all_bids.pop(0)[0] if len(self.all_bids) > 1 else self.all_bids[0][0]

        # Calculate similarities to the proposed bids of the opponent based on the opponent model.
        similarities = [ self.opponent_model.getUtility(bid) for bid, u in good_bids ]
        index = similarities.index(max(similarities))

        # If none of the bids are similar enough, lower our utility value.
        if similarities[index] < 0.5 and self.progress() > 0.5:
            self.utility_value = max(self.utility_value - 0.005, self.reservation_value)

        # Remove the bid to be placed from the list and return it.
        return self.all_bids.pop(self.all_bids.index(good_bids[index]))[0]

    def progress(self):
        return self._progress.getCurrentRound() / self._progress.getTotalRounds()
