import sys
import os
from time import sleep
import datetime
from base64 import b64decode
import myTools.ModuleInstaller as mi

# Check if the version of Python is appropriate:
mi.Python_version()

try: 
    import pandas as pd
except ImportError:
    mi.installModule('pandas')
    import pandas as pd

try: 
    import pyodbc
except ImportError:
    mi.installModule('pyodbc')
    import pyodbc

def deobf(string):
    return b64decode(string).decode()


def printSplashScreen():

    print('\n\n            ******************** WELCOME IN THE SURVEY_SAMPLE A19 PROJECT ********************')
    print('\n\nTHIS SCRIPT ALLOWS TO EXTRACT SURVEY DATA FROM THE SAMPLE CALLED \"Survey Sample A19\"')
    print('\n\nIT REPLICATES THE BEHAVIOUR OF A STORED PROCEDURE & TRIGGER IN A PROGRAMMATIC WAY')
    print('\n\nNB: At the end, the table will be exported as CSV file in your current folder.')
    print('\n\nCOMMAND LINES OPTIONS ARE: Please type -h or --help to print the help content on the console')
    print('\n\n\t\t\t\t    -------------------------------\n\n')


def get_all_survey_data_sql(connection):

    # Templates to fill columns:
    answer_column = 'CONVERT(VARCHAR, COALESCE((SELECT a.Answer_Value FROM Answer AS a WHERE a.UserId = u.UserId AND a.SurveyId = {} AND a.QuestionId = {}), -1)) AS ANS_Q{}'
    
    null_columnn = 'NULL AS ANS_Q{}'

    outer_union_query = 'SELECT UserId, {} AS SurveyId, {} FROM [User] AS u WHERE EXISTS (SELECT * FROM Answer AS a WHERE u.UserId = a.UserId AND a.SurveyId = {})'
    
    # Retrieving the "name" of the survey, useful later on to iterate:
    surveycursor = 'SELECT SurveyId FROM Survey ORDER BY SurveyId'
    surveycursor = pd.read_sql(surveycursor, connection)['SurveyId']
    
    # Query with dummy variable allowing to know which question is used in the surveys:
    current_question_cursor = 'SELECT * FROM (SELECT SurveyId, QuestionId, 1 AS InSurvey FROM SurveyStructure WHERE SurveyId = {} \
    UNION SELECT {} AS SurveyId, Q.QuestionId, 0 AS InSurvey FROM Question AS Q WHERE NOT EXISTS (SELECT * FROM SurveyStructure AS S WHERE S.SurveyId = {}\
    AND S.QuestionId = Q.QuestionId)) AS t ORDER BY QuestionId'
    
    # Useful string variable:
    current_union_query_block = ''
    
    # Building of the final set:
    for i in surveycursor:
        
        current = pd.read_sql(current_question_cursor.format(i, i, i), connection)
        
        columns_query_part = ''
        
        # Recomposition of the queries according to the questions contained in each survey and addition of punctuation necessary:
        for index in current.index:
            
            if current.InSurvey[index] == 0:
                
                if index < len(current.index)-1:
                    columns_query_part += null_columnn.format(str(current.QuestionId[index])) + ', '
                else:
                    columns_query_part += null_columnn.format(str(current.QuestionId[index]))
            
            elif current.InSurvey[index] == 1:
                
                if index < len(current.index)-1:
                    columns_query_part += answer_column.format(current.SurveyId[index], current.QuestionId[index], str(current.QuestionId[index])) + ', '
                else:
                    columns_query_part += answer_column.format(current.SurveyId[index], current.QuestionId[index], str(current.QuestionId[index]))
        
        if i < len(surveycursor):
            current_union_query_block += outer_union_query.format(i, columns_query_part, i) + ' UNION '
        else:
            current_union_query_block += outer_union_query.format(i, columns_query_part, i)
    
    sorted_query = current_union_query_block + 'ORDER BY UserId'       # Ascending sorting by UserId 

    final_query = pd.read_sql(sorted_query, connection).fillna('NULL')  # Replacing 'None' by 'NULL'
    
    # Displaying the whole dataset:
    pd.set_option("display.max_rows", final_query.shape[0])
    
    return final_query, current_union_query_block


