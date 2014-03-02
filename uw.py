from twill.commands import *
import paramiko
from getpass import getpass

#potrzebne w if __name__="__main__"
import argparse
from os import remove
import config

#Klasa do poruszania sie po usosie
class Usos():
	def __init__(self):
		self.loggedIn=False
	
	#metoda logujaca
	def logIn(self, pw=None, pesel=None):
		#Wiem, global, brzydko ale trudno. Jeden global na skrypt ujdzie
		global verbose
		if not pesel:
			self.login=raw_input('PESEL: ')
		else:
			self.login=pesel
		if not pw:
			self.password=getpass()
		else:
			self.password=pw
		go('https://logowanie.uw.edu.pl/cas/login')
		fv('1','username',self.login)
		fv('1','password',self.password)
		try:
			submit('3')
			self.loggedIn=True
			
			#"Easier to ask for forgiveness than permission"
			try:
				verbose
			except NameError:
				verbose=True
			if verbose:
				print 'Usos - zalogowano.'
		except:
			print 'Error 10: Logowanie nie powiodlo sie.'
	
	#metoda rejestrujaca na przedmiot
	def register(self, url):
		if self.loggedIn:
			go(url)
			submit('1')
		else:
			print 'Error 11: Uzytkownik niezalogowany.'


#Klasa do poruszania sie po serwerze mimuw
class Ssh():
	def __init__(self):
		self.host="students.mimuw.edu.pl"
		self.port=22
		self.loggedIn=False
		self.mailList=[]
		
		self.client=paramiko.SSHClient()
		self.client.load_system_host_keys()
		self.client.set_missing_host_key_policy(paramiko.WarningPolicy)
	
	def logIn(self, login=None, pw=None):
		global verbose
		try:
			if not login:
				self.login=raw_input('login: ')
			else:
				self.login=login
			if not pw:
				self.password=getpass()
			else:
				self.password=pw
			
			self.client.connect(self.host, username=self.login, password=self.password, port=self.port)
			self.loggedIn=True
			try:
				verbose
			except NameError:
				verbose=True
			if verbose:
				print "Ssh - zalogowano."
		except:
			print "Error 20: Logowanie nie powiodlo sie."
	
	def execute(self, command):
		if self.loggedIn:
			stdin, stdout, stderr = self.client.exec_command(command)
			if stderr:
				print stderr.read()
			if stdout:
				return stdout.read()
		else:
			print "Error 21: Uzytkownik niezalogowany."
	
	def checkMail(self):
		if self.loggedIn:
			stdin, stdout, stderr = self.client.exec_command('cd Mail/Maildir/new;ls')
			stdoutCopy=stdout.read()
			if stdoutCopy != '':
				try:
					verbose
				except NameError:
					verbose=True
				if verbose:
					print "Nowa poczta!"
				mailList=stdoutCopy.split('\n')
				mailCount=1
				
				for mail in mailList:
					if mail!='':
						print mailCount, mail
						self.mailList.append(mail)
					mailCount+=1
			
			else:
				try:
					verbose
				except NameError:
					verbose=True
				if verbose:
					print "Nie ma nowych wiadomosci"
	
	def displayMail(self):
		if self.loggedIn:
			if self.mailList==[]:
				try:
					verbose
				except NameError:
					verbose=True
				if verbose:
					print "Nie ma nowych wiadomosci"
			else:
				mailCount=1
				for mail in self.mailList:
					stdin, stdout, stderr = self.client.exec_command('cd Mail/Maildir/new;cat ' + mail)
					print "Wiadomosc nr ", mailCount, "/", len(self.mailList)
					
					stdoutCopy=stdout.read()
					mailLines=stdoutCopy.split('\n')
					for line in mailLines:
						if 'From: ' in line:
							mailFrom=line
						elif 'Subject: ' in line:
							mailSubject=line
						elif 'Date: ' in line:
							mailDate=line
					print mailDate + '\n' + mailFrom + '\n' + mailSubject
					
					mailCount+=1
		else:
			print "Error 31: Uzytkownik niezalogowany"

#Skrypt
if __name__=="__main__":
	parser=argparse.ArgumentParser()
	
	parser.add_argument("--verbose", "-v", action="store_true")
	parser.add_argument("--usos", "-u", action="store_true")
	parser.add_argument("--ssh", "-s", action="store_true")
	parser.add_argument("--mail", "-m", action="store_true")
	
	parser.add_argument("--pesel", "-p")
	parser.add_argument("--login", "-l")
	parser.add_argument("--password", "-pw")
	
	args=parser.parse_args()
	
	#zmieniam konfiguracje nadpisujac niektore wartosci
	for key, value in vars(args).items():
		try:
			if config.vars[key]==False and value==True:
				config.vars[key]=True
		except KeyError:
			config.vars[key]=value
	
	verbose=config.vars['verbose']
	
	redirect_output('dummy')
	
	if config.vars['usos']:
		UsosClient=Usos()
		UsosClient.logIn(pesel=config.vars['pesel'], pw=config.vars['password'])
	if config.vars['ssh']:
		SshClient=Ssh()
		try:
			SshClient.logIn(login=config.vars['login'], pw=UsosClient.password)
		except NameError:
			SshClient.logIn(login=config.vars['login'], pw=config.vars['password'])
		if config.vars['mail']:
			SshClient.checkMail()
			#TODO: dekodowanie znakow
			SshClient.displayMail()
	
	remove('dummy')