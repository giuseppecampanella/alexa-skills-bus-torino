# -*- coding: utf-8 -*-

import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

from bs4 import BeautifulSoup
import requests
from datetime import datetime, date

from .postgres_interface import db_utility

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


BUS_STOP = "873"

class Bus():
    def __init__(self, bus_number):
        self.number = bus_number


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Dimmi di quale pullman vuoi sapere l'orario."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class SaveBusAndStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("SaveBusAndStopIntent")(handler_input)
        
    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        bus = slots['bus'].value
        stop = slots['stop'].value
        
        db = db_utility.Database()
        response = db.save_bus_and_stop(bus, stop)
        db.close_db()
        
        if response:
            speak_output = f"Il pullman numero {bus} e' stato salvato nella fermata numero {stop}"
        else:
            speak_output = "C'e' stato un errore, riprova."
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class RetrieveGttBusIntentHandler(AbstractRequestHandler):
    
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("RetrieveGttBusIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        bus = Bus(slots['pullman'].value)

        db = db_utility.Database()
        stop = db.get_stop_from_bus(bus)
        db.close_db()
        
        # if stop is not None it means it was previous saved with SaveBusAndStopIntent
        if stop:
            # http://www.5t.torino.it/5t/trasporto/arrival-times-byline.jsp?kl8w7c0k&action=getTransitsByLine&shortName=2095&routeCallback=lineBranchCtrl.getLineBranch&oreMinuti=04%3A45&gma=17%2F02%2F21
            url = "https://www.muoversiatorino.it/stops/gtt:" + str(stop)
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            _date = soup.find("div", {"class":"date-row"})
            if _date:
                _date = _date.text.split(" ")[1].split(".")
            
            busses = soup.findAll("p", {"class":"departure route-detail-text padding-normal border-bottom"})
            # get information only from the slot-pullman from the user
            three_busses = 3
            speak_output = f"Il pullman numero {bus.number}"
            for b in busses:
                # get bus number
                bus_number = b.find("span", {"class":"route-number"}).text
                
                if bus.number == bus_number:
                    three_busses -= 1
                    # if the pullman is not accessible, break
                    if b.find("span", {"class":"time notaccessible"}):
                        speak_output += " non e' accessibile, riprova con un altro."
                        break
                    
                    # get time for that particular bus
                    _time = b.find("span", {"class":["time realtime accessible", "time accessible"]})
                    # if there's no bus, break
                    if not _time:
                        speak_output += " non e' accessibile, riprova con un altro."
                        break
                    
                    t = _time.text

                    # 'in arrivo'
                    if "In arrivo" in t:
                        speak_output += " e' in arrivo, oppure"
                    # '3 min'
                    elif "min" in t:
                        t = t.split(" ")[0]
                        if int(t) == 1:
                            speak_output += f" passera' tra {str(t)} minuto, il prossimo " 
                        else:
                            speak_output += f" passera' tra {str(t)} minuti, il prossimo" 
                    # '04:32'
                    else:
                        _t = datetime.now()
                        h, m = t.split(":")
                        _t = _t.replace(hour=int(h))
                        _t = _t.replace(minute=int(m))
                        if _date:
                            _t = _t.replace(day=int(_date[0]))
                            _t = _t.replace(month=int(_date[1]))
                            _t = _t.replace(year=int(_date[2]))
                        
                        today = datetime.now()
                        logger.info(f"data calcolata {_t}")
                        logger.info(f"data di oggi {today}")
                        
                        # I think that they are based in Ireland, they are 1 hour late
                        if today.hour == 23:
                            today = today.replace(hour=0)
                        else:
                            today = today.replace(hour=today.hour + 1)
                        diff_date = _t-today
                        # compute what time remains before it's to late to take the bus
                        secs = diff_date.total_seconds()
                        hours = int(secs / 3600)
                        minutes = int(secs / 60) % 60
                        if hours > 0:
                            if hours == 1:
                                speak_output += f" passera' tra {hours} ora" 
                            else:
                                speak_output += f" passera' tra {hours} ore"
                            if minutes != 0:
                                speak_output += " e "
                            else:
                                speak_output += ", il prossimo"
                        else:
                        # if hours == 0:
                            speak_output += " passera' tra"
                        
                        logger.info(secs)
                        logger.info(hours)
                        
                        if minutes > 1:
                            speak_output += f" {minutes} minuti"
                        elif minutes == 1:
                            speak_output += f" {minutes} minuto"
                            
                        if three_busses != 0:
                            speak_output += ", il prossimo"
                    
                else:
                    speak_output += " non e' presente in questa fermata, riprova con un altro."
                    break
                
                # break only whith 3 bus times
                if three_busses == 0:
                    break
        else:
            speak_output = "Non e' stato possibile trovare la fermata, salva prima."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Any cleanup logic goes here.
        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(SaveBusAndStopIntentHandler())
sb.add_request_handler(RetrieveGttBusIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
