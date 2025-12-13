from singledispatchmethod import singledispatchmethod

from .state import WorldState
import rideshare_simulator.events as events


class Simulator(object):
    def __init__(self, request_generator, driver_generator,
                 dispatch_policy_A, dispatch_policy_B, dispatch_policy_expt, pricing_policy, **kwargs):
        self.request_generator = request_generator
        self.driver_generator = driver_generator
        self.dispatch_policy_A = dispatch_policy_A
        self.dispatch_policy_B = dispatch_policy_B
        self.dispatch_policy_expt = dispatch_policy_expt
        self.pricing_policy = pricing_policy
        self.state = WorldState(**kwargs)
        self.state.push_event(
            self.driver_generator.generate(self.state)[0])

    def run(self, T=float("Inf")):
        while len(self.state.drivers['A']) <= 10: # make sure there are enough drivers in the system
            event = self.state.pop_event() ##get the next nearest event
            new_events = self.handle_event(event) ##handle event (new_events may occur)
            for new_event in new_events: 
                self.state.push_event(new_event) ##add new event
        self.state.push_event(
            self.request_generator.generate(self.state)[0])
        while not len(self.state.event_queue) == 0 and self.state.ts < T:
            event = self.state.pop_event() ##get the next nearest event
            self.state.step(event.ts) ##Worldstate forwards to the time of the event
            new_events = self.handle_event(event) ##handle event (new_events may occur)
            for new_event in new_events: 
                self.state.push_event(new_event) ##add new event
            yield (self.state, event)

    @singledispatchmethod
    def handle_event(self, event):
        """
        Returns a tuple (updates, new_events), where updates represent
        state changes to be applied to self.state, and new_events represents
        future events to be added to self.state.event_queue.

        This is the main point at which state mutation occurs.
        """
        raise NotImplementedError("No handler for event of type {cls}"
                                  .format(cls=type(event)))

    @handle_event.register(events.DriverOnlineEvent)
    def _(self, event: events.DriverOnlineEvent):
        """
            a new driver is added 
        """
        self.state.add_driver(event.driver) ## add this driver to WorldState
        offline_event = events.DriverOfflineEvent(
            event.ts + event.shift_length, event.driver.id)  ## add the event that the driver leaves the network
        return self.driver_generator.generate(self.state) + [offline_event] ## also add the event for the next new driver 

    @handle_event.register(events.DriverOfflineEvent)
    def _(self, event: events.DriverOfflineEvent):
        """
            a driver is leaving the network
        """
        for policy in ['A','B','expt']:
            self.state.drivers[policy][event.driver_id].go_offline()
        return []

    @handle_event.register(events.RequestDispatchEvent)
    def _(self, event: events.RequestDispatchEvent):
        self.state.riders[event.rider.id] = event.rider
        next_request = self.request_generator.generate(self.state)
        # dispatch
        dispatch_A = self.dispatch_policy_A.dispatch('A', self.state, event)
        dispatch_B = self.dispatch_policy_B.dispatch('B', self.state, event)
        dispatch_expt = self.dispatch_policy_expt.dispatch('expt', self.state, event)
        # make an offer
        if len(dispatch_A) > 0:
            offer_A = self.pricing_policy.make_offer(dispatch_A)
            is_accepted_A = event.rider.respond_to_offer(offer_A)
            response_event_A = events.OfferResponseEvent(
                ts=event.ts,
                policy='A',
                treatment=0,
                rider_id=event.rider.id,
                driver_id=dispatch_A[0],
                route=dispatch_A[1],
                offer=offer_A,
                cost=dispatch_A[3],
                accepted=is_accepted_A)
        else:
            offer_A = self.pricing_policy.make_offer(None)
            response_event_A = events.OfferResponseEvent(
                ts=event.ts,
                policy='A',
                treatment=0,
                rider_id=event.rider.id,
                driver_id=None,
                route=None,
                offer=offer_A,
                cost=None,
                accepted=None)
        if len(dispatch_B) > 0:
            offer_B = self.pricing_policy.make_offer(dispatch_B)
            is_accepted_B = event.rider.respond_to_offer(offer_B)
            response_event_B = events.OfferResponseEvent(
                ts=event.ts,
                policy='B',
                treatment=1,
                rider_id=event.rider.id,
                driver_id=dispatch_B[0],
                route=dispatch_B[1],
                offer=offer_B,
                cost=dispatch_B[3],
                accepted=is_accepted_B)
        else:
            offer_B = self.pricing_policy.make_offer(None)
            response_event_B = events.OfferResponseEvent(
                ts=event.ts,
                policy='B',
                treatment=1,
                rider_id=event.rider.id,
                driver_id=None,
                route=None,
                offer=offer_B,
                cost=None,
                accepted=None)
        if len(dispatch_expt) > 0:
            offer_expt = self.pricing_policy.make_offer(dispatch_expt)
            is_accepted_expt = event.rider.respond_to_offer(offer_expt)
            response_event_expt = events.OfferResponseEvent(
                ts=event.ts,
                policy='expt',
                treatment=int(self.dispatch_policy_expt.is_treated(event)),
                rider_id=event.rider.id,
                driver_id=dispatch_expt[0],
                route=dispatch_expt[1],
                offer=offer_expt,
                cost=dispatch_expt[3],
                accepted=is_accepted_expt)
        else:
            offer_expt = self.pricing_policy.make_offer(None)
            response_event_expt = events.OfferResponseEvent(
                ts=event.ts,
                policy='expt',
                treatment=int(self.dispatch_policy_expt.is_treated(event)),
                rider_id=event.rider.id,
                driver_id=None,
                route=None,
                offer=offer_expt,
                cost=None,
                accepted=None)
        return [response_event_A, response_event_B, response_event_expt] + next_request
        
    @handle_event.register(events.OfferResponseEvent)
    def _(self, event: events.OfferResponseEvent):
        if event.accepted:
            self.state.drivers[event.policy][event.driver_id].route = event.route
        return []
