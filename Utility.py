import os, os.path, pwd, pdb, docket, json, subprocess, datetime, dateutil.parser, pprint, commands, base64, uuid
from Crypto.Cipher import AES
import tarfile
from pytz import timezone, reference
from pathlib2 import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import Encoders
from contextlib import contextmanager
import smtplib
import hashlib
import glob

@contextmanager
def changedir(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

class Utility(object):
    """
    This module provides an array of utility functions that saves alot of time
    in writing and repeating all over.
    Utility functions that can be class/static methods only are expected via this
    class
    """
    @classmethod
    def getUserName(cls):
        """
        This function returns the currently logged in user.
        :returns    : A non-empty string of the currently logged in user
        """"
        return pwd.getpwuid(os.geteuid()).pw_name

    @classmethod
    def getHostName(cls):
        """
        This function returns the fully qualified hostname of the localhost
        :returns    : A non-empty string of localhost's name
        """
        return socket.getfqdn()

    @classmethod
    def slurpFile(cls, filePath):
        """
        This function reads the contents of the file provided in filePath and 
        returns it as a string.
        :param filePath : The path to the file whose contents are to be read
        :returns    : String contents of the file. If the file is not available
                      or the contents cannot be read for any reason, _None_ will
                      be returned
        """"
        if (os.path.exists(filePath)):
            try:
                contents = Path(filePath).read_text()
                return contents
            except Exception as e:
                print "An exception occurred when reading the file [%s]" % str(e)
        return None

    @classmethod
    def readJSONFile(cls, filePath):
        """
        This function reads the json contents of the file provided in filePath
        and returns it as a json object
        :param filePath    : The path to the file whose contents are to be read
        :returns    : A valid json objet created from the file contents. If
                      the file is not available or the contents cannot be read
                      for any reason, _None_ will be returned.
        """
        if (os.path.exists(filePath)):
            try:
                contents = Path(filePath).read_text()
                jsonContent = json.loads(contents)
                return jsonContent
            except Exception as e:
                print "An exception occurred when reading the JSON file [%s]" % str(e)

        return None

    @classmethod
    def writeJSONFile(cls, filePath, jsonObject):
        """
        This function writes the json contents to a file
        :param filePath    : the file path to be writted to
        :param jsonObject    : The jsonObject to be persisted to the file
        """
        if (os.path.exists(filePath)):
            try:
                with open(filePath, 'w') as jsonFile:
                    json.dump(jsonObject, jsonFile, sort_keys=True,
                              indent=4, separators=(',', ': '))
            except Exception as e:
                print "An exception occurred when reading the JSON file [%s]" % str(e)

        return None

    @classmethod
    def executeCommand(cls, command):
        """
        This function executes a shell command on the localhost and returns the
        output displayed on the console.
        :param command : The shell command to be executed on the localhost
        :returns    : A tuple containing the return code of the command executed
                      along with the contents of stdout
        """
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        res = p.sstdout.readlines()
        return (p.returncode, res)

    @classmethod
    def convertUTCToTimeZone(cls, utcdatetime, timezonestring):
        """
        This function is used to convert the date and time provided in UTC to
        a region specific timezone provided in the timezonestring parameter.
        :param utcdatetime    : The date and time in UTC format
        :param timezonestring : The timezone as string identical to that seen 
                                in the system timezone database e.g.
                                Asia/Singapore
        :returns              : The datetime converted to timezone specific time
        """
        destTimeZone = timezone(timezonestring)
        UTCDateTime = dateutil.parser.parse(utcdatetime)
        DestDateTime=UTCDateTime.astimezone(destTimeZone)

        return DestDateTime

    @classmethod
    def sendEmail(cls, sendTo, sendFrom, cc, subject, attachments=[],
                  message="", mesageFormat="html", encodeAttachment=True):
        """
        This function is used to convert a 
        :param sendTo           : The email id to whch the email is to be sent
                                  Multiple email id's can be separated using a comma
        :param sendFrom         : The email id of the user who is sending the email
        :param cc               : The email id's to which the email is copied to.
                                  Multiple email id's can be separated using a comma
        :param subject          : A string containing the subject of the email
        :param attachments      : A list of paths to files that are to be attached
                                  to the email
        :param message          : A string containing the email message
        :param messageFormat    : Format of the message to be sent text/html
        :param encodeAttachment : Base64 encoding needed (True/False)
        """
        msg = MIMEMultipart('alternative')
        msg["From"] = sendFrom
        msg["To"]   = sendTo
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject

        msg.attach(MIMEText(message, messageFormat))

        for attachment in attachments:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(attachment, "rb").read())
            if encodeAttachment:
                Encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename="%s"' % os.path.basename(attachment))
            msg.attach(part)

        try:
            smtp = smtplib.SMTP()
            smtp.connect('localhost', 25)
            smtp.sendmail(from_addr="", to_addrs=sendTo, msg=msg.as_string())
        except Exception as e:
            print str(e)
        finally:
            smtp.close()
        return

    @classmethod
    def createTarBallPackage(cls, pathToPackage, packageName, destinationPath,
                             exclusionLambda):
        """
        This function creates a tarball containing the files provided in the
        parameter _pathToPackage_.
        :param pathToPackage        : The folder containing files to be compressed
        :param packageName          : The name of the package to be created
        :param destinationPath      : The destination _folder_ where this compressed
                                      file is to be created
        :param exclusionLambda      : The lambda to exclude files that would
                                      otherwise be included in the compressed file.
        """
        leafPathNode = os.path.basename(pathToPackage)
        containingDir = pathToPackage.replace(leafPathNode, "")

        fullPackagePath = "{}/{}".format(destinationPath, packageName)
        if (os.path.exists(fillPackagePath) == False):
            with changedir(containingDir):
                try:
                    with tarfile.open(fullPackagePath, "w:bz2") as tar:
                        tar.add (name=leafPathNode, recursive=True,
                                 exclude=exclusionLambda)
                        os.chmod(fullPackagePath, 0777)
                except Exception as e:
                    print str(e)
        return

    @classmethod
    def generateMD5Sum(cls, filePath="", contentStr=""):
        """
        This function creates an md5 checksum using the contents of the file
        :param filePath        : The path to the file from from which the checksum is to
                                 be generated
        :returns               : A string containing the checksum
        """
        hasher = None
        if filePath != "":
            BLOCKSIZE = 65536
            hasher = hashlib.md5()
            with open(filePath, 'rb') as afile:
                buf = afile.read(BLOCKSIZE)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = afile.read(BLOCKSIZE)
        elif contentStr != "":
            hasher = hashlib.md5(contentStr)

        return hasher.hexdigest()


                    