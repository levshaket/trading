# PYTHON LIBRARY TO TEXT OR CALL A PHONE NUMBER


#MODULES
import os, keyring
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse


#TWILIO (calling service) FUNCTIONS

def set_twilio_acct(acct_nickname, acct_phone, acct_number, acct_token):
	sequence = '{}/{}/{}'.format(acct_phone, acct_number, acct_token)
	keyring.set_password('twilio', acct_nickname, sequence)

def get_twilio_acct(acct_nickname):
	acct_details = keyring.get_password('twilio', acct_nickname).split('/')
	return acct_details

def text(recipient, msg, acct_nickname='basic'):
	recipient_phone = get_recipient_phone(recipient)
	acct_phone, acct_number, acct_token = get_twilio_acct(acct_nickname)  
	twilio = Client(acct_number, acct_token)
	twilio.api.account.messages.create(to=recipient_phone,from_=acct_phone,body=msg)
	
def call(recipient, msg='https://demo.twilio.com/docs/voice.xml', acct_nickname='basic'):
	recipient_phone = get_recipient_phone(recipient)
	acct_phone, acct_number, acct_token = get_twilio_acct(acct_nickname)  
	twilio = Client(acct_number, acct_token)
	twilio.api.account.calls.create(to=recipient_phone,from_=acct_phone,url=msg)

def voice_msg(msg):
	voice = VoiceResponse()
	voice.say(msg)
	voice.hangup()
	return str(voice)

#RECIPIENT (phone number) FUNCTIONS
	
def set_recipient_phone(recipient, phone_number):
	keyring.set_password('phone',recipient, phone_number)

def get_recipient_phone(recipient):
	phone_number = keyring.get_password('phone',recipient)
	return phone_number
	
#OS SYSTEM (notify) FUNCTIONS

def beep(freq=440, dur=0.2):
	os.system('play --no-show-progress --null --channels 1 synth {} sine {}'.format(dur,freq))
	
def say(msg):
	os.system('spd-say "{}"'.format(msg))
