# Bus Torino
I have made the structure of this skill, the implementation of the database is leave to you.

## Implement your favourite Database
Personally I love PostgreSQL so I made a simple interface:

```
lambda/
├── postgres_interface/
│   ├── db_utility.py
│   └── ...
└── ...
```

Inside `db_utility.py` you have two functions:

```python
def save_bus_and_stop(self, bus, stop):
    response = False
    # Add query to save in the db and a True response if the query went ok
    return response
```

and 

```python
def get_stop_from_bus(self, bus):
    stop = None
    # Add query to retrieve the stop number from the db
    return stop
```

which you can implement and are called by `lambda_function.py`

## Let's speak with Alexa

With this Alexa Skill you can ask to Alexa when will arrive your favourite Gtt bus. It's very simple!

### Save bus and stop

First you save using Alexa the stop and the bus like this:

`Alexa, apri gtt e salva nella fermata {stop} il pullman {bus}`

or

`Alexa, apri gtt e salva il pullman {bus} nella fermata {stop}`

where `{stop}` and `{bus}` are respectively the stop number and the bus number.

### Retrieve bus time

THEN you can ask Alexa when your favourite bus will arrive like this:

`Alexa, chiedi a gtt quando passa il {pullman}`

or

`Alexa, chiedi a gtt tra quanto passa il {pullman}`