def refresh_survey_view(connection, sql_query):
    
    # Updating the current view in a pickle file in order to compare it with any subsequent changes:
    print('\nPickle file of the current structure survey saving in current folder...')
    if os.access(os.getcwd(), os.W_OK): # Checking that the file directory is writable
        try:
            sql_query.to_pickle('./survey_view.pkl')
            sleep(1)
            print('\nDone.')
        except Exception:
            raise Exception
            sys.exit(0)
    else:
        print('\nPickle file not saved!\nPlease check your administrator rights')
        sys.exit(0)


    # Exporting a CSV file with the consultation date:
    if os.access(os.getcwd(), os.W_OK): # Checking that the file directory is writable
        print('\nYour CSV file is saving in current folder...')
        try:
            get_all_survey_data_sql(connection)[0].to_csv(f'./last_view_{datetime.date.today()}_{str(datetime.datetime.now().hour).zfill(2)}h{str(datetime.datetime.now().minute).zfill(2)}.csv', sep=';', index_label="Index")
            sleep(1)
            print('\nCompleted!')
        except Exception:
            raise Exception
            sys.exit(0)
    else:
        print('\nCurrent CSV file not saved!\nPLease check your administrator rights.')
        sys.exit(0)

        
    # Updating the view in the rdbms:
    print('\nRefreshing the view. Please wait for a few seconds...\n')
    try:
        sql_survey_data = 'CREATE OR ALTER VIEW vw_AllSurveyData AS {}'.format(get_all_survey_data_sql(connection)[1])
        cursor = connection.cursor()
        cursor.execute(sql_survey_data)
        connection.commit()
        # Close the cursor and delete it
        cursor.close()
        del cursor
    except Exception:
        print('\nConnection issue! Please try to connect again.')
        sys.exit(0)



def main():

    # First help:
    if len(sys.argv)==1:
        print('Please type --help command')
        sys.exit(0)

    # Presentation of the program
    printSplashScreen()

    # Help:
    if sys.argv[1] == '--help' or sys.argv[1] =='-h':
        print('\n\n\WELCOME IN THE HELP CONTENT:')
        print('\nServer name, Username and Password are requiered in the command line.')
        print('You must write -s before your SQL Server name.')
        print('You must write -u before your SQL Username.')
        print('You must write -p before your SQL Password.')
        print('NB: Keep the order above!')
        print('\nExample: python.exe Python_SQL_Project.py -s LAPTOP-DEMO123EX\SQL2019 -u myUserName -p myPassword')
        sys.exit(0)
    
    # Storing the arguments of connection:
    try:
        if sys.argv[1] == '-s':
            servername = sys.argv[2]
            if sys.argv[3]== '-u':
                username = sys.argv[4]
                if sys.argv[5]== '-p':
                    password = sys.argv[6]
                else:
                    pass
            else:
                pass
        else:
            print('Please type --help command')
            sys.exit(0)
    except Exception:
        raise Exception('Error in writing the arguments')
        print('Please type --help command')
        sys.exit(0)

    #srvr = b'TEFQVE9QLTdJOFZHTVNPXFNRTDIwMTk='
    #usr = b'c2E='
    #pwd = b'Z29zcWw='
    #cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER={deobf(srvr)};DATABASE=Survey_Sample_A19;UID={deobf(usr)};PWD={deobf(pwd)};')
    
    # Searching the first valid driver and trying to connect:
    print('\nSearching drivers')
    sleep(1)

    print('\nDrivers found:')
    for x in pyodbc.drivers():
        print(x)
    
    print('\nTrying to connect. Please wait...')
    if pyodbc.drivers():
        for driver in pyodbc.drivers():
            try:
                cnxn = pyodbc.connect(f'DRIVER={driver};SERVER={servername};DATABASE=Survey_Sample_A19;UID={username};PWD={password};')
                # Quick check of connection and execution on the server:
                check = cnxn.cursor()
                check.execute('SELECT 1')
                check.close()
                del check
                print('\nConnected server.\n\nCurrent driver: '+ driver)
                print('\nEnjoy!\n')
                break      # Do not need to test other drivers further.
            except pyodbc.Error as err:
                print('\nError: %s' %err)
                continue
    else:
        print('\nSuitable drivers not found.\nEnd of the program.')
        sys.exit(0)
    
    # Current connection with creation of cursor:
    try:
        cnxn.cursor()
    except pyodbc.Error as ne3:
        raise ne3
        sys.exit(0)
    
    # Connecting to the survey structure and saving it as dataframe:
    try:
        survey_structure = "SELECT * FROM SurveyStructure"
        survey_structure_1 = pd.read_sql(survey_structure, cnxn)
    except Exception as excep2:
        print('\nError: %s' %excep2)

    refresh_survey_view(cnxn, survey_structure_1)

    survey_structure_2 = pd.read_sql(survey_structure, cnxn)
    
    # Matching the last survey structure available to the one stored in the current folder
    try:
        if survey_structure_2.to_string() == pd.read_pickle('./survey_view.pkl').to_string():
            pass
        else:
            # If new survey structure, it acts as the trigger:
            refresh_survey_view(cnxn, survey_structure_2)
    
        print(get_all_survey_data_sql(cnxn)[0])
        print(f'\nLast view: {datetime.date.today()} {str(datetime.datetime.now().hour).zfill(2)}:{str(datetime.datetime.now().minute).zfill(2)}')

        # Close the database connection
        cnxn.close()
    except Exception as excep3:
        print('\nError: %s' %excep3)

if __name__ == '__main__':
    main()