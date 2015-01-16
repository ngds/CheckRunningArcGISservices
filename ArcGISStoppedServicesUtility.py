# Checks ArcGIS Server service folders for stopped services
# Restarts stopped services
# Prints names of stopped services to console
# Sends email notification for stopped services
# Source: http://resources.arcgis.com/en/help/main/10.1/index.html#/Example_Check_a_folder_for_stopped_services/0154000005tr000000/
# Source: http://resources.arcgis.com/en/help/main/10.1/index.html#/Example_Stop_or_start_all_services_in_a_folder/0154000005qv000000/
# Source: http://www.bytecreation.com/blog/2013/8/11/send-email-in-python-using-gmail-google-apps-account-or-exchange 

# For Http calls
import httplib, urllib, json

# For system tools, 
import sys, datetime, os

#Import Python modules for sending email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# For reading passwords without echoing
import getpass

# Defines the entry point into the script
def main(argv=None):
    # Print some info
    print
    print "This tool is a sample script that detects stopped services in a folder."
    print  
    
    # Ask for admin/publisher user name and password
    username = "serveradmin"
    password = "AZadmin416server"
    
    # Ask for server name
    serverName = "apatite"
    serverPort = 6080

    folders = ["ROOT","aasggeothermal", "baselayers", "geologic_maps", "NGDS", "OneGeology","test"]

    # Create a list to hold stopped services
    stoppedList = []
    
    # Get a token
    token = getToken(username, password, serverName, serverPort)
    if token == "":
        print "Could not generate a token with the username and password provided."
        return
    
    # Construct URL to read folder
    for folder in folders:
        try:    
            if str.upper(folder) == "ROOT":
                folder = ""
            else:
                folder += "/"
                    
            folderURL = "/arcgis/admin/services/" + folder
            
            # This request only needs the token and the response formatting parameter 
            params = urllib.urlencode({'token': token, 'f': 'json'})
    
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            
            # Connect to URL and post parameters    
            httpConn = httplib.HTTPConnection(serverName, serverPort)
            httpConn.request("POST", folderURL, params, headers)
            
            # Read response
            response = httpConn.getresponse()
            if (response.status != 200):
                httpConn.close()
                print "Could not read folder information."
                return
            else:
                data = response.read()
                
                # Check that data returned is not an error object
                if not assertJsonSuccess(data):          
                    print "Error when reading folder information. " + str(data)
                else:
                    print "Processed folder information successfully. Now processing services..."

                # Deserialize response into Python object
                dataObj = json.loads(data)
                httpConn.close()

                # Loop through each service in the folder and stop or start it    
                for item in dataObj['services']:

                    fullSvcName = item['serviceName'] + "." + item['type']

                    # Construct URL to stop or start service, then make the request                
                    statusURL = "/arcgis/admin/services/" + folder + fullSvcName + "/status"
                    httpConn.request("POST", statusURL, params, headers)
                    
                    # Read status response
                    statusResponse = httpConn.getresponse()
                    if (statusResponse.status != 200):
                        httpConn.close()
                        print "Error while checking status for " + fullSvcName
                        return
                    else:
                        statusData = statusResponse.read()
                                      
                        # Check that data returned is not an error object
                        if not assertJsonSuccess(statusData):
                            print "Error returned when retrieving status information for " + fullSvcName + "."
                            print str(statusData)

                        else:
                            # Add the stopped service and the current time to a list
                            statusDataObj = json.loads(statusData)
                            if statusDataObj['realTimeState'] == "STOPPED":
                                stoppedList.append([fullSvcName,str(datetime.datetime.now())])
                                # Construct URL to stop or start service, then make the request                
                                startServiceURL = "/arcgis/admin/services/" + folder + fullSvcName + "/START"
                                httpConn.request("POST", startServiceURL, params, headers)
                                          
                    httpConn.close()           
        except:
            pass
    # Check number of stopped services found
    if len(stoppedList) == 0:
        print "No stopped services detected in folder " + folder.rstrip("/")        
    else:
        # Write out all the stopped services found
        # This could alternatively be written to an e-mail or a log file
        for item in stoppedList:
            print "Service " + item[0] + " was detected to be stopped at " + item[1]
            #Where the email is being sent to (multiple email address example given if needed)
            #If only one is needed just delete the 2nd address as per the comment example below
            #emailto   = ['first@emailaddress.com']
            emailto   = ['sysadmin@azgs.az.gov', 'christy.caudill@azgs.az.gov', 'laura.bookman@azgs.az.gov', 'ron.palmer@azgs.az.gov']

            #Who the email is being sent from (if using gmail this is ignored, can only send from account owners adddress)
            emailfrom = 'APATITE STOPPED SERVICES MONITOR'

            #Put email message info together. Edit subject line if needed.
            message = MIMEMultipart('alternative')
            message['To'] = ", ".join(emailto)
            message['From'] = emailfrom
            message['Subject'] = 'Stopped Services on Apatite'

            #Details of your SMTP server (gmail SMTP url & port entered, change if needed)
            #If you're using an exchange server, port 587 should work as well
            deetsurl = smtplib.SMTP("10.208.11.37")
            #deetsuser = ""
            #deetspassword = ""

            #Connect to the SMTP server and authenticate using TLS encryption
            #If using exchange this should work as well as long as TLS is enabled on the server
            deetsurl.ehlo()
            #deetsurl.starttls()
            deetsurl.ehlo()
            #deetsurl.login(deetsuser, deetspassword)
            #Create your plain text message
            plaintextemailmessage = unicode("Service " + item[0] + " was detected to be stopped at " + item[1] + ". Service was restarted.") 
            #Add the HTML and plain text messages to the message info list (array)
            storeplain = MIMEText(plaintextemailmessage, 'plain')
            message.attach(storeplain)
            deetsurl.sendmail(emailfrom, emailto, message.as_string())
            deetsurl.quit()
    return

# A function to generate a token given username, password and the adminURL.
def getToken(username, password, serverName, serverPort):
    # Token URL is typically http://server[:port]/arcgis/admin/generateToken
    tokenURL = "/arcgis/admin/generateToken"
    
    params = urllib.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'})
    
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    
    # Connect to URL and post parameters
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", tokenURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Error while fetching tokens from admin URL. Please check the URL and try again."
        return
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):            
            return
        
        # Extract the token from it
        token = json.loads(data)        
        return token['token']            
        

# A function that checks that the input JSON object 
#  is not an error object.
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True
    
        
# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
