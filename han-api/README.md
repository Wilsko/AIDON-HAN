Python palvelut, jotka lukevat HAN-kortin tuottamat tiedot sqlite3-kantoihin

- sensor-reader.py tallettaa mittaridatan sensor_data.db kantaan sekä määrävälein kulutustiedot historiakantoihin sensor_data_15min.db ja sensor_data_history.db (1 tunnin välein)

- gpio-switch-reader.py tallettaa GPIO-kytkintiedot gpio_data.db kantaan ja  kytkimen tilamuutokset gpio_changes.db kantaan

- mgmt-data-reader.py tallettaa sarjalinjalta luettavat kytkin- ja lämpötilatiedot mgmt_data.db kantaan ja tilamuutokset mgmt_changes kantaan

- watchdog.py lukee kannoista viimeisten talletustebn aikaleimat ja hälyttää mikäli ne tulkitaan vanhentuneiksi

han-api.py julkaisee kantojen tietoja json-muotoiltuna
