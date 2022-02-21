from agents.template_agent.template_agent import TemplateAgent

import random, time
from collections import Counter

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

        self.best_bid = (None, 0.0)
        self.last_bid = None
        self.utility_value = 0.9
        self.reservation_value = 0.6

    def notifyChange(self, info):
        super().notifyChange(info)

        if isinstance(info, Settings):
            # Create a counter for all the values per issue of the opponent.
            self.counter = dict((k,Counter()) for k in self._profile.getProfile().getUtilities().keys())

            # Create a list of all bids and sort them based on their utility function value.
            self.all_bids = [ (bid, self._profile.getProfile().getUtility(bid)) for bid in AllBidsList(self._profile.getProfile().getDomain()) ]
            self.all_bids = [ x for x in self.all_bids if x[1] > self.reservation_value ]
            self.all_bids.sort(key=lambda x:x[1], reverse=True)

        elif isinstance(info, ActionDone):
            self.last_bid = self._last_received_bid
            self.curr_round = self._progress.getCurrentRound()

    def getDescription(self) -> str:
        return "Agent 4"

    def _myTurn(self):
        action = Accept(self._me, self.last_bid) if self._isGood(self.last_bid) else Offer(self._me, self._findBid())
        self.getConnection().send(action)

    def _isGood(self, bid: Bid):
        if bid is None:
            return False

        for issue in bid.getIssues():
            self.counter[issue][bid.getValue(issue)] += 1

        return self._profile.getProfile().getUtility(bid) > self.utility_value


    def _findBid(self):
        if self.last_bid is None:
            return self.all_bids.pop(0)[0]

        # Generate all the good bids.
        good_bids = [ b for b in self.all_bids if b[1] > self.utility_value ]
        if not good_bids:
            self.utility_value = max(self.utility_value - 0.01, self.reservation_value)
            return self.all_bids.pop(0)[0]

        # Calculate similarities to the proposed bids of the opponent.
        similarities = [ sum([ self.counter[i][bid.getValue(i)] / (self._progress.getCurrentRound() + 1) for i in bid.getIssues() ]) / len(bid.getIssues()) for bid, u in good_bids ]
        ix = sorted(range(len(similarities)), key=lambda k: similarities[k], reverse=True)[:10]

        # If none of the bids are similar enough, update the utility value.
        if similarities[ix[0]] < (self._progress.getCurrentRound() / self._progress.getTotalRounds()) ** 3 and \
           (self._progress.getCurrentRound() / self._progress.getTotalRounds()) < 0.25:
            self.utility_value = max(self.utility_value - 0.01, self.reservation_value)

        bid = sorted([ good_bids[i] for i in ix ], key=lambda x:x[1], reverse=True)[0]

        # Remove the bid to be placed from the list and return it.
        return self.all_bids.pop(self.all_bids.index(bid))[0]
