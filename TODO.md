# Todos

- Fix event printer
- Flag to enable best_data saving
- Disable best_data saving by default
- Change main behaviour to use backend detection for file parsing
- Fix registration system for converters similiar to backend
- Fix ugly fixes in event_search row 154 and 372
- Fix better signal removal (limit to code length?)
- Convert gaussian noise std to xcorr limit
- Better debug logging
- caching of data store to not have to reload file list each time one wants to access the data
- fix a better plug-and-play support system for different radar systems in CLI's (rather than if radar == name)
- Clean up even_search function and fix better granularity
- move from too much OOP formalism in sub-packages

- in metecho.data, change RawDataInterface to RawData, change `backend` to `format`,
- Extract converter from DataStore and separate it, separation of concenrns

- REFACTOR the event search