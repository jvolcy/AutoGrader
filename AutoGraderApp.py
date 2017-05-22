from __future__ import print_function
import sys

if sys.version_info >= (3, 0):
    from tkinter import *
    import tkinter.ttk as ttk
    import tkinter.filedialog as tkFileDialog
    #import tkinter.messagebox
    import tkinter.scrolledtext as ScrolledText
else:
    from Tkinter import *
    import ttk
    import tkFileDialog
    import tkMessageBox
    import ScrolledText

import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/src")

from AutoGrader import AutoGrader
import SpelmanLogo
import json

AUTO_GRADER_APP_VERSION = "0.98q"
#requires AutoGrader V 0.94 or later


"""
0.5 - Initial release
0.6 - html option
0.7 - AutoGrader class
0.8 - HTML Post-processor added (re-formats program output)
0.82 - Separate files: AutoGrader class moved to file AutoGrader.ph
0.84 - Added "No Input File" option
0.86 - Added option to include top level source code in output/Added line numbers
0.87 - Option to specify source filename added
0.88 - Added option to manage zip files (facilitates working with compressed Moodle downloads)
0.89 - Added Max run time
0.90 - Added Spelman logo
0.91a - notebook configuration pages for Python and C++ added
0.91b - removed plain text output option
0.91c -
0.92 - src sub-directory created
0.93 - unzip bug fixed (missing closing quote in unzip command)
0.94 - pkill used to terminate non-terminating programs; processed projects are reported in alphabetical order
0.95 - Python3 support added; max run time changed to 3 (previously 5)
0.96 - monolithic html output files now contain all JS and CSS content
0.97 - save preferences added
0.98p - javascript grade entry added
0.98q - working directory set to directory of source file

To Do: - 
#Need to provide an option for manual entry instead of test data (which won't work for a gussing game, for example)
#Need to allow user to specify browers or use default
#Need to read feedback file back into HTML page when available

"""


class Application:
    """Controller class for the graphical Python AutoGrader"""
    #misc. constants
    SOURCE_DIRECTORY_SET    = 1<<0
    TEST_DATA_FILES_SET     = 1<<1
    LANGUAGE_SELECTED       = 1<<2
    DEFAULT_MAX_RUN_TIME    = 3     #allow scripts to run for this long by default
    DEFAULT_MAX_OUTPUT_LINES = 100  #max # of output lines by compiler and executing code included in the output html file
    OPTIONS_FILE = 'src/ag_options.json'

    #color constants
    WIDGET_PRE_SET_BACK_COLOR = "#fff0f0"       #this is the back color before a field is set
    WIDGET_SET_BACK_COLOR = "#f0fff0"       #this is the back color after a field is set
    PYTHON_TEXT_COLOR = '#aa00ff'
    CPP_TEXT_COLOR = '#0000ff'
    PYTHON_WND_COLOR = '#f0ddff'
    CPP_WND_COLOR = '#e0e0ff'
    ABOUT_WND_COLOR = '#eeffee'
    ABOUT_TEXT_COLOR = '#006600'

    def __init__(self):
        self.Ready2Start = 0
        self.TestDataFiles = []
        self.autoGrader = AutoGrader()      #instantiate the AutoGrader object
        if sys.version_info >= (3, 0):
            self.python2 = False
            print("Python3")
        else:
            self.python2 = True
            print("Python2")
    
    def ButtonStartClick(self):     #callback for 'Start' button click
        try:
            self.ag_options['max_run_time'] = int(self.MaxRunSpinBox.get())
        except: #if the int() fails (invalid integer), force to DEFAULT_MAX_RUN_TIME
            self.MaxRunSpinBox.delete(0, END)
            self.MaxRunSpinBox.insert(0, str(self.ag_options['max_run_time']))

        try:
            self.ag_options['max_output_lines'] = int(self.MaxOutputLinesSpinBox.get())
        except: #if the int() fails (invalid integer), force to DEFAULT_MAX_OUTPUT_LINES
            self.MaxOutputLinesSpinBox.delete(0, END)
            self.MaxOutputLinesSpinBox.insert(0, self.ag_options['max_output_lines'])
       
        TestDataFiles = [] if self.NoInputCheckBox.get() == 1 else (self.TestDataFiles)
        self.ag_options['include_source_in_output'] = self.IncludeSource.get()

        self.ag_options['py_top_level_module'] = self.pyTopLevelModule.get().strip()
        if self.LangChoice == 'Python':
            sourceFilename = self.ag_options['py_top_level_module']
        else:
            sourceFilename = ""
            
        #source directory
        self.ag_options['top_level_directory'] = self.EntrySourceDirectory.get().strip()

        #check to see if the output file exists.  If it does, ask if it should be overwritten
        OutputFile = self.EntryOutputFile.get().strip()
        if os.path.isfile(OutputFile):
            if self.python2:
                choice = tkMessageBox.askyesno("Output File Exists", "Overwrite '" + OutputFile + "'?")
            else:
                choice = messagebox.askyesno("Output File Exists", "Overwrite '" + OutputFile + "'?")
            if choice == False:     #do not overwrite; simply exit
                return

        #check to see if we should auto uncomprees zip files
        self.ag_options['cpp_auto_unzip'] = self.cppAutoUnzip.get()
        self.ag_options['py_auto_unzip'] = self.pyAutoUnzip.get()
 
        if self.LangChoice == 'C++':
            AutoUnzip = self.ag_options['cpp_auto_unzip']
        elif self.LangChoice == 'Python':
            AutoUnzip = self.ag_options['py_auto_unzip']
            
        zipFiles = self.autoGrader._findFilesInDir(self.ag_options['top_level_directory'], ".zip")
        for zipFile in zipFiles:
            #is there a directory corresponding to the .zip filename?
            dirname = os.path.splitext(zipFile)[0]
            if os.path.isdir(dirname) == False:     #no directory exists with the name of the zip file (assume it has not been unzipped)
                if AutoUnzip == True:
                    choice = True
                else:
                    if self.python2:
                        choice = tkMessageBox.askyesno("zip File Found in Source Directory", "Would you like to unzip the file '" + zipFile + "'?")
                    else:
                        choice = messagegox.askyesno("zip File Found in Source Directory", "Would you like to unzip the file '" + zipFile + "'?")
                        
                if choice == True:
                    #cmd = 'mkdir "' + dirname + '"'
                    cmd = 'unzip "' + zipFile + '" -d "' + dirname + '"'
                    print (cmd)
                    os.system(cmd)


        #interpreter selection
        self.ag_options['cpp_compiler'] = self.cppInterpreter.get().strip()
        self.ag_options['py_interpreter'] = self.pyInterpreter.get().strip()
        if self.LangChoice == 'C++':
            interpreter = self.ag_options['cpp_compiler']
        elif self.LangChoice == 'Python':
            interpreter = self.ag_options['py_interpreter']
        else:
            interpreter = 'None'

        
        print ("Output File: " + OutputFile)
        print ("AutoUnzip: " + str(AutoUnzip))
        print ("LangChoice: " + self.LangChoice)
        print ("TestDataFiles: " + str(TestDataFiles))
        print ("Source Directory: " + self.ag_options['top_level_directory']) 
        print ("sourceFilename: " + sourceFilename)
        print ("includeSource:" + str(self.ag_options['include_source_in_output']))
        print ("maxRunTime: " + str(self.ag_options['max_run_time']))
        print ("interpreter:" + interpreter)
        print ("maxOutputLines" +str(self.ag_options['max_output_lines']))

        #save user options
        self.save_user_options(self.OPTIONS_FILE)

        self.autoGrader.processFiles(testDataFiles=TestDataFiles, sourceDirectory=self.ag_options['top_level_directory'],
            sourceFilename=sourceFilename, outputFile=OutputFile, language=self.LangChoice,
            IncludeSourceInOutput=bool(self.ag_options['include_source_in_output']), maxRunTime=self.ag_options['max_run_time'],
            interpreter=interpreter, maxOutputLines=self.ag_options['max_output_lines'], AutoGraderVersion=AUTO_GRADER_APP_VERSION)
            

    def EnableStartButton(self):
        if self.Ready2Start == Application.SOURCE_DIRECTORY_SET + Application.TEST_DATA_FILES_SET + Application.LANGUAGE_SELECTED:
            self.ButtonStart.config(state=NORMAL)
        else:
            self.ButtonStart.config(state=DISABLED)

    def ButtonSourceDirectoryClick(self):
        SourceDirectory = tkFileDialog.askdirectory(mustexist=True, initialdir=self.EntrySourceDirectory.get())
        if SourceDirectory == "":    #user pressed 'Cancel'
            return

        #get the source directory
        self.EntrySourceDirectory.delete(0, END)
        self.EntrySourceDirectory.insert(0, SourceDirectory )
        self.Ready2Start = self.Ready2Start | Application.SOURCE_DIRECTORY_SET
        self.EntrySourceDirectory.config(bg=Application.WIDGET_SET_BACK_COLOR)

        #use the name of the source directory as the name of the output file
        default_output_file = SourceDirectory + '.html'
        
        self.EntryOutputFile.delete(0, END)
        self.EntryOutputFile.insert(0, default_output_file)
        
        self.EnableStartButton()
        

    def TestFilesSet(self, val):
        """sets the background and variables associated with the Input Test Data
        Files listbox.  Defaults to False."""
        if (val == True):   #Test files have been specified
            self.Ready2Start |= Application.TEST_DATA_FILES_SET
            self.ListBoxInputFiles.config(bg=Application.WIDGET_SET_BACK_COLOR)
        else:       #Test files have not yet been specified
            if self.Ready2Start & Application.TEST_DATA_FILES_SET != 0:
                self.Ready2Start -= Application.TEST_DATA_FILES_SET 
            self.ListBoxInputFiles.config(bg=Application.WIDGET_PRE_SET_BACK_COLOR)
        self.EnableStartButton()
            

    def ButtonAddInputDataFilesClick(self):
        #if the listbox has never been accessed, remove the initial message
        if self.bListBoxInputFilesClean == True:
            self.ListBoxInputFiles.delete(0, END)
            self.bListBoxInputFilesClean = False

        fpath = tkFileDialog.askopenfilenames(initialdir=self.ag_options['test_data_directory'])
        if fpath == "":    #user pressed 'Cancel'
            return
        
        #store the path to the data files
        self.ag_options['test_data_directory'] = os.path.split(fpath[0])[0]

        print (self.ag_options['test_data_directory'])
        print ("Test Data Files:")        
        for path in fpath:
            if path not in self.TestDataFiles:
                self.TestDataFiles.append(path)
                _, filename =  os.path.split(path)
                print (filename)
                self.ListBoxInputFiles.insert(END, filename)
        self.TestFilesSet(True)


    def ButtonRemoveInputDataFilesClick(self):
        #if the listbox has never been accessed, remove the initial message
        if self.bListBoxInputFilesClean == True:
            self.ListBoxInputFiles.delete(0, END)
            self.bListBoxInputFilesClean = False

        #if no item is selected, do nothing
        if self.ListBoxInputFiles.curselection() == ():
            return
        
        #first, delete the corresponding item in the TestDataFiles list
        self.TestDataFiles.pop(self.ListBoxInputFiles.curselection()[0])
        
        itemToDelete = self.ListBoxInputFiles.get(self.ListBoxInputFiles.curselection())
        print ('deleting ', itemToDelete)
        
        #now, delete the selected list box item
        self.ListBoxInputFiles.delete(ANCHOR)

        #if there are no more items in the list, change the color and clear the ready flag
        if len(self.TestDataFiles) == 0:
            self.TestFilesSet(False)
            

    def NoInputCheckBoxClick(self):
        if self.NoInputCheckBox.get() == 1:
            self.TestFilesSet(True)  #if the no input check box is checked, we automatically check off setting the input files
            self.ButtonAddInputDataFiles.config(state=DISABLED)
            self.ButtonRemoveInputDataFiles.config(state=DISABLED)
        else:
            self.ButtonAddInputDataFiles.config(state=NORMAL)           
            self.ButtonRemoveInputDataFiles.config(state=NORMAL)
            if self.ListBoxInputFiles.size() == 0:
                self.TestFilesSet(False)

        if self.bListBoxInputFilesClean == True:
            self.ListBoxInputFiles.delete(0, END)
            self.bListBoxInputFilesClean = False

    def SpecifyFilenameCheckBoxClick(self):
        if self.specifyFilename.get() == 1:
            self.EntrySourceFile.config(state=NORMAL)
            self.EntrySourceFileTextVar.set(self.defaultSourceFile)
        else:
            self.defaultSourceFile = self.EntrySourceFileTextVar.get()
            self.EntrySourceFileTextVar.set("Test all files")
            self.EntrySourceFile.config(state=DISABLED)

    def optionMenuLanguageChanged(self, choice):
        self.LangChoice = choice
            
        if choice == 'C++':
            self.MainLabel.configure(text="  C++ Auto-Grader " + AUTO_GRADER_APP_VERSION + "  ", fg=self.CPP_TEXT_COLOR)
            self.nb.hide(self.NoLangOptionsTab)
            self.nb.hide(self.PythonOptionsTab)
            self.nb.add(self.CppOptionsTab)
            self.Ready2Start = self.Ready2Start | Application.LANGUAGE_SELECTED
            self.OptionMenuLanguage.config(bg=Application.WIDGET_SET_BACK_COLOR)
        elif choice == 'Python':
            self.MainLabel.configure(text="  Python Auto-Grader " + AUTO_GRADER_APP_VERSION + "  ", fg=self.PYTHON_TEXT_COLOR)
            self.nb.hide(self.NoLangOptionsTab)
            self.nb.add(self.PythonOptionsTab)
            self.nb.hide(self.CppOptionsTab)
            self.Ready2Start = self.Ready2Start | Application.LANGUAGE_SELECTED
            self.OptionMenuLanguage.config(bg=Application.WIDGET_SET_BACK_COLOR)
        else:
            self.MainLabel.configure(text="  C++ / Python Auto-Grader " + AUTO_GRADER_APP_VERSION + "  ", fg='#000000')
            self.nb.add(self.NoLangOptionsTab)
            self.nb.hide(self.PythonOptionsTab)
            self.nb.hide(self.CppOptionsTab)
            self.EntrySourceFileTextVar.set("Test all files")
            self.ButtonStart.config(state=DISABLED)
            
        self.EnableStartButton()
    
    def BuildUI(self):

        #add Spelman Logo
        self.spelmanLogoPhoto=PhotoImage(data=SpelmanLogo.SPELMAN_LOGO, height=50)
        w = Canvas(self.MainWindow, height=55, width=150)
        w.grid(row=0, column=1, columnspan=2, padx=30, pady=10)
        w.create_image(10, 10, image=self.spelmanLogoPhoto, anchor='nw')
        
        self.MainWindow.title("Python Auto-Grader " + AUTO_GRADER_APP_VERSION)
        self.MainLabel=Label(self.MainWindow, text="  C++ / Python Auto-Grader " + AUTO_GRADER_APP_VERSION + "  ", font=("Helvetica", 20,"bold"))
        self.MainLabel.grid(row=0, column=2, columnspan=7, pady=5)

        #create the main notebook
        self.nb = ttk.Notebook(self.MainWindow, name='nb') # create Notebook in "master"
        self.nb.grid(row=2, column=2, columnspan=7, rowspan=1, padx=0, pady=0) # fill "master" but pad sides

        #create the main notebook tab
        self.MainTab = Frame(self.nb, name='mainTab')
        self.nb.add(self.MainTab, text='Main')

        
        Label(self.MainTab, text="Select a Language:", font=("Helvetica", 14, "bold"), fg='#334353').grid(row=0, column=3, columnspan=3, pady=5)
        self.OptionMenuLanguageVar = StringVar()
        self.OptionMenuLanguageVar.set(" - - - - - ")
        self.OptionMenuLanguage = OptionMenu(self.MainTab, self.OptionMenuLanguageVar, "C++", "Python", command=self.optionMenuLanguageChanged)
        self.OptionMenuLanguage.config(font=("Helvetica", 18,"bold", "italic"), fg='#334353', bg=Application.WIDGET_PRE_SET_BACK_COLOR, width=10)
        self.OptionMenuLanguage.grid(row=0, column=6, columnspan=1, pady=10, sticky=W)

        self.ButtonStart = Button(self.MainTab, text="Start", width=25, compound="center", command=self.ButtonStartClick, state=DISABLED)
        self.ButtonStart.grid(row=9, column=5, columnspan=5, pady=2)

        self.ButtonRemoveInputDataFiles = Button(self.MainTab, text="-", font=("Helvetica", 18,"bold"), compound="center", width=1, command=self.ButtonRemoveInputDataFilesClick)
        self.ButtonRemoveInputDataFiles.grid(row=1, column=4, padx=0, ipadx=0, sticky=E)

        self.ButtonAddInputDataFiles = Button(self.MainTab, text="+", font=("Helvetica", 18,"bold"), compound="center", width=1, command=self.ButtonAddInputDataFilesClick)
        self.ButtonAddInputDataFiles.grid(row=1, column=5, sticky=W, padx=0, ipadx=0)

        self.ListBoxInputFiles = Listbox(self.MainTab, bg=Application.WIDGET_PRE_SET_BACK_COLOR, width=30)
        self.ListBoxInputFiles.grid(row=2, column=2, padx=5, pady=5, columnspan=4, rowspan=6, ipadx=0, ipady=0)
        self.ListBoxInputFiles.insert(END, 'Test Data Files [None]')
        self.bListBoxInputFilesClean = True #flag that tells us we need to clear the initial list box message
        self.TestFilesSet(False)

        self.ButtonSourceDirectory = Button(self.MainTab, text="Top Level Source Dir", compound="center", width=15, command=self.ButtonSourceDirectoryClick)
        self.ButtonSourceDirectory.grid(row=2, column=6, sticky=W, padx=0, ipady=0)

        self.EntrySourceDirectory = Entry(self.MainTab, width=40)
        self.EntrySourceDirectory.grid(row=3, column=6, ipady=0, padx=5, pady=0, columnspan=5, sticky=W)
        self.EntrySourceDirectory.delete(0, END)
        self.EntrySourceDirectory.insert(0, self.ag_options['top_level_directory'] )
        if self.ag_options['top_level_directory'] == '':
            self.EntrySourceDirectory.config(bg=Application.WIDGET_PRE_SET_BACK_COLOR)
        else:
            self.EntrySourceDirectory.config(bg=Application.WIDGET_SET_BACK_COLOR)
            self.Ready2Start |= Application.SOURCE_DIRECTORY_SET


        Label(self.MainTab, text="Output File:").grid(row=4, column=6, columnspan=2, padx=0, pady=0, sticky=W)

        self.EntryOutputFile = Entry(self.MainTab, width=40)
        self.EntryOutputFile.grid(row=5, column=6, ipady=0, padx=5, columnspan=5, sticky=W)
        self.EntryOutputFile.delete(0, END)
        self.EntryOutputFile.insert(0, self.ag_options['top_level_directory'] + '.html')

        self.IncludeSource = IntVar()
        Checkbutton(self.MainTab, text="Include source in output", variable=self.IncludeSource, justify=LEFT).grid(row=6, column=6, columnspan=1, padx=0, pady=0, ipady=0, sticky=W)
        self.IncludeSource.set(self.ag_options['include_source_in_output'])
        
        self.NoInputCheckBox = IntVar()
        Checkbutton(self.MainTab, text="No Test Data", variable=self.NoInputCheckBox, command=self.NoInputCheckBoxClick).grid(row=1, column=2)
        self.NoInputCheckBox.set(0)

        
        Label(self.MainTab, text="Max Run Time (secs)", font=("Helvetica", 14)).grid(row=9, column=2, columnspan=2, padx=5, sticky=E)
        self.MaxRunSpinBox = Spinbox(self.MainTab, from_=0, to=600, width=10)
        self.MaxRunSpinBox.grid(row=9, column=4, columnspan=2)
        self.MaxRunSpinBox.delete(0, END)
        self.MaxRunSpinBox.insert(0, str(self.ag_options['max_run_time']))
 
            
        Label(self.MainTab, text="Limit outputs to\nthis many lines:", font=("Helvetica", 14), justify=LEFT).grid(row=10, column=2, columnspan=2, padx=5, sticky=E)
        self.MaxOutputLinesSpinBox = Spinbox(self.MainTab, from_=1, to=600, width=10)
        self.MaxOutputLinesSpinBox.grid(row=10, column=4, columnspan=2)
        self.MaxOutputLinesSpinBox.delete(0, END)
        self.MaxOutputLinesSpinBox.insert(0, str(self.ag_options['max_output_lines']))

        #Create the Python options notebook tab
        self.PythonOptionsTab = Frame(self.nb, bg=self.PYTHON_WND_COLOR)
        self.nb.add(self.PythonOptionsTab, text='Options')

        self.pyAutoUnzip = IntVar()
        Checkbutton(self.PythonOptionsTab, text="Automatically uncompress Zip files", variable=self.pyAutoUnzip, command=lambda : 0, bg=self.PYTHON_WND_COLOR, fg=self.PYTHON_TEXT_COLOR, justify=LEFT).grid(row=5, column=1, columnspan=1, padx=5, sticky=W)
        self.pyAutoUnzip.set(self.ag_options['py_auto_unzip'])
        
        Label(self.PythonOptionsTab, text='Files with a .zip extension will be automatically uncompressed to a directory with the same name as the zip file.\n', font=("Helvetica", 12, "italic"), bg=self.PYTHON_WND_COLOR, fg=self.PYTHON_TEXT_COLOR, justify=LEFT).grid(row=6, column=1, columnspan=3, padx=5, sticky=W)
        
        Label(self.PythonOptionsTab, text="When a student's submission consists of multiple .py files, you must specify the top level module.\nNote: Students must be told what to name their top-level module.  Executes (default interpreter config)\nwith 'python <TopModule.py>'\n", font=("Helvetica", 12, "italic"), bg=self.PYTHON_WND_COLOR, fg=self.PYTHON_TEXT_COLOR, justify=LEFT).grid(row=14, column=1, columnspan=3, padx=5, sticky=W)

        Label(self.PythonOptionsTab, text='Name of top-level Python module:', bg=self.PYTHON_WND_COLOR, justify=LEFT).grid(row=13, column=1, columnspan=1, padx=5, sticky=W)
        
        self.pyTopLevelModule = StringVar()
        self.EntryPythonTopModule = Entry(self.PythonOptionsTab, width=40, textvariable=self.pyTopLevelModule, justify=LEFT)
        self.pyTopLevelModule.set(self.ag_options['py_top_level_module'])
        self.EntryPythonTopModule.grid(row=13, column=2, ipady=0, ipadx=0, padx=5, columnspan=2, sticky=W)

        Label(self.PythonOptionsTab, text='Python command-line interpreter:', bg=self.PYTHON_WND_COLOR).grid(row=16, column=1, columnspan=1, padx=5, sticky=W)
        self.pyInterpreter = StringVar()
        self.EntryPythonInterpreter = Entry(self.PythonOptionsTab, width=40, textvariable=self.pyInterpreter, justify=LEFT)
        self.pyInterpreter.set(self.ag_options['py_interpreter'])
        self.EntryPythonInterpreter.grid(row=16, column=2, ipady=0, ipadx=0, padx=5, columnspan=2, sticky=W)
        Label(self.PythonOptionsTab, text='Specify the python interpreter and command line options here. Example: "/usr/bin/python -v -3"\n', font=("Helvetica", 12, "italic"), bg=self.PYTHON_WND_COLOR, fg=self.PYTHON_TEXT_COLOR, justify=LEFT).grid(row=17, column=1, columnspan=3, padx=5, sticky=W)

        #Create the C++ options notebook tab
        self.CppOptionsTab = Frame(self.nb, bg=self.CPP_WND_COLOR)
        self.nb.add(self.CppOptionsTab, text='Options')

        self.cppAutoUnzip = IntVar()
        Checkbutton(self.CppOptionsTab, text="Automatically uncompress Zip files", variable=self.cppAutoUnzip, command=lambda : 0, bg=self.CPP_WND_COLOR, fg=self.CPP_TEXT_COLOR, justify=LEFT).grid(row=5, column=1, columnspan=1, padx=5, sticky=W)
        self.cppAutoUnzip.set(self.ag_options['cpp_auto_unzip'] )
        
        Label(self.CppOptionsTab, text='Files with a .zip extension will be automatically uncompressed to a directory with the same name as the zip file.\n', font=("Helvetica", 12, "italic"), bg=self.CPP_WND_COLOR, fg=self.CPP_TEXT_COLOR, justify=LEFT).grid(row=6, column=1, columnspan=3, padx=5, sticky=W)

        Label(self.CppOptionsTab, text='C++ command-line compiler:', bg=self.CPP_WND_COLOR).grid(row=16, column=1, columnspan=1, padx=5, sticky=W)
        self.cppInterpreter = StringVar()
        self.EntryCppInterpreter = Entry(self.CppOptionsTab, width=40, textvariable=self.cppInterpreter, justify=LEFT)
        self.cppInterpreter.set(self.ag_options['cpp_compiler'])
        self.EntryCppInterpreter.grid(row=16, column=2, ipady=0, ipadx=0, padx=5, columnspan=2, sticky=W)
        Label(self.CppOptionsTab, text='Specify the C++ compiler with optioal command line options here. Example: "/usr/bin/g++ -lm"\n', font=("Helvetica", 12, "italic"), bg=self.CPP_WND_COLOR, fg=self.CPP_TEXT_COLOR, justify=LEFT).grid(row=17, column=1, columnspan=3, padx=5, sticky=W)
        

        #Create the 'no language selected' options notebook tab
        self.NoLangOptionsTab = Frame(self.nb)
        self.nb.add(self.NoLangOptionsTab, text='Options')
        Label(self.NoLangOptionsTab, text='Please select a language from the\n"Main" tab to eneable "Options" setting.', font=("Helvetica", 20), fg='#ff0000', height=10).pack(fill=BOTH)

        #set default options frame to 'no language selected'
        self.nb.hide(self.PythonOptionsTab)
        self.nb.hide(self.CppOptionsTab)
        self.nb.add(self.NoLangOptionsTab)
    
        #Create the 'About' notebook tab
        self.AboutTab = Frame(self.nb, bg=self.ABOUT_WND_COLOR)
        self.nb.add(self.AboutTab, text='About')

        #create the scrollable 'About' text box
        self.scrollTextAboutTab = ScrolledText.ScrolledText(
        master = self.AboutTab,
        wrap   = 'word',  # wrap text at full words only
        height = 21,
        bg=self.ABOUT_WND_COLOR,
        fg=self.ABOUT_TEXT_COLOR,
        font=("Helvetica", 14)
        )

        aboutFn = open('src/AG_about.dat')
        aboutText = aboutFn.read()
        aboutFn.close()
        
        self.scrollTextAboutTab.insert('insert', 'Spelman AutoGrader ' + AUTO_GRADER_APP_VERSION)
        self.scrollTextAboutTab.insert('insert', aboutText)
        self.scrollTextAboutTab.config(state=DISABLED)
        
        self.scrollTextAboutTab.pack(expand=True) #fill='both', expand=False)


    def load_user_options(self, fileName):
        '''function that creates a default options dictionary then overrides entries in the dictionary
        with corresponding entries in the options file on disk.'''
        #set defaults
    
        self.json_opts = {}         #this will hold the options currently on disk        
        self.ag_options = {
            'version': AUTO_GRADER_APP_VERSION,
            'max_run_time': self.DEFAULT_MAX_RUN_TIME,
            'max_output_lines': self.DEFAULT_MAX_OUTPUT_LINES,
            'include_source_in_output': 1,
            'top_level_directory': '',
            'test_data_directory': '',
            'cpp_auto_unzip': 1,
            'cpp_compiler': 'g++',
            'py_recursie_process': 1,
            'py_auto_unzip': 1,
            'py_top_level_module': 'main.py',
            'py_interpreter': 'python',
        }
            
        #load options from file which may overwrite the defaults
        try:
            #load the json string from the options file
            fn = open(fileName)
            ag_options_json = fn.read()
            fn.close()

            #convert the json string to a dictionary
            self.json_opts = json.loads(ag_options_json)

            #update the ag_options dictionary with matching entries in the opts dictionary
            for key in self.json_opts:
                if key in self.ag_options:
                    self.ag_options[key] = self.json_opts[key]
        except:
            print ("Error accessing options file " + self.OPTIONS_FILE)


    def save_user_options(self, fileName):
        '''function that saves the user options to disk without deleting file keys no longer
        used or used by a different version of the program.'''
        #update the json_opts dictionary with matching options from the ag_options dictionary.
        #The json_opts dictioary represents the options currently on disk.
        for key in self.ag_options:
            self.json_opts[key] = self.ag_options[key]
                
        #write the options file here
        fn = open(fileName, 'w')
        fn.write(json.dumps(self.json_opts))
        fn.close()

    
    #WM_DELETE_WINDOW handler
    def on_closing(self):
        #save user options ( moved to ButtonStartClick() )
        #self.save_user_options(self.OPTIONS_FILE)
        self.MainWindow.destroy()
        

    def run(self):

        self.load_user_options(self.OPTIONS_FILE)
        self.MainWindow = Tk()
        self.MainWindow.configure()
        #self.MainWindow.configure(bg='#334353')
        self.MainWindow.resizable(0,0)  #prevent window resizing
        self.BuildUI()

        #assign the WM_DELETE_WINDOW event handler
        self.MainWindow.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.MainWindow.mainloop()
    

if __name__ == "__main__":
    app = Application()
    app.run()



