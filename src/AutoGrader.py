from __future__ import print_function
import os
import time
import sys
#import thread
#from threading import Thread
import subprocess
import signal
from syntaxhighlighter_3_0_83 import *

AUTO_GRADER_VERSION = "0.94"

"""
0.8 - Initial separation from AutoGrader App
0.82 - Added "No Input File" option when input file list is empty
0.84 - Added option to include source code in output/added line numbers
0.85 - option to add sourcefile name added
0.86 - _findFiles() function generalized to work with filenames, not just extentions
0.88 - removed text file output capability
0.89 - added c++ support
0.90a - added total # of projects processed to output file.
0.91 - pkill used to terminate processes that run too long; output files are now presented in sorted order
0.92 - Python3 support added
0.93 - monolithic html output files now contain all JS and CSS content
0.94 - javascript grade entry added

"""

class AutoGrader:
    """class to automatically analyze Python code by automating the input data and tabulating the output"""
    class Const:
        """class that contains misc. constants related to the AutoGrader class"""
        #misc constants
        PROG_OUTPUT_START_TOKEN = "@@@_START_TOKEN_@@@"
        PROG_OUTPUT_END_TOKEN = "@@@@_END_TOKEN_@@@"
        PYTHON_WHITE_SPACES = ' \t\n\r'
        HTML_TAB_CHAR = '<pre style="display:inline;">&#9;</pre>'
        #html color constants
        HEADER_COLOR1 = "blue"      #color of the main header (source file name)
        HEADER_COLOR2 = "green"     #color of sub-headers (test file names)
        ANALYTICS_COLOR1 = "orange" #color for source file analytics
        ANALYTICS_COLOR2 = "brown"  #color for execution time output
        OUTPUT_COLOR = "black"      #main output color
        ERROR_COLOR = "red"         #color indicating an error
        FEEDBACK_COLOR = "purple"   #color of "instructor feedback" text
        LINE_NUMBER_COLOR = "gray"  #color for code line numbers
        #CSS_DIRECTORY = ".css"

    def __init__(self):
        if sys.version_info >= (3, 0):
            self.python2 = False
        else:
            self.python2 = True

    def openFile(self, *arg):
        '''create a stub for the file() function which exists in Python2, but is replaced by the open() function in Python3.
        Also, take advantage of this stub to specify the unicode encoding for Python3'''
        if self.python2 == True:
            return file(*arg)
        else:
            return open(*arg, encoding='utf-8')
    
    def analyzeCppCode(self, sourceFile):
        """function that counts linenumbers, and estimates the # of comments in
        the supplied C++ sourceFile.  The function returns a tuple with the format
        (numLines, numComments)."""
        numLines = 0        # Number of lines of code
        numComments = 0     # Number of comments in the code

        f=self.openFile(sourceFile)
        for line in f:
            numLines += 1;
            loc = 0
            while (loc != -1):       #count the # of times the '/*' characters appears
                loc = line.find("#", loc)
                if (loc != -1):
                    loc += 1
                    numComments += 1
                    
            loc = 0
            loc = line.find('//', loc)      #count the # of times the '//' characters appears
            if (loc != -1):
                loc += 1
                numComments += 1
                       
        f.close()
        return numLines, numComments



        

    def analyzePythonCode(self, sourceFile):
        """function that counts linenumbers, and estimates the # of comments and # of tokens in
        the supplied Python sourceFile.  The function returns a tuple with the format
        (numLines, numDocStr, numComments, numDefs, numClasses)."""
        numLines = 0        # Number of lines of code
        numDocStr = 0       # Number of doc strings in code
        numComments = 0     # Number of comments in the code
        numDefs = 0         # Number of functions
        numClasses = 0      # Number of classes
        f=self.openFile(sourceFile)
        for line in f:
            numLines += 1;
            loc = 0
            while (loc != -1):       #count the # of times the '#' characters appears
                loc = line.find("#", loc)
                if (loc != -1):
                    loc += 1
                    numComments += 1
            loc = 0
            while (loc != -1):
                loc = line.find('"#', loc)      #discount the # of times the '#' char appears as the 1st char in double quotes (skip hex constants)
                if (loc != -1):
                    loc += 1
                    numComments -= 1
            loc = 0
            while (loc != -1):
                loc = line.find("'#", loc)      #discount the # of times the '#' char appears as the 1st char in single quotes (skip hex constants)
                if (loc != -1):
                    loc += 1
                    numComments -= 1
            loc = 0
            while (loc != -1):                  #count the # of ''' found
                loc = line.find("'''", loc)
                if (loc != -1):
                    loc += 1
                    numDocStr += 1
            loc = 0
            while (loc != -1):                  #count the # of """ found
                loc = line.find('"""', loc)
                if (loc != -1):
                    loc += 1
                    numDocStr += 1

            if line.strip(AutoGrader.Const.PYTHON_WHITE_SPACES) != '':
                if line.strip(AutoGrader.Const.PYTHON_WHITE_SPACES).split()[0] == 'def':              #count # of defs
                    numDefs += 1
                if line.strip(AutoGrader.Const.PYTHON_WHITE_SPACES).split()[0] == 'class':            #count # of classes
                    numClasses += 1
                       
        f.close()
        numDocStr /= 2       #assume that the """ and ''' chars appear in pairs   
        return numLines, numDocStr, numComments, numDefs, numClasses

    def _MakeHtmlHeader(self, outputFile, language, title="AutoGrader", header_text=""):
        """create the html header in the supplied outputFile"""

        if language == 'C++':
            brush = shBrushCpp_js
        if language == 'Python':
            brush = shBrushPython_js
            
        html_header = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
	<title>''' + title + '''</title>
	<script type="text/javascript">''' + shCore_js + '''</script>
	<script type="text/javascript">''' + brush + '''</script>
	<style type="text/css" rel="stylesheet">''' + shCoreDefault_css + '''</style>
	<script type="text/javascript">SyntaxHighlighter.all();</script>
</head>

<body style="background: white; font-family: Helvetica">
<form encrypt="multipart/form-data" action="" method="POST">
<h1>''' + header_text + '''</h1>
        '''
        f=self.openFile(outputFile, "a")    #open for appending
        f.write(html_header)
        f.close()


    def _removeFile(self, filename):
        """function that deletes a file without raising an exception if the file can't be removed or doesn't exist."""
        try:
            #delete the output file
            os.remove(filename)
        except:
            #print ("Failed to remove the file: " + filename)
            pass


    def _fileHead(self, sourceFile, destFile, maxNumLines, maxNumBytes):
        """function that appends the first maxNumLines lines or first maxNumBytes bytes (whichever is smaller) from sourceFile to destFile."""
        #os.system('head -n ' + str(numLines) +' "' + sourceFile +'" >> "' + destFile + '"')
        os.system('head -c ' + str(maxNumBytes) + ' "' + sourceFile + '" | head -n ' + str(maxNumLines) + ' >> "' + destFile + '"')


    def _threadExec(self, cmd):
        os.system(cmd)  #execute the py script in a shell
        return

    def _compileCppFiles(self, compiler, sourceFiles, outputFile, exeFile, maxOutputLines):
        f=self.openFile(outputFile, "a")    #open for appending
        #Delineate the start of the unformatted py code output with a token: PROG_OUTPUT_START_TOKEN.
        #Flank with '\n's to ensure the token is on a line by itself
        f.write ('<font face="verdana" color=" ' +AutoGrader.Const.HEADER_COLOR2 + '"><br>\n------------- compiler output -------------</font>\n')
        f.write('<pre><font face="courier" color="' + AutoGrader.Const.OUTPUT_COLOR + '">')
        f.close()

        tmpFile = outputFile.strip() + '.AB'
        self._removeFile(tmpFile)
        self._removeFile(exeFile)
        #compile the code
        compile_args = '"' + compiler + '" -o "' + exeFile +'" '

        for sourceFile in sourceFiles:
            #include only .cpp files (not .h or .hpp files) on the g++ command line
            if sourceFile[-4:] == '.cpp' or sourceFile[-3:] == '.cc':
                compile_args = compile_args + '"' + sourceFile+ '" '

        #store the compiler output to a temp file    
        compile_args = compile_args + '> "' + tmpFile + '" 2>&1'
        
        print ("compiling:" + compile_args)
        os.system(compile_args)

        #copy the first maxOutputLines from the temp file to the output file
        #Also, limit the # bytes to 40*maxOutputLines (this avoids large output files due to ridiculously long lines)
        self._fileHead(tmpFile, outputFile, maxOutputLines, 40*maxOutputLines)
        self._removeFile(tmpFile)
        
        f=self.openFile(outputFile, "a")    #open for appending
        f.write('</font></pre>')
        f.close()


         
    def _shellExec(self, interpreter, sourceFile, dataFile, outputFile, maxRunTime, maxOutputLines):
        """function to execute source code in a shell using a specified interpreter.
        interpreter = full path or name of script interpreter (examples: python, /usr/bin/python2.7, etc.)
        sourceFile = full path of the script to be executed
        dataFile = file from which stdin data will be redirected.  Set to an empty string if the script requires no data input.
        outputFile = file to which both stdout and stderr will be redirected
        bRecompile - when using C++, set to True to compile before executing.  When set to False, execute without recompiling."""
        #Build the shell command to execute the py script or C++ program with appropriate stdin, stdout and stderr redirection
        #Enclose all file names with double quotes for the shell.
        #Add a 2>&1 to the command line so that stderr (2) is redirected to stdout (1)
        #stdin(0) is redirected from dataFile; stdout(1) is redirected to outputFile
        #stderr(2) is redicted to stdout(1), which is itself redirected to outputFile
        
        f=self.openFile(outputFile, "a")    #open for appending
        #Delineate the start of the unformatted py code output with a token: PROG_OUTPUT_START_TOKEN.
        #Flank with '\n's to ensure the token is on a line by itself
        f.write('<pre><font face="courier" color="' + AutoGrader.Const.OUTPUT_COLOR + '">')
        f.close()

        tmpFile = outputFile.strip() + '.AB'
        self._removeFile(tmpFile)

        #set the working directory to the directory of the source file
        if sourceFile == '':
            source = ' '
            cwd = '.'
        else:
            source = ' "' + sourceFile + '"'
            cwd = os.path.split(sourceFile)[0]
            
        if dataFile == '':
            _args = interpreter + source + ' >> "' + tmpFile + '" 2>&1'
        else:
            _args = interpreter + source + ' < "' + dataFile + '" >> "' + tmpFile + '" 2>&1'

                
        #print ("Executing: " + _args)
        
        start_time = time.time()
        p = subprocess.Popen(args=_args, shell=True, cwd=cwd)    #the pid returned appears to be the pid of the shell
        elapsed_time = time.time() - start_time
        
        while p.poll() == None and elapsed_time < maxRunTime:
            elapsed_time = time.time() - start_time
            print ("*", end='')
            
        #copy the first maxOutputLines from the temp file to the output file
        #Also, limit the # bytes to 40*maxOutputLines (this avoids large output files due to ridiculously long lines)
        self._fileHead(tmpFile, outputFile, maxOutputLines, 40*maxOutputLines)
        self._removeFile(tmpFile)

        #kill the process, if it has exceeded its max run time
        if elapsed_time >= maxRunTime:
            print ("Killing process {0}. Run time exceeds max value of {1} seconds.".format(p.pid, maxRunTime))
            p.terminate()       #try a s/w termination
            time.sleep(1)       #wait 1 second
            p.kill()            #force the termination

            os.system('kill -9 ' + str(p.pid))  #appears to be the pid of the shell
            
            #This is a hack.  The pid returned by subprocess.Popen() seems to be the ID of
            #the shell (the function is called wiht the shell=True option).
            #We anecdotally add 1 to get the pid of the child process started by the shell.
            #Look into using subprocess.run() for a better solution.
            os.system('kill -9 ' + str(p.pid+1))

            #finally, for good measure (C++ only) ...
            os.system('pkill AG.out')    #just kill all AG.out processes
           
            ##wait for child to terminate
            #maxTimetoWaitForChildTermination = 5.0
            #start_time = time.time()
            #elapsed_time2 = 0.0
            #while p.poll() == None and elapsed_time < maxTimetoWaitForChildTermination:
            #    elapsed_time2 = time.time() - start_time
            #    print "*",
            
            self._reportErrorMsg("<br>Maximum execution time of {0} seconds exceeded.  Process forcefully terminated... output may be lost.".format(maxRunTime), outputFile)

        
        f=self.openFile(outputFile, "a")    #open for appending
        #Delineate the end of the unformatted py code output with a token: PROG_OUTPUT_END_TOKEN
        #Flank with '\n's to ensure the token is on a line by itself
        #f.write('\n' + AutoGrader.Const.PROG_OUTPUT_END_TOKEN + '\n')
        f.write('</font></pre>')
        f.close()
            
        return elapsed_time

    def _gradingBox(self, sourceDirectory, sourceFile, outputFile, gradingTextLabel):
        '''function that creates the instructor grading box.  This box is pre-polated with the student's name'''
        #extract the student name from the sourceFile name: remove the leading sourcedirectory
        #name and note that Moodle begins the submitted filename with the student's name followed
        #by an '_'
        student_name = sourceFile.split(sourceDirectory)[1].split('_')[0].strip('/')
        f=self.openFile(outputFile, "a")    #open for appending
        f.write ('<font face="courier" color="' + AutoGrader.Const.FEEDBACK_COLOR + '">')
        f.write('<br>Instructor Feedback for '+student_name+'</font><br><textarea name="'+gradingTextLabel+'" rows=4 cols=80>'+student_name+'\nGrade: \nComments: </textarea><br><br>')
        f.close()
        

    def _reportFileAnalytics(self, sourceFiles, outputFile, language):
        """function that gets and reports source code analytics to the destination file in the
        specified format (AutoGrader.Const.TEXT or AutoGrader.Const.HTML)"""
        
        #is this a single file or a set of files?
        bSingleFile = len(sourceFiles) == 1
        
        #open the output file for appending
        f=self.openFile(outputFile, "a")    #open for appending
        f.write ('<font face="verdana" color="' + AutoGrader.Const.HEADER_COLOR1 + '">')
        f.write ('<br>\n=======================================================<br>\n')
        if bSingleFile:
            f.write(sourceFiles[0])    #if this is a single file, simply output its name
        else:   #if these are multiple files, list the directory name in bold
            f.write('<b>' + os.path.split(sourceFiles[0])[0] + '</b>') #directory name in bold
        f.write ('<br>\n=======================================================<br>\n</font>')

        #for each file, report the analytics
        for sourceFile in sourceFiles:
            if bSingleFile == False:    #only print the filename if we have more than 1 file in the list
                f.write ('<font face="verdana" color="' + AutoGrader.Const.HEADER_COLOR1 + '">')
                f.write(os.path.split(sourceFile)[1] + '</font><br>\n')
                    
            if language == 'C++':
                numLines, numComments = self.analyzeCppCode(sourceFile)
                f.write ('<font face="courier" color="' + AutoGrader.Const.ANALYTICS_COLOR1 + '">Code Lines: ' + str(numLines))
                f.write ('<br>\n~#Comments: ' + str(numComments) + '<br>\n')
                
            if language == 'Python':
                numLines, numDocStr, numComments, numDefs, numClasses = self.analyzePythonCode(sourceFile)
                f.write ('<font face="courier" color="' + AutoGrader.Const.ANALYTICS_COLOR1 + '">Code Lines: ' + str(numLines))
                f.write (AutoGrader.Const.HTML_TAB_CHAR*2 + '~#Functions:  ' + str(numDefs))
                f.write (AutoGrader.Const.HTML_TAB_CHAR*2 + '~#Classes: ' + str(numClasses))
                f.write ('<br>\n~#Comments: ' + str(numComments))
                f.write (AutoGrader.Const.HTML_TAB_CHAR*2 + '~#DocStrs: ' + str(numDocStr) + '<br>\n')
                        
            f.write('</font><br>') #skip a line between entries
        f.close()


    def _reportExecTime(self, exec_time, outputFile):
        """function that reports execution time to the output file in the specified
        format (AutoGrader.Const.TEXT or AutoGrader.Const.HTML)"""
        f=self.openFile(outputFile, "a")    #open for appending
        f.write ('<font face="verdana" color="' + AutoGrader.Const.ANALYTICS_COLOR2 + '">[Execution Time: ' + format("%0.4f" % exec_time) + ' sec.]</font><br>\n')
        f.close()


    def _reportDataFile(self, dataFileName, outputFile):
        """function that reports the name of the input data file to the outputFile in the specified format.
        dataFileName = the name of the data file to be reported in the output file
        outputfile = the name of the output file (this is the same file that receives stdout and stderr from the executed script
        outputFileType = format of outputFile (AutoGrader.Const.TEXT or AutoGrader.Const.HTML)"""
        #subsequent access to the file should be open for "append"-ing
        f=self.openFile(outputFile, "a")    #open for appending
        f.write ('<font face="verdana" color=" ' +AutoGrader.Const.HEADER_COLOR2 + '"><br>\n------------- ' + os.path.split(dataFileName)[1] + ' -------------</font>\n')
        f.close()


    def _writeOutput(self, msg, outputFile):
        """print the supplied message in red to the output file.  Use this function
        when the output file is not already open."""
        f=self.openFile(outputFile, "a")    #open otuputFile for appending
        f.write (msg)
        f.close()


    def _reportErrorMsg(self, ErrorMessage, outputFile):
        """print the supplied message in red to the supplied file.  Use this function
        when the output file is not already open."""
        f=self.openFile(outputFile, "a")    #open otuputFile for appending
        self._insertErrorMsg(ErrorMessage, f)
        f.close()

                
    def _insertErrorMsg(self, ErrorMessage, outputFileObject):
        """print the supplied message is red to the supplied output file object.
        Use this function when the outputfile is already open (you have a file object)."""
        outputFileObject.write('<font color="' + AutoGrader.Const.ERROR_COLOR + '">')
        outputFileObject.write (ErrorMessage)
        outputFileObject.write('</font>')


    def _formatSource(self, sourceFiles, outputFile, language):
        """function that inserts the source code into the output file"""
        f=self.openFile(outputFile, "a")    #open otuputFile for appending

        for sourceFile in sourceFiles:                       
            #read in input file
            with self.openFile(sourceFile) as inputFile:
                preprocessedSource = inputFile.read()
                inputFile.close()
                
            #replace every occurence of '<' with '&lt' in the source file for the syntax highlighter
            source = preprocessedSource.replace('<', '&lt')
                
            f.write('<font face="courier" color="' + AutoGrader.Const.HEADER_COLOR2 + '">')
            f.write ('-------------  BEGIN LISTING: ' + os.path.split(sourceFile)[1] + ' -------------</font><br>\n')
            if language == 'C++':
                f.write('<pre class="brush: cpp;">')
            if language == 'Python':
                f.write('<pre class="brush: python;">')
            f.write(source)
            f.write('</pre>')

            f.write('<font face="courier" color="' + AutoGrader.Const.HEADER_COLOR2 + '">')
            f.write ('-------------   END LISTING: ' + os.path.split(sourceFile)[1] + ' -------------</font><br>\n')
                        
        f.close()


    def _printSeparator(self, filePointer, color=Const.HEADER_COLOR1):
        """function that prints a separator in the output file"""
        filePointer.write ('<font face="verdana" color=" ' + color + '"><br>\n=======================================================</font><br>\n')

    
    def _openFileAndPrintSeparator(self, outputFile, color=Const.HEADER_COLOR1):
        """function that prints a separator in the output file after opening the file"""
        f=self.openFile(outputFile, "a")    #open for appending
        _printSeparator(f, color)
        f.close()


    def _findFilesInDir(self, directory, extension=".py", foundFiles=None):
        """function that searches the specified 'directory' for files
        with the supplied extention.  The function returns a list of these files or appends to the
        supplied foundFiles list."""

        #mutable default arguments in Python are evaluated once when the function is defined, not each time the function is called.
        if foundFiles == None:
            foundFiles = []
            
        filenames = os.listdir(directory)
        for filename in filenames:
            #need to verify that the entity is a file (this avoids problems when directory names have file extensions)
            if filename[-len(extension):] == extension and filename[0:1] != '.' and os.path.isfile(directory + '/' + filename):
                foundFiles.append(directory + '/' + filename)
                print ('===>' + filename)
        return foundFiles


    def _findFiles(self, topLevelDirectory, extension=".py", foundFiles=None):
        """function that searches the supplied topLevelDirectory and all sub-directories for files
        with the supplied extention.  The function returns a list of these files or appends to the
        supplied foundFiles list."""
        
        #mutable default arguments in Python are evaluated once when the function is defined, not each time the function is called.
        if foundFiles == None:
            foundFiles = []
        
        for dirpath, dirnames, filenames in os.walk(topLevelDirectory):
            for filename in filenames:
                #need to verify that the entity is a file (this avoids problems when directory names have file extensions)
                if filename[-len(extension):] == extension and filename[0:1] != '.' and os.path.isfile(dirpath+"/"+filename):
                    foundFiles.append(dirpath+"/"+filename)
                    #print dirpath+"/"+filename
        return foundFiles
 
    def _recursivelyFindFiles(self, topLevelDirectory, extension=".py"):
        """function that searches the supplied topLevelDirectory and all sub-directories for files
        with the supplied extention.  The function returns a list of these files in the top-level directory
        (self.TopLevelFilesFound) along with a list of sub-directories containing these files
        (self.SubDirsFound)."""
        print ('finding ' + extension + '...\n')
        tempFilesFound = []
        tempSubDirs = {}    #initialize temporary dictionary of sbudirectories
        
        for dirpath, dirnames, filenames in os.walk(topLevelDirectory):
            #print 'dirpath= ' + dirpath
            for filename in filenames:
                #check file extension and verify this is not a hidden file
                #also need to verify that the entity is a file (this avoids problems when directory names have file extensions)
                if filename[-len(extension):] == extension and filename[0] != '.' and os.path.isfile(dirpath+"/"+filename):
                    #print 'filename = ' + dirpath +'/'+filename
                    if dirpath == topLevelDirectory:
                        tempFilesFound.append(dirpath+"/"+filename)
                    else:
                        #print '********* '
                        #print dirpath
                        tempSubDirs[dirpath] = True

                ##recursively search sub-directories
                #for dirname in dirnames:
                    ##ignore directories with names that begin with a '.' or '_'
                    #if dirname[0] != '.' and dirname[0] != '_':
                         #self._findFiles(dirname, extension)
                         
        #self.SubDirsFound=self.subdirs.keys()

        #in Python 3 dict.keys(), dict.values() and dict.items() will all return iterable views instead of lists                   
        if sys.version_info >= (3, 0):
            return (tempFilesFound, list(tempSubDirs.keys()))
            
        return (tempFilesFound, tempSubDirs.keys())


    def _recursivelyFindFile(self, topLevelDirectory, filename):
        """function that searches the supplied topLevelDirectory and all sub-directories for a file
        with the supplied filename.  The function returns a list of these sub-directories."""
        print ('finding ' + filename + '...\n')
        tempSubDirs = {}    #initialize temporary dictionary of sbudirectories
        
        for dirpath, dirnames, filenames in os.walk(topLevelDirectory):
            #print '---dirpath---'
            #print dirpath
            #print '---dirnames---'
            #print dirnames
            #print '---filenames---'
            #print filenames
            #print '------'
            for f in filenames:
                #check filenames for a match
                if f == filename:
                    tempSubDirs[dirpath] = True

        #in Python 3 dict.keys(), dict.values() and dict.items() will all return iterable views instead of lists                   
        if sys.version_info >= (3, 0):
            return list(tempSubDirs.keys())
                         
        return tempSubDirs.keys()

                
    def processFiles(self, testDataFiles, sourceDirectory, sourceFilename, outputFile, language, IncludeSourceInOutput, maxRunTime, interpreter, maxOutputLines, AutoGraderVersion):
        """ TestDataFiles - list of test data files as full path strings
        sourceDirectory - top level directory containing .py files (all sub directories will be searched)
        soruceFilename - specifies the name of the .py file to search and execute.  Set to "" or None to search/execute all .py files in the sourceDirectory.
        OutputFile - destination txt or html file
        Language - either "C++" or "Python"
        IncludeSourceInOutput - boolean; if True, output will contain full listing of each source file
        maxRunTime - the maximum execution time in integer seconds.  After this number of seconds, the running code will be forcefully terminated.
        interpreter - a string representing the tool to use (e.g. 'g++ -Wall' or '/usr/bin/python' """
        
        print ("***Start***")
        self.sourceDirectory = sourceDirectory
        #self.TopLevelFilesFound = []
        #self.subdirs = {}    #dictionary of sbudirectories
        

        #delete the output file
        self._removeFile(outputFile)

        #create the html header.  Use the name of the source directory as the header text.
        self._MakeHtmlHeader(outputFile, language, "AutoGrader", os.path.split(sourceDirectory)[-1])

        #--------- C++ ---------
        if language == 'C++':
            #call _recursivelyFindFiles to generate the self.TopLevelFilesFound and self.SubDirsFound lists
            (self.TopLevelFilesFound, self.SubDirsFound) = self._recursivelyFindFiles(sourceDirectory, ".cpp")
            (tlf, sd) = self._recursivelyFindFiles(sourceDirectory, ".cc")

            self.TopLevelFilesFound += tlf
            self.SubDirsFound += sd

            exeFile = sourceDirectory + '/' + 'AG.out'


            def doInnerCppProcessing(sourceFiles, gradingTextLabel): #sourceFiles is a list of filenames
                #get/report the analytics on the source files
                self._reportFileAnalytics(sourceFiles, outputFile, language)
                
                #include source code here if selected
                if IncludeSourceInOutput == True:
                    self._formatSource(sourceFiles, outputFile, language)

                #compile the file
                self._removeFile(exeFile)
                self._compileCppFiles(interpreter, sourceFiles, outputFile, exeFile, maxOutputLines)

                if os.path.isfile(exeFile): #did the compilation succeed?
                    print("Compilation succeeded.")
                    self._reportErrorMsg("Compilation succeeded.<br>", outputFile)                    
                    if len(testDataFiles) == 0:     #no input data required
                        exec_time = self._shellExec('"'+exeFile+'"', '', '', outputFile, maxRunTime, maxOutputLines)
                        print (format("%0.4f" % exec_time) + " secs.")
                    else:
                        for dataFile in testDataFiles:
                            self._reportDataFile(dataFile, outputFile)
                            
                            #print the name of the datafile to indicate progress.  This is a temporary solution to allow us to identify
                            #programs that don't end.  Ultimately, we will want to use a fork()/wait() pair and be able to set a max run time.
                            _, filename =  os.path.split(dataFile)
                            print ("processing '" + filename + "'...")
                            exec_time = self._shellExec('"'+exeFile+'"', '', dataFile, outputFile, maxRunTime, maxOutputLines)

                            print (format("%0.4f" % exec_time) + " secs.")
                            self._reportExecTime(exec_time, outputFile)
                        print ()
                else:
                    print("Executable not found. Check compiler output.")
                    self._reportErrorMsg("Executable not found. Check compiler output.<br>", outputFile)

                self._removeFile(exeFile)
                self._gradingBox(sourceDirectory, sourceFiles[0], outputFile, gradingTextLabel)
                return


            #compile the names of single-file programs and multi-file programs into a single list to enable sorting.
            #note that this is a list of tuples.  The first element is the name of the file or directory.
            #the second element specifies if the first is a filename or directory name.
            filesAndDirs = []
            for x in self.TopLevelFilesFound:
                filesAndDirs.append((x,'file')) #add files

            for x in self.SubDirsFound:
                filesAndDirs.append((x,'dir'))  #add directories

            filesAndDirs.sort()     #sort the list

            print ("**********************************")
            for x in filesAndDirs:
                print (x)
            print ("**********************************")

            #now, process the sorted list depending on whether it is a single-file or directory.
            for n, x in enumerate(filesAndDirs):
                if x[1] == 'file':   #this is a file
                    #we will process source code in the top-level directory as single-file programs                                                
                    print ('=======================================================')
                    print (x[0])
                    print ('=======================================================')
                    #doInnerCppProcessing([x[0]], 'student'+str(n))
                    doInnerCppProcessing([x[0]], 'student')
                elif x[1] == 'dir':     #this is a directory
                    #we will process source code in sub-directories of the top-level directory as multi-file programs
                    print ('=======================================================')
                    print (x[0])
                    print ('=======================================================')
                    sourceFiles = []
                    self._findFilesInDir(x[0], ".cpp", sourceFiles)  #add .h files to the files list
                    self._findFilesInDir(x[0], ".cc", sourceFiles)  #add .h files to the files list
                    self._findFilesInDir(x[0], ".h", sourceFiles)  #add .h files to the files list
                    self._findFilesInDir(x[0], ".hpp", sourceFiles)  #add .hpp files to the files list
                    #doInnerCppProcessing(sourceFiles, 'student'+str(n))
                    doInnerCppProcessing(sourceFiles, 'student')
                else:
                    print ("***** EXCEPTION: Entity for processing is neither a file nor a directory. *****")
                    
                
            self._reportErrorMsg('<br><br><b>**** ' + str(len(self.TopLevelFilesFound) + len(self.SubDirsFound)) + ' project(s) processed. ****</b>', outputFile)

        #--------- Python ---------
        elif language == 'Python':
            print ('Find sub dirs')
            #first, find all the subdirectories that contain a python source file that matches <sourceFilename>
            #(_, self.SubDirsFound) = self._recursivelyFindFiles(sourceDirectory, sourceFilename)
            #(_, self.SubDirsFound) = self._recursivelyFindFiles(sourceDirectory, '/' + sourceFilename)
            self.SubDirsFound = self._recursivelyFindFile(sourceDirectory, sourceFilename)

            print ('Find TLFs')
            #now, find all .py files in the top level directory.
            self.TopLevelFilesFound = self._findFilesInDir(sourceDirectory, ".py", [])
            #(self.TopLevelFilesFound, _) = self._recursivelyFindFiles(sourceDirectory, ".py")


            #does this block do anything??? 9/25/16
            #if sourceFilename == "" or sourceFilename == None:
                #self._recursivelyFindFiles(sourceDirectory, ".py")
            #else:
                #self._recursivelyFindFiles(sourceDirectory, '/' + sourceFilename)


            def doInnerPythonProcessing(sourceFiles, topLevelModule, gradingTextLabel): #sourceFiles is a list of filenames
                #get/report the analytics on the source files
                self._reportFileAnalytics(sourceFiles, outputFile, language)
                
                #include source code here if selected
                if IncludeSourceInOutput == True:
                    self._formatSource(sourceFiles, outputFile, language)


                if len(testDataFiles) == 0:     #no input data required
                    exec_time = self._shellExec('"'+interpreter+'"', topLevelModule, '', outputFile, maxRunTime, maxOutputLines)
                    print (format("%0.4f" % exec_time) + " secs.")
                    self._reportExecTime(exec_time, outputFile)
                else:
                    for dataFile in testDataFiles:
                        self._reportDataFile(dataFile, outputFile)
                        
                        #print the name of the datafile to indicate progress.  This is a temporary solution to allow us to identify
                        #programs that don't end.  Ultimately, we will want to use a fork()/wait() pair and be able to set a max run time.
                        _, filename =  os.path.split(dataFile)
                        print ("processing '" + filename + "'...")
                        exec_time = self._shellExec('"'+interpreter+'"', topLevelModule, dataFile, outputFile, maxRunTime, maxOutputLines)

                        print (format("%0.4f" % exec_time) + " secs.")
                        self._reportExecTime(exec_time, outputFile)
                    print ()
                    
                self._gradingBox(sourceDirectory, sourceFiles[0], outputFile, gradingTextLabel)
                return


            #compile the names of single-file programs and multi-file programs into a single list to enable sorting.
            #note that this is a list of tuples.  The first element is the name of the file or directory.
            #the second element specifies if the first is a filename or directory name.
            filesAndDirs = []
            for x in self.TopLevelFilesFound:
                filesAndDirs.append((x,'file')) #add files

            for x in self.SubDirsFound:
                filesAndDirs.append((x,'dir'))  #add directories

            filesAndDirs.sort()     #sort the list

            print ("**********************************")
            for x in filesAndDirs:
                print (x)
            print ("**********************************")


            #now, process the sorted list depending on whether it is a single-file or directory
            for n, x in enumerate(filesAndDirs):
                if x[1] == 'file':   #this is a file
                    #we will process source code in the top-level directory as single-file programs                                                
                    print ('=======================================================')
                    print (x[0])
                    print ('=======================================================')
                    #doInnerPythonProcessing([x[0]], x[0], 'student'+str(n))
                    doInnerPythonProcessing([x[0]], x[0], 'student')
                elif x[1] == 'dir':     #this is a directory
                    #we will process source code in sub-directories of the top-level directory as multi-file programs
                    print ('=======================================================')
                    print (x[0])
                    print ('=======================================================')
                    #doInnerPythonProcessing(self._findFilesInDir(x[0],".py", []), x[0]+'/'+sourceFilename, 'student'+str(n))
                    doInnerPythonProcessing(self._findFilesInDir(x[0],".py", []), x[0]+'/'+sourceFilename, 'student')
                else:
                    print ("***** EXCEPTION: Entity for processing is neither a file nor a directory. *****")
                    
                
            self._reportErrorMsg('<br><br><b>**** ' + str(len(self.TopLevelFilesFound) + len(self.SubDirsFound)) + ' project(s) processed. ****</b>', outputFile)



        #--------- Unknown language ---------
        else:
            print ('Unknown language choice: ' + language)
            return

        
        self._reportErrorMsg('<br><font face="verdana">', outputFile)
        self._reportErrorMsg('Report Generator: AutoGrader v' + AutoGraderVersion  + '<br>', outputFile)
        if language == 'C++':
            self._reportErrorMsg('C++ Compiler: ' + interpreter + '<br>', outputFile)
        elif language == 'Python':
            self._reportErrorMsg('Python Interpreter: ' + interpreter + '<br>', outputFile)
        else:
            self._reportErrorMsg('Compiler/Interpreter: Not Specified <br>', outputFile)
        self._reportErrorMsg('<br></font>', outputFile)

        self._writeOutput('''<font size='+6'><input type="button" style="font-size:20px;width:250px" value="Download Feedback" OnClick="download_feedback_file()">
        <br><br></font></form>''', outputFile)


        feedback_filename = 'feedback.txt'
        download_script = '''
        <script type="text/javascript">

        function download_feedback_file()
        {
        
          x = document.getElementsByName("student").length
          msg = ""
          for (i=0; i<x; i++)
          {
                msg = msg + document.getElementsByName("student")[i].value
                msg = msg + '\\n\\n-------------------------------------------------------\\n'
          }

          var element = document.createElement('a');
          element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(msg));
          element.setAttribute('download', "''' + feedback_filename + '''");

          element.style.display = 'none';
          document.body.appendChild(element);

          element.click();

          document.body.removeChild(element);
        }

        </script>
        </body></html>

        '''
        self._writeOutput(download_script, outputFile)

        self._writeOutput('</body></html>', outputFile)

        
        #open the output file using the default application
        cmd = 'open "' + outputFile + '"'
        os.system(cmd)
            
        print ("***End***\n")



        #---------  ---------

