# Event search configuration

If wanted the event search process is highly configurable, if not a default configuration will be generated based on the experiment definition.

As seen in [event search](event_search.md) there are four steps in the event search and each step is configurable.

---

## Echo Search

Echo search configuration is specified in the [hardtarget documentation](https://danielk.developer.irf.se/hardtarget/analyse/method/echo_search/).

---

## Echo post process and noise calculation

The echo post process and noise calculation can be configured with the event search configuration:

::: metecho.events.types.EventSearchCfg

---

## Meteor Search

To correctly configure each of the search functions the event criteria cconfiguration is used, it is defined in the following way:

::: metecho.events.types.EventCriteriaCfg

---

## Event clusters

To properly define the window of a event it can be configured with the following parameters:

::: metecho.events.types.EventSelectCfg
