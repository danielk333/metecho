# Event Search

::: metecho.events.event_search.event_search

---

## Search steps

The event search is a four step process that is highly configurable, more information about the configuration is available at [configuration](configuration.md).

### 1. Echo post process

From the echo search we have echo information for each ipp. The echo post process steps gathers the information that can be extracted over several ipp's. Extracting information that spans over "Windows" in the data that the hardtarget library cannot handle.

::: metecho.events.event_search.echo_post_process

### 2. Calculate gaussian noise

From the echo search a mean and standard deviation is estimated per ipp. In this step the gaussian noise is calculated in windows spanning several ipp's to get a correct gaussian noise esitmation. Any "peaks" in the correlation for each ipp are filtered out already in the echo search analysis to get a correct noise estimation.

::: metecho.events.event_search.calculate_noise

### 3. Meteor Search

In this step the echo is searched for meteor events. By default there are six search functions that will iterate through the echo. The amount of matches per coherent integration is configurable for a confirmed match. The meteor search will also not just return confirmed events but also sort them into meteor and meteor trails. So the output of this step is each ipp where a meteor is present, each ipp is where a meteor trail is present and the amount of matches per ipp (from the search functions).

::: metecho.events.event_search.meteor_search

### 4. Event clusters

At last event clusters are created from the gathered data. The events are clustered based on the meteor and meteor trail arrays, the post processed echo and the noise. Windows that contains several events are also separated so that there is no event overlap or merged into one.

::: metecho.events.event_search.create_event_cluster

---
