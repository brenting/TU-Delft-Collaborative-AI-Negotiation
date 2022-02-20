import logging, random
from collections import Counter
from typing import cast

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Offer import Offer
from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.Settings import Settings
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.issuevalue.Bid import Bid
from geniusweb.issuevalue.Domain import Domain
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profileconnection.ProfileConnectionFactory import (
    ProfileConnectionFactory,
)

class AgentThree(DefaultParty):

    def __init__(self):
        super().__init__()
        self.getReporter().log(logging.INFO, "party is initialized")
        self._profile = None
        self._last_received_bid: Bid = None
        self._best_received_bid = (0.0, None)

        self.utility = 0.9

    def notifyChange(self, info: Inform):
        """This is the entry point of all interaction with your agent after is has been initialised.

        Args:
            info (Inform): Contains either a request for action or information.
        """

        # a Settings message is the first message that will be send to your
        # agent containing all the information about the negotiation session.
        if isinstance(info, Settings):
            self._settings: Settings = cast(Settings, info)
            self._me = self._settings.getID()

            # progress towards the deadline has to be tracked manually through the use of the Progress object
            self._progress = self._settings.getProgress()

            # the profile contains the preferences of the agent over the domain
            self._profile = ProfileConnectionFactory.create(
                info.getProfile().getURI(), self.getReporter()
            )

            # Calculate the reservation value.
            # self.reservation_value = self._profile.getProfile().getUtility(self._profile.getProfile().getReservationBid())
            self.reservation_value = 0.6

            # Create a counter for all the values per issue of the opponent.
            self.counter = dict((k,Counter()) for k in self._profile.getProfile().getUtilities().keys())

            # Create a list of all bids and sort them based on their utility function value.
            self.all_bids = [ (self._profile.getProfile().getUtility(bid), bid) for bid in AllBidsList(self._profile.getProfile().getDomain()) ]
            self.all_bids.sort(key=lambda x:x[0], reverse=True)

            # Filter the list of all bids such that U(s) > 0.8.
            self.good_bids = [ bid for (u, bid) in self.all_bids if u > self.utility]

        # ActionDone is an action send by an opponent (an offer or an accept)
        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()

            # if it is an offer, set the last received bid
            if isinstance(action, Offer):
                self._last_received_bid = cast(Offer, action).getBid()
        # YourTurn notifies you that it is your turn to act
        elif isinstance(info, YourTurn):
            # execute a turn
            self._myTurn()

            # log that we advanced a turn
            self._progress = self._progress.advance()

        # Finished will be send if the negotiation has ended (through agreement or deadline)
        elif isinstance(info, Finished):
            # terminate the agent MUST BE CALLED
            self.terminate()
        else:
            self.getReporter().log(
                logging.WARNING, "Ignoring unknown info " + str(info)
            )

    # lets the geniusweb system know what settings this agent can handle
    # leave it as it is for this course
    def getCapabilities(self) -> Capabilities:
        return Capabilities(
            set(["SAOP"]),
            set(["geniusweb.profile.utilityspace.LinearAdditive"]),
        )

    # terminates the agent and its connections
    # leave it as it is for this course
    def terminate(self):
        self.getReporter().log(logging.INFO, "party is terminating:")
        super().terminate()
        if self._profile is not None:
            self._profile.close()
            self._profile = None


    def getDescription(self) -> str:
        return "Agent version 1"

    def _myTurn(self):
        if self._isGood(self._last_received_bid):
            action = Accept(self._me, self._last_received_bid)

        else:
            # if not, find a bid to propose as counter offer
            bid = self._findBid()
            action = Offer(self._me, bid)

        # send the action
        self.getConnection().send(action)

    def _isGood(self, bid):
        if not bid:
            return False

        # Increment the counter of the values per issue.
        for issue in bid.getIssues():
            self.counter[issue][bid.getValue(issue)] += 1

        # Store the bid that has the most utility to us.
        if self._profile.getProfile().getUtility(bid) > self._best_received_bid[0]:
            self._best_received_bid = (self._profile.getProfile().getUtility(bid), bid)

        # Accept the bid if the utility is greater than [0.8, 0.7], depending on current time T.
        return self._profile.getProfile().getUtility(bid) > self.utility

    def _findBid(self) -> Bid:
        if self._progress.getCurrentRound() / self._progress.getTotalRounds() > 0.95 and \
           self._profile.getProfile().getUtility(self._best_received_bid[1]) > self.utility:
            return self._best_received_bid[1]

        self.update_distances()

        if self.closest_bids:
            return [x for _, x in sorted(zip([self._profile.getProfile().getUtility(x) for x in self.closest_bids], self.closest_bids), key=lambda x:x[0], reverse=True)][0]
        else:
            return random.choice(self.good_bids)

        # # Return any of the closest bids, or a good bid as an alternative.
        # return random.choice(self.closest_bids) if self.closest_bids else random.choice(self.good_bids)

    def similarity_to_last_received_bid(self, bid: Bid):
        if not bid or not self._last_received_bid:
            return 0

        return sum([ self.counter[issue][bid.getValue(issue)] / (self._progress.getCurrentRound() + 1) for issue in bid.getIssues()])

    def update_distances(self):
        distances = [ self.similarity_to_last_received_bid(bid) for bid in self.good_bids ]
        closest_bids = [ (x,y) for x,y in sorted(zip(self.good_bids, distances), key=lambda x:x[1], reverse=True) ]
        self.closest_bids = [ x for x,y in closest_bids[:10] ]

        if closest_bids and closest_bids[0][1] < (self._progress.getCurrentRound() / self._progress.getTotalRounds())**3 * 5.0:
            self.utility = max(self.utility - 0.01, self.reservation_value)
            self.good_bids = [ bid for (u, bid) in self.all_bids if u > self.utility]
