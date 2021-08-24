import subprocess
import sys

def __isConda()-> bool:
    """Function to check if a Conda environnment is enabled"""
    if 'conda' in sys.executable or 'python' in sys.executable:
        return True

def Python_version():
    """Function to check if the version of Python is greater than or equal to 3.6"""
    if not (sys.version_info.major == 3 and sys.version_info.minor >= 6):
        print("A version of Python greater than or equal to 3.6 is required.")
        print("You use Python {}.{}.".format(sys.version_info.major, sys.version_info.minor))
        print("The program ")
        sys.exit(1)

def installModule(package):
    """Function created in order to install module not available on the viewer environment"""
    if __isConda() == True:
        print('Installing the package '+package+'\n')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

