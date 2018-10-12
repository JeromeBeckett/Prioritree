# Import necessary modules
from tkinter import *
from tkinter import messagebox, simpledialog
from tkinter.ttk import Combobox, Separator, Progressbar
from datetime import date, timedelta
import sqlite3 as sql
import re
import os

# Determine if account is new or not
def assessAccount(event=None,userSwitch=None):
    global username
    if userSwitch == None:
        username = userInput.get()
    else:
        username = userSwitch
    global conn
    conn = sql.connect('userdata/'+username+'.db')
    global c
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='todos'")
    result=c.fetchall()
    global newAccount
    global todos
    global categories

    # If number of tables is zero, create tables in database
    if (len(result) == 0):
        newAccount = "yes"
        if messagebox.askokcancel("New account?","Create new account with username "+username+"?"):
            c.execute("CREATE TABLE todos (key FLOAT, todo VARCHAR, type INTEGER, parent FLOAT, children INTEGER, otherchildren INTEGER, date DATE, category VARCHAR, completion BOOLEAN, completionDate DATE, disabled INTEGER)")
            c.execute("CREATE TABLE categories (name VARCHAR)")
            c.execute("CREATE TABLE longterm (key FLOAT, todo VARCHAR, type INTEGER, parent FLOAT, children INTEGER, progress INTEGER, completion BOOLEAN, completionDate DATE, disabled INTEGER)")
            c.execute("CREATE TABLE contacts (key INTEGER PRIMARY KEY,name VARCHAR, address VARCHAR, email VARCHAR, phone VARCHAR)")
            c.execute("CREATE TABLE events (key INTEGER PRIMARY KEY, title VARCHAR, location VARCHAR, datetime DATETIME, description VARCHAR)")
            c.execute("CREATE TABLE reminders (key INTEGER PRIMARY KEY, title VARCHAR, description VARCHAR, active BOOLEAN)")
            c.execute("CREATE TABLE urls (key INTEGER PRIMARY KEY, url VARCHAR)")

            todos = list()
            c.execute("SELECT * FROM categories ORDER BY name ASC")
            categories = list(c.fetchall())
            if len(categories) == 0:
                categories.append("")
            categories = tuple(categories)
            if userSwitch != None:
                app.destroy()
            construct()
        else:
            conn.close()
            os.remove('userdata/'+username+'.db')
            if userSwitch != None:
                conn = sql.connect('userdata/'+oldUsername+'.db')
                c = conn.cursor()
                newAccount = "no"

    # Otherwise fetch data
    else:
        if userSwitch != None:
            app.destroy()
        newAccount = "no"
        c.execute("SELECT * FROM todos ORDER BY key ASC")
        todos = c.fetchall()
        todos = list(todos)
        c.execute("SELECT * FROM categories ORDER BY name ASC")
        categories = list(c.fetchall())
        if len(categories) == 0:
            categories.append("")
        categories = tuple(categories)
        construct()


# Introductory help if new user
def getStarted(a):
    sequential()
    if a == 1:
    	messagebox.showinfo("Help basics","Enter something in the box below and press enter to create a todo.\n\nBefore confirming the todo, you can click the calendar, input a date and press enter to set a specific date for the todo.\nYou can also choose a category with the dropdown box.\n\nTo delete a todo click the minus box.\n\nCreate sublists with the sublist tool.\n\nMake todos with conditional lists with the question button.\n\nUse the select tool to turn multiple tasks into subtasks, questions, change their categories or dates, or delete them.\n\nUse the help button for more details or to learn about more features.")

def stringEncode(string):
    quoteEscaper = string.split("'")
    for i in range(1,len(quoteEscaper)):
        quoteEscaper[i] = "&quot;"+quoteEscaper[i]
    encodedString = "".join(quoteEscaper)
    return [string,encodedString]

def stringDecode(string):
    quoteEscaper = string.split("&quot;")
    for i in range(1,len(quoteEscaper)):
        quoteEscaper[i] = "'"+quoteEscaper[i]
    decodedString = "".join(quoteEscaper)
    return decodedString

# Adding new todo to database
def processTodo(event=None):
    global inputBar
    global inputText
    global todoContent
    global todoFrames
    global todoCompletions
    global c
    global conn
    global todos
    global sqlDate
    global categoryText
    global categoryList
    global categoryList2

    # Fetch todo, add category to dropdown list, insert into database
    newTodo = inputBar.get()
    if "'" in newTodo:
        newTodo = stringEncode(newTodo)[0]
        sqlTodo = stringEncode(newTodo)[1]
    else:
        sqlTodo = newTodo
    if sqlDate == "" and (currentView=="daily" or currentView=="weekly"):
        sqlDate = str(date.today() + timedelta(days=dayToBeViewed))
    inputText.set("")
    length = len(todoCompletions)
    todoCompletions.append(IntVar())
    categoryText = categoryList2.get()
    if categoryText not in categoryList['values'] and categoryText != "":
            categoryList['values'] += tuple([categoryText])
            categoryList2['values'] += tuple([categoryText])
            c.execute("INSERT INTO categories (name) VALUES ('"+categoryText+"')")
    c.execute("INSERT INTO todos (key,todo,type,children,otherchildren,date,category) VALUES ("+str(len(todos))+".0,'"+sqlTodo+"',1,0,0,'"+sqlDate+"','"+categoryText+"')")
    conn.commit()

    # Build widget for new todo without needing update()
    if currentView != "category":
        c.execute("SELECT * FROM todos ORDER BY key ASC")
        todos = c.fetchall()
        todos = list(todos)
        todoFrame = Frame(todoContent)
        todoFrames.append(todoFrame)
        todoFrame.pack(side=TOP,anchor=W)
        todoWidget = Checkbutton(todoFrame, text=newTodo, font=("Segoe UI",14), borderwidth=0, pady=0, variable=todoCompletions[length], command=lambda i=length:checked(i))
        todoWidgets.append(todoWidget)
        todoWidget.grid(row=0,column=0)
        if categoryText != "":
            todoCategory = Label(todoFrame, text=categoryText, bg="yellow", font=("Segoe UI",14))
            todoCategories.append(todoCategory)
            todoCategory.grid(row=0,column=1,sticky=W,padx=(15,0))
        else:
            emptyLabel = Label(todoFrame)
            todoCategories.append(emptyLabel)
            emptyLabel.grid(row=0,column=1)

    # In category view call update() rather than cycling through the category frames
    else:
        update()


# Write to database when todo ticked
def checked(index):
    global todos
    global todoCompletions
    global todoWidgets
    global todoProgress
    global c
    global conn
    todoType = todos[index][2]
    todoParent = todos[index][3]
    todoChildren = todos[index][4]

    # If being ticked
    if todoCompletions[index].get() == 1:
        if currentView == "longterm":

            # If main longterm todo, complete task permanently, else disable previous subtasks
            if todos[index][2] == 1:
                if messagebox.askyesno("Complete task?","Complete this task permanently?"):
                    c.execute("UPDATE longterm SET progress=100, completion=1, completionDate='"+str(date.today())+"',disabled=1 WHERE key="+str(todos[index][0]))
                    todoWidgets[index].config(state=DISABLED)
                    todoProgress[index].config(value=100)
                    for i in range(index+1,index+1+todoChildren):
                        c.execute("UPDATE longterm SET completion=1, disabled=1 WHERE key="+str(todos[i][0]))
                        todoWidgets[i].config(state=DISABLED)
                else:
                    todoWidgets[index].deselect()
            else:
                c.execute("UPDATE longterm SET completion=1 WHERE key="+str(todos[index][0]))
                for i in range(len(todos)):
                    if todos[i][0] == todoParent:
                        parentIndex = i
                        parentChildren = todos[i][4]
                        todoProgress[i].config(value=todos[index][5])
                for i in range(parentIndex+1,parentIndex+parentChildren+1):
                    if i < parentIndex+index:
                        c.execute("UPDATE longterm SET completion=1, disabled=1 WHERE key="+str(todos[i][0]))
                        todoWidgets[i].config(state=DISABLED)
                        todoWidgets[i].select()

        # If normal todo type (not longterm) save completion and complete subtasks
        elif todoType == 1:
            c.execute("UPDATE todos SET completion=1, completionDate='"+str(date.today())+"' WHERE key="+str(todos[index][0]))
            if todoChildren>0:
                for i in range(index+1,index+1+todoChildren):
                    if todos[i][8] == 0:
                        todoWidgets[i].select()
                        c.execute("UPDATE todos SET completion=1, completionDate='"+str(date.today())+"' WHERE key="+str(todos[i][0]))

        # If subtask save completion. Disable other list if question subtask.
        elif todoType == 2:
            c.execute("UPDATE todos SET completion=1, completionDate='"+str(date.today())+"' WHERE key="+str(todos[index][0]))
            for i in range(len(todos)):
                if todos[i][0] == todoParent and todos[i][2] == 3:
                    parentChildren = todos[i][4]
                    parentOtherChildren = todos[i][5]
                    print(todos)
                    if index <= i+parentChildren:
                        for g in range(i+parentChildren+1,i+parentOtherChildren+1):
                            c.execute("UPDATE todos SET disabled=1 WHERE key="+str(todos[g][0]))
                            todoWidgets[g].config(state=DISABLED)
                    else:
                        for g in range(i+1,i+parentChildren+1):
                            c.execute("UPDATE todos SET disabled=1 WHERE key="+str(todos[g][0]))
                            todoWidgets[g].config(state=DISABLED)
    
    # If being unticked
    else:
    	# If longterm save incompletion and enable previous subtask
        if currentView == "longterm":
            c.execute("UPDATE longterm SET completion=0 WHERE key="+str(todos[index][0]))
            todoWidgets[index].config(fg="black")
            for i in range(len(todos)):
                if todos[i][0] == todoParent:
                    parentIndex = i
                    todoProgress[i].config(value=todos[index-1][5])
            todoWidgets[index-1].config(state=NORMAL)
            c.execute("UPDATE longterm SET disabled=0 WHERE key="+str(todos[index-1][0]))
        else:
            c.execute("UPDATE todos SET completion=0, completionDate='' WHERE key="+str(todos[index][0]))
            if todos[index][2] == 2:
                for i in range(len(todos)):
                    if todos[i][0] == todoParent and todos[i][2] == 3:
                        parentChildren = todos[i][4]
                        parentOtherChildren = todos[i][5]
                        listCompleted = 0
                        for g in range(i+1,i+parentChildren+parentOtherChildren+1):
                            if todos[g][8] == 1:
                                listCompleted += 1
                        if listCompleted == 1:
                            print("Hi")
                            if index <= i+parentChildren:
                                print("test1")
                                for g in range(i+parentChildren+1,i+parentOtherChildren+1):
                                    c.execute("UPDATE todos SET disabled=0 WHERE key="+str(todos[g][0]))
                                    todoWidgets[g].config(state=NORMAL)
                            else:
                                print("test2")
                                for g in range(i+1,i+parentChildren+1):
                                    c.execute("UPDATE todos SET disabled=0 WHERE key="+str(todos[g][0]))
                                    todoWidgets[g].config(state=NORMAL)
    conn.commit()

    # Update todos
    if currentView == "longterm":
        c.execute("SELECT * FROM longterm")
    else:
        c.execute("SELECT * FROM todos")
    todos = c.fetchall()
    print(todos)
                    
def nothing():
    a = 1


# When a reminder is made active or inactive delete notification contents and rebuild it.
def updateNotifications():
    global notification
    global notificationLabel
    global reminders
    global toolbars
    c.execute("SELECT * FROM reminders")
    reminders = c.fetchall()
    notifications = ""
    for i in reminders:
        if i[3] == 1:
            if notifications == "":
                main.pack_forget()
                notificationLabel.pack(side=TOP, fill=X)
                main.pack(side=TOP,anchor=W,fill=Y,expand=True)
                notifications = i[1]
            else:
                notifications += "   -   "+i[1]
    notification.set(notifications)
    if notifications == "":
        notificationLabel.pack_forget()


# Rebuilds todo content onscreen; could be because of view change, todo type edits, deletions, subtasks etc.
def update(calledBy=None,index=None,column=None):
    cancel()
    global todos
    global todoCompletions
    global todoWidgets
    global todoProgress
    global todoCategories
    global todoFrames
    global categoryFrames
    global questionFrames
    global yesLabels
    global noLabels
    global questions
    global dayToBeViewed
    global weekToBeViewed
    global timePeriodText
    global categoryText

    # Destroy all elements from last build of update()
    for i in range(len(todoWidgets)):
        todoWidgets[i].destroy()
    for i in range(len(todoFrames)):
        todoFrames[i].destroy()
    for i in range(len(todoCategories)):
        todoCategories[i].destroy()
    for i in range(len(categoryFrames)):
        categoryFrames[i].destroy()
    for i in range(len(todoProgress)):
        todoProgress[i].destroy()
    if questions > -1:
        for frame in questionFrames:
            frame.destroy()

    # Redefine important variables
    todoCompletions = list()
    todoWidgets = list()
    todoProgress = list()
    todoCategories = list()
    todoFrames = list()
    questionFrames = list()
    categoryFrames = list()
    yesLabels = list()
    noLabels = list()
    isItemQuestion = 0
    questionSubtasks = 0
    questionYes = 0
    questionNo = 0
    questions = -1
    i = 0

    # Gather correct todo data depending on view
    if currentView == "sequential":
        c.execute("SELECT * FROM todos ORDER BY key ASC")
    elif currentView == "daily":
        today = str(date.today() + timedelta(days=dayToBeViewed))
        todayReorder = today.split("-")[2]+"/"+today.split("-")[1]
        timePeriodText.set(todayReorder)
        c.execute("SELECT * FROM todos WHERE date='"+today+"' ORDER BY key ASC")
    elif currentView == "weekly":
        weekStart = date.today()+timedelta(days=0-(date.today().weekday()),weeks=weekToBeViewed)
        weekEnd = weekStart+timedelta(days=7)
        weekStartReorder = str(weekStart).split("-")[2]+"/"+str(weekStart).split("-")[1]
        weekEndReorder = str(weekEnd).split("-")[2]+"/"+str(weekEnd).split("-")[1]
        timePeriodText.set(str(weekStartReorder)+" to "+str(weekEndReorder))
        c.execute("SELECT * FROM todos WHERE date>='"+str(weekStart)+"' and date<'"+str(weekEnd)+"' ORDER BY key ASC")
    elif currentView == "category":
        previousCategory = 0
        c.execute("SELECT * FROM todos ORDER BY CASE WHEN category='' THEN 2 ELSE 1 END, category ASC, key ASC, CASE WHEN date='' THEN 2 ELSE 1 END, date ASC")
    elif currentView == "longterm":
        c.execute("SELECT * FROM longterm")
    todos = c.fetchall()
    todos = list(todos)

    # Goes through each todo in database and determines how to present it
    for item in todos:

        # Decode single quotes if any
        if "&quot;" in item[1]:
            item = list(item)
            item[1] = stringDecode(item[1])

    	# Sets what to show as a category, if any
        if item[2]!=2 and currentView != "longterm":
            categoryText = item[7]
        else:
            categoryText = ""

        # If category view, build frame for category to group todos in
        if currentView == "category" and previousCategory != categoryText and item[2]!=2:
            previousCategory = categoryText
            categoryFrame = LabelFrame(todoContent, text=categoryText)
            categoryFrames.append(categoryFrame)
            categoryFrame.pack(side=TOP,anchor=W)

        # Sets amount of indentation and readies question data structures if necessary
        if item[2] == 2:
            todoIndent = 50
        elif item[2] == 3:
            isItemQuestion = 1
            questions += 1
            questionYes = item[4]
            questionNo = item[5]
            questionSubtasks = questionYes + questionNo
            if currentView != "category":
                questionFrame = Frame(todoContent, padx=20)
            else:
                questionFrame = Frame(categoryFrame, padx=20)
            questionFrames.append(questionFrame)
            yesRow = 1
            noRow = 1
            todoIndent = 0
        else:
            todoIndent = 0

        # If todo is not a question subtask (IE most cases) build todo presentation
        if questionSubtasks <= 0 or isItemQuestion == 1:
            todoCompletions.append(IntVar())
            if currentView != "category":
                todoFrame = Frame(todoContent)
            else:
                todoFrame = Frame(categoryFrame)
            todoFrames.append(todoFrame)
            todoFrame.pack(side=TOP,anchor=W)
            todoWidget = Checkbutton(todoFrame, text=item[1]+"\t", font=("Segoe UI",14), borderwidth=0, pady=0, variable=todoCompletions[i], command=lambda i=i:checked(i))
            todoWidgets.append(todoWidget)
            todoWidget.grid(row=0,column=0,sticky=W,padx=(todoIndent,0))

            # Builds progress bar, category labels and/or ticks or disables todo widget
            if currentView == "longterm":
                if item[2]==1:
                    progress = Progressbar(todoFrame, orient=HORIZONTAL, length=300, mode='determinate', value=0)
                    todoProgress.append(progress)
                    progress.grid(row=0,column=1)
                else:
                    todoProgress.append(Label(root))
                if item[6] == 1:
                    todoWidget.select()
                if item[8] == 1:
                    todoWidget.config(state=DISABLED)
            elif categoryText != "" and currentView != "category":
                todoCategory = Label(todoFrame, text=categoryText, bg="yellow", font=("Segoe UI",14))
                todoCategories.append(todoCategory)
                todoCategory.grid(row=0,column=1,sticky=W,padx=(15,0))
                if item[8] == 1:
                    todoWidget.select()
            else:
                emptyLabel = Label(todoFrame)
                todoCategories.append(emptyLabel)
                emptyLabel.grid(row=0,column=1)
                if item[8] == 1:
                    todoWidget.select()

            # Format question presentation ready for subtasks (if any)
            if isItemQuestion == 1:
                questionFrames[questions].pack(side=TOP,anchor=W)
                label = Label(questionFrames[questions],text="yes")
                yesLabels.append(label)
                label.grid(column=0,row=0,padx=10)
                label = Label(questionFrames[questions],text="no")
                noLabels.append(label)
                label.grid(column=1,row=0)
                isItemQuestion = 0

        # If question subtask, determine if "yes" or "no" and build widget
        else:
            todoCompletions.append(IntVar())
            todoWidget = Checkbutton(questionFrames[questions], text=item[1], font=("Segoe UI",14), borderwidth=0, padx=20, variable=todoCompletions[i], command=lambda i=i:checked(i))
            todoWidgets.append(todoWidget)
            if item[10] == 1:
                todoWidget.config(state=DISABLED)
            if item[8] == 1:
                todoWidget.select()
            if questionYes > 0:
                #todoWidget.config(bg="#51bd49")
                todoWidget.grid(column=0,row=yesRow,sticky=NSEW)
                questionSubtasks -= 1
                questionYes -= 1
                yesRow += 1
            elif questionNo > 0:
                #todoWidget.config(bg="red")
                todoWidget.grid(column=1,row=noRow,sticky=NSEW)
                questionSubtasks -= 1
                questionNo -= 1
                noRow += 1
        i += 1
    sqlDate = ""
    updateNotifications()
    if calledBy == "delete":
        removeTodo()
    elif calledBy == "subtask":
        instructionText.set("Click todo to apply subtask to.")
        instructionButton.config(text="Cancel")
        instructionButton.pack(side=LEFT)
        subThisTodo(parent,1)
    elif calledBy == "questonSubtask":
        addQuestionSubtask(parent,column)


# Called when longterm todo entered and confirmed
def longtermEntered(event=None,subtask=None):
    global inputBar
    global inputText
    global longterms
    global todos
    global todoWidgets
    global todoFrames
    global todoProgress
    global todoCompletions
    global parent
    global parentKey
    global c
    global conn

    # Fetch todo
    newTodo = inputBar.get()
    if "'" in newTodo:
        newTodo = stringEncode(newTodo)[0]
        sqlTodo = stringEncode(newTodo)[1]
    else:
        sqlTodo = newTodo
    length = len(todoCompletions)
    todoCompletions.append(IntVar())

    # If main longterm todo, add to database and build
    if subtask != 1:
        c.execute("INSERT INTO longterm (key,todo,type,children,progress,completion) VALUES ("+str(len(todos))+".0,'"+sqlTodo+"',1,0,0,0)")
        conn.commit()
        c.execute("SELECT * FROM longterm")
        todos = c.fetchall()
        todoFrame = Frame(todoContent)
        todoFrames.append(todoFrame)
        todoFrame.pack(side=TOP,anchor=W)
        todoWidget = Checkbutton(todoFrame, text=newTodo, font=("Segoe UI",14), borderwidth=0, pady=0, variable=todoCompletions[length], command=lambda i=length:checked(i))
        todoWidgets.append(todoWidget)
        todoWidget.grid(row=0,column=0,sticky=W)
        progress = Progressbar(todoFrame, mode='determinate', value=0)
        todoProgress.append(progress)
        progress.grid(row=0,column=1)
        inputText.set("")

    # If longterm subtask, ask user to set progress of bar, add to database and build
    else:
        parentChildren = todos[parent][4]
        progress = simpledialog.askinteger("Set progress","At what percentage of progress\nshould this subtask be anchored at?")
        if progress != None:
            parentChildren = todos[parent][4]
            c.execute("UPDATE longterm SET children="+str(parentChildren+1)+" WHERE key="+str(parentKey)+".0")
            c.execute("INSERT INTO longterm (key,todo,type,parent,progress,completion) VALUES ("+str(parentKey)+"."+str(parentChildren+1)+",'"+sqlTodo+"',2,"+str(parentKey)+".0,"+str(progress)+",0)")
            conn.commit()
            c.execute("SELECT * FROM longterm ORDER BY key ASC")
            todos = c.fetchall()
            todoCompletions.append(IntVar())
            todoWidget = Checkbutton(todoContent, text=newTodo, font=("Segoe UI",14), borderwidth=0, pady=0, variable=todoCompletions[length], command=lambda i=length:checked(i))
            todoWidgets.append(todoWidget)
            todoWidget.pack(side=TOP,anchor=W,padx=50)
            todoProgress.append(Label(root))
            parents = -1
            for i in todos:
                if i[2] == 1 and int(i[0])*100<int(int(parentKey*100)+int(parentChildren*10)):
                    parents += 1
            inputText.set("")
                

# Cancels any running process or function; removes temporary commands, colours, variables, and text
def cancel(event=None):
    global defaultColour
    global selected
    global instructionText
    global instructionButton
    global inputButton
    global inputBar
    global dateInputText
    global dateInput
    global process
    process = None
    for i in range(len(todoWidgets)):
        todoWidgets[i].config(bg=defaultColour,command=lambda i=i:checked(i))
    instructionText.set("")
    instructionButton.pack_forget()
    if currentView != "longterm":
        inputButton.config(command=processTodo)
        inputBar.bind('<Return>', processTodo)
    dateInputText.set("")
    dateInput.place_forget()
    selected = list()


# Sets day or week to the succeeding one
def next():
    global dayToBeViewed
    global weekToBeViewed
    if currentView == "daily":
        dayToBeViewed += 1
    else:
        weekToBeViewed += 1
    update()


# Sets day or week to the preceeding one
def previous():
    global dayToBeViewed
    global weekToBeViewed
    if currentView == "daily":
        dayToBeViewed -= 1
    else:
        weekToBeViewed -= 1
    update()


# Set focus on input bar, ready for input
def addTodo():
    cancel()
    global inputBar
    global inputText
    inputBar.focus_set()
    inputText.set("Enter your todo here")
    inputBar.select_range(0, END)


# Called by initial delete subroutine. Deletes selected todo(s) from database and screen
def deleteThisTodo(delete,i=None):
    global todoWidgets
    global todoCompletions
    global todos
    global c
    global conn

    # Single todo chosen - delete from database and screen and remove links to parent or remove any children
    if delete == 'empty':
        delete = i
        todo = todos[delete]
        todoKey = todo[0]
        todoType = todo[2]
        todoChildren = todo[4]
        todoOtherChildren = todo[5]
        if currentView != "longterm":
            table = "todos"
        else:
            table = "longterm"
        if todoType == 2:
            todoParent = todo[3]
            for g in range(len(todos)):
                if todos[g][0] == todoParent:
                    parentIndex = g
                    parentChildren = todos[g][4]
                    parentOtherChildren = todos[g][5]
            if delete <= (parentIndex+parentChildren):
                c.execute("UPDATE "+table+" SET children="+str(parentChildren-1)+" WHERE key="+str(todoParent))
            else:
                c.execute("UPDATE "+table+" SET otherchildren="+str(parentOtherChildren-1)+" WHERE key="+str(todoParent))
            c.execute("DELETE FROM "+table+" WHERE key="+str(todoKey))
        else:
            c.execute("DELETE FROM "+table+" WHERE key>="+str(todoKey)+" AND key<"+str((todoKey+1)))

    # Multiple todos selected - remove each selected todo from database and links to other todos
    # (parent todos add children to 'selected' as well so extra algorithm unecessary)
    else:
        delete = sorted(delete,reverse=True)
        for i in delete:
            if todos[i][3] != None and todos[i][3] not in selected:
                todoParent = todos[i][3]
                for g in range(len(todos)):
                    if todos[g][0] == todoParent:
                        parentIndex = g
                        parentChildren = todos[g][4]
                        parentOtherChildren = todos[g][5]
                if i <= (parentIndex+parentChildren):
                    c.execute("UPDATE todos SET children="+str(parentChildren-1)+" WHERE key="+str(todoParent))
                else:
                    c.execute("UPDATE todos SET otherchildren="+str(parentOtherChildren-1)+" WHERE key="+str(todoParent))
            todoKey = todos[i][0]
            c.execute("DELETE FROM todos WHERE key="+str(todoKey))
    conn.commit()
    c.execute("SELECT * FROM todos ORDER BY key ASC")
    todos = c.fetchall()
    update("delete")
            

# Called when delete button clicked - jump to deleteThisTodo() if todos in selected or set up todos for being clicked
def removeTodo():
    global process
    process = "delete"
    if len(selected)>0:
        if messagebox.askokcancel("Delete","Delete selected todos?"):
            deleteThisTodo(selected)
    else:
        cancel()
        global instructionText
        instructionText.set("Click a todo to delete it.")
        global instructionButton
        instructionButton.config(text="Done")
        instructionButton.pack(side=LEFT)
        global todoWidgets
        for i in range(len(todoWidgets)):
            todoWidgets[i].config(bg="red",command=lambda i=i:deleteThisTodo('empty',i))


# Called by initial select subroutine. Colours todo and adds/removes from selected list.
def selectThisTodo(i):
    global todos
    global todoWidgets
    global todoCompletions
    global selected
    todoChildren = todos[i][4]
    todoOtherChildren = todos[i][5]
	
	# If already selected, deselect (including subtasks if parent todo)            
    if i in selected:
        if todos[i][3] not in selected:
            selected.remove(i)
            todoWidgets[i].config(bg="yellow")
            if todoChildren != None:
                for g in range(todoChildren):
                    selected.remove(i+g+1)
                    todoWidgets[i+g+1].config(bg="yellow")
                for g in range(todoOtherChildren):
                    selected.remove(i+todoChildren+g+1)
                    todoWidgets[i+todoChildren+g+1].config(bg="yellow")

    # Select todo (including subtasks if parent todo)   
    else:
        selected.append(i)
        todoWidgets[i].config(bg="#51bd49")
        if todoChildren != None:
            for g in range(todoChildren):
                selected.append(i+g+1)
                todoWidgets[i+g+1].config(bg="#51bd49")
            for g in range(todoOtherChildren):
                selected.append(i+todoChildren+g+1)
                todoWidgets[i+todoChildren+g+1].config(bg="#51bd49")
    todoWidgets[i].toggle()


# Called when select button clicked, sets up todos to be clicked for selection
def selectTodo():
    cancel()
    global process
    process = "select"
    global instructionText
    instructionText.set("Click a todo to select it.")
    global instructionButton
    instructionButton.config(text="Clear selected")
    instructionButton.pack(side=LEFT)
    global todoWidgets
    for i in range(len(todoWidgets)):
        todoWidgets[i].config(bg="yellow",command=lambda i=i:selectThisTodo(i))


# Called when subtask entered. Adds subtask to database, links with parent and calls update()
def subtaskEntered(event=None):
    global c
    global conn
    global todos
    global parent
    global inputBar
    global inputText
    global subColumn
    global parentKey
    global subtaskPartnership
    global categoryText
    newSubtask = inputBar.get()
    if "'" in newSubtask:
        newSubtask = stringEncode(newSubtask)[1]
    inputText.set("Another subtask?")
    inputBar.select_range(0, END)
    parentChildren = todos[parent][4]
    parentOtherChildren = todos[parent][5]
    if subColumn == "yes":
        for i in range(parentChildren+parentOtherChildren,parentChildren,-1):
            c.execute("UPDATE todos SET key="+str(parentKey)+"."+str(i+1)+" WHERE key="+str(parentKey)+"."+str(i))
        c.execute("INSERT INTO todos (key,todo,type,parent,date,category,completion) VALUES ("+str(parentKey)+"."+str(parentChildren+1)+",'"+newSubtask+"',"+str(2)+","+str(parentKey)+".0,'"+todos[parent][6]+"','"+todos[parent][7]+"',0)")
        c.execute("UPDATE todos SET children="+str(parentChildren+1)+" WHERE key="+parentKey+".0")
        calling = "questionSubtask"
        column="yes"
    elif subColumn == "no":
        c.execute("INSERT INTO todos (key,todo,type,parent,date,category,completion) VALUES ("+str(parentKey)+"."+str(parentChildren+parentOtherChildren+1)+",'"+newSubtask+"',"+str(2)+","+str(parentKey)+".0,'"+todos[parent][6]+"','"+todos[parent][7]+"',0)")
        c.execute("UPDATE todos SET otherchildren="+str(parentOtherChildren+1)+" WHERE key="+parentKey+".0")
        calling = "questionSubtask"
        column="no"
    else:
        c.execute("INSERT INTO todos (key,todo,type,parent,date,category,completion) VALUES ("+str(parentKey)+"."+str(parentChildren+1)+",'"+newSubtask+"',"+str(2)+","+str(parentKey)+".0,'"+todos[parent][6]+"','"+todos[parent][7]+"',0)")
        c.execute("UPDATE todos SET children="+str(parentChildren+1)+" WHERE key="+parentKey+".0")
        calling = "subtask"
        column=None
    conn.commit()
    update(calling,parent,column)
    

# Called when question clicked after subtask(). Sets up subtaskEntered()
def addQuestionSubtask(questionIndex,column):
    global inputBar
    global inputText
    global inputButton
    global subColumn
    global parent
    global parentKey
    subColumn = column
    parent = questionIndex
    parentKey = str(todos[parent][0]).split(".")[0]
    inputButton.config(command=subtaskEntered)
    inputBar.bind('<Return>', subtaskEntered)
    inputBar.focus_set()
    inputText.set("Enter subtask to apply to '"+column+"' column")
    inputBar.select_range(0, END)
    for i in range(len(todoWidgets)):
        if i != parent:
            todoWidgets[i].config(bg=defaultColour)
        else:
            todoWidgets[i].config(bg="#51bd49")


# Called when todo clicked after subtask() (long term view). Sets up subtaskEntered()
def addLongtermSubtask(index):
    global parent
    global parentKey
    global inputButton
    global inputBar
    global inputText
    global todoWidgets
    parent = index
    todoWidgets[parent].toggle()
    inputText.set("Enter a subtask")
    inputBar.select_range(0, END)
    parentKey = str(todos[index][0]).split(".")[0]
    inputButton.config(command=lambda e=None,a=1:longtermEntered(e,a))
    inputBar.bind('<Return>', lambda e,a=1:longtermEntered(e,a))
    inputBar.focus_set()
    for i in range(len(todoWidgets)):
        if i != parent:
            todoWidgets[i].config(bg=defaultColour)
        else:
            todoWidgets[i].config(bg="#51bd49")


# Called when todo clicked after subtask(). Sets selected todos to subtasks of parent and updates, or sets up subtaskEntered()
def subThisTodo(i,a=None):
    global defaultColour
    global todos
    global todoWidgets
    global todoCompletions
    global selected
    global c
    global conn
    global parent
    global parentKey
    global parentChildren
    parent = i
    if a==None:
        todoWidgets[i].toggle()
    parentKey = str(todos[parent][0]).split(".")[0]
    parentChildren = todos[parent][4]
    if len(selected)>0:
        g = parentChildren+1
        for i in selected:
            initialKey = str(todos[i][0])
            c.execute("UPDATE todos SET type="+str(2)+", parent="+str(parentKey)+".0"+", key="+str(parentKey)+"."+str(g)+" WHERE key="+initialKey)
            c.execute("UPDATE todos SET children="+str(g)+" WHERE key="+parentKey+".0")
            g += 1
        conn.commit()
        update()
    else:
        global inputBar
        global inputText
        global inputButton
        inputButton.config(command=subtaskEntered)
        inputBar.bind('<Return>', subtaskEntered)
        inputBar.focus_set()
        inputText.set('Enter subtask')
        inputBar.select_range(0, END)
        for i in range(len(todoWidgets)):
            if i != parent:
                todoWidgets[i].config(bg=defaultColour)
            else:
                todoWidgets[i].config(bg="#51bd49")
                

# Called by subtask button. Sets up normal and question todos to be clicked for subtasks.
def subtask():
    global selected
    global todoWidgets
    global defaultColour
    global questionIndexes
    global instructionText
    global instructionButton
    global process
    process = "subtask"
    if len(selected)>0:
        instructionText.set("Apply selected todos as subtasks to which todo?")
    else:
        cancel()
        instructionText.set("Click todo to apply subtask to.")
    instructionButton.config(text="Cancel")
    instructionButton.pack(side=LEFT)
    questionIndexes = list()
    question = -1
    for i in range(len(todoWidgets)):
        if i in selected or todos[i][2]==2:
            todoWidgets[i].config(bg=defaultColour)
        elif todos[i][2]==3:
            question += 1
            questionIndexes.append(i)
            yesLabels[question].config(bg="deep sky blue")
            yesLabels[question].bind("<Button-1>",lambda e,question=questionIndexes[question]:addQuestionSubtask(question,"yes"))
            noLabels[question].config(bg="deep sky blue")
            noLabels[question].bind("<Button-1>",lambda e,question=questionIndexes[question]:addQuestionSubtask(question,"no"))
        elif currentView == "longterm":
            todoWidgets[i].config(bg="Deep Sky Blue",command=lambda index=i:addLongtermSubtask(index))
        else:
            todoWidgets[i].config(bg="Deep Sky Blue",command=lambda index=i:subThisTodo(index))


# Called when todo clicked after question(). Converts to question and deletes or applies existing subtasks to "yes" or "no"
def questionThisTodo(i):
    global todoCompletions
    global todoWidgets
    global todos
    global c
    global conn
    parent = i
    todoWidgets[i].toggle()
    if todos[parent][2] == 3:
        if messagebox.askokcancel("Convert back?","Convert selected question todo back to normal?"):
            if messagebox.askyesnocancel("Pick subtasks","Which subtask column should stay as subtasks? (Cancel for none)"):
                keep = "yes"
            else:
                keep = "no"
    else:
        key = todos[parent][0]
        children = todos[parent][4]
        c.execute("UPDATE todos SET type="+str(3)+" WHERE key="+str(key))
        conn.commit()
        if children > 0:
            column = messagebox.askyesnocancel("Use subtasks?","Pick which column you want the current subtasks to be (Cancel for neither)")
            if column == True:
                c.execute("UPDATE todos SET otherchildren=0 WHERE key="+str(key))
                update()
            elif column == False:
                c.execute("UPDATE todos SET children=0, otherchildren="+str(children)+" WHERE key="+str(key))
                conn.commit()
                update()
            elif column == None:
                c.execute("UPDATE todos SET children=0, otherchildren=0 WHERE key="+str(key))
                conn.commit()
                for i in range(children):
                    selected.append(parent+i+1)
                global calledFrom
                calledFrom = "question"
                deleteThisTodo(selected)
        else:
            c.execute("UPDATE todos SET otherchildren=0 WHERE key="+str(key))
            update()


# Called by question button. Sets up todos to be clicked and converted.
def question():
    cancel()
    global todos
    global todoWidgets
    global instructionText
    global instructionButton
    global process
    process = "question"
    instructionText.set("Click a todo to make a question")
    instructionButton.pack(side=LEFT)
    for i in range(len(todoWidgets)):
        if todos[i][2] == 1:
            todoWidgets[i].config(bg="medium sea green",command = lambda index=i: questionThisTodo(index))
##        elif todos[i][2] == 3:
##            todoWidgets[i].config(bg="medium sea green")


# Called by completed date input, applies date to selected todos or single todo (and any children)
def saveDate(event,a,index):
    global sqlDate
    global todos
    dateSet = dateInput.get().split("/")
    print(dateSet)
    if dateSet[0] == "today" or dateSet[0] == "Today":
        dateSet = str(date.today()).split("-")
    dateInput.place_forget()
    if re.match(r'^\d{2}\/\d{2}\/\d{2}$',"/".join(dateSet)) != None and int(dateSet[0])<32 and int(dateSet[1])<13:
        sqlDate = str("20"+dateSet[2]+"-"+dateSet[1]+"-"+dateSet[0])
        if a==1:
            if len(selected)>0:
                for i in selected:
                    c.execute("UPDATE todos SET date='"+sqlDate+"' WHERE key="+todos[i][0])
            else:
                subtasks = todos[index][4]+todos[index][5]
                parentKey = str(todos[index][0]).split(".")[0]
                c.execute("UPDATE todos SET date='"+sqlDate+"' WHERE key="+parentKey+".0")
                for i in range(int(subtasks)):
                    c.execute("UPDATE todos SET date='"+sqlDate+"' WHERE key="+parentKey+"."+str((i+1)))
            sqlDate = ""
    else:
        messagebox.showerror("Invalid input","Invalid date input. Must be in the form DD/MM/YY and be a real date.")
        setDate(a)
    conn.commit()


# Called when todo clicked after setDate(). Places date input screen and waits for input or cancellation.
def dateThisTodo(index):
    global defaultDate
    if len(selected)<1:
        todoWidgets[index].toggle()
    dateInput.place(x=172,y=55)
    dateInputText.set(defaultDate)
    dateInput.focus_set()
    dateInput.select_range(0,END)
    dateInput.bind("<Return>",lambda e,a=1,index=index: saveDate(e,a,index))


# Called by date button. If toolbar button, sets up todo to be clicked, if input bar button, places date input screen and waits for input or cancellation.
def setDate(button):
    global todoWidgets
    global dateSet
    global defaultDate
    global process
    process = "date"
    if dateSet != "":
        defaultDate = str(dateSet[0]+"/"+dateSet[1]+"/"+dateSet[2])
    else:
        defaultDate = "dd/mm/yy"
    if button == 1:
        if len(selected)>0:
            dateThisTodo(0)
        else:
            for i in range(len(todoWidgets)):
                if todos[i][2] != 2:
                    todoWidgets[i].config(bg="orchid",command = lambda i=i: dateThisTodo(i))
    else:
        Label(todoContent, text="[close]", fg="blue").place(x=450,y=450)
        dateInput.place(x=497,y=490)
        dateInputText.set(defaultDate)
        dateInput.focus_set()
        dateInput.select_range(0,END)
        dateInput.bind("<Return>",lambda e,a=2, index=-1: saveDate(e,a,index))
        dateInput.bind("<Escape>",cancel)


# Called by setCategory() when category box activated when todos selected, or todo clicked. Applies category to todo(s) and updates.
def categoriseThisTodo(index):
    global categoryText
    global categoryList
    global categortList2
    global conn
    global c
    global selected
    global todos
    categoryText = categoryList.get()
    if categoryText not in categoryList['values']:
        categoryList['values'] += tuple([categoryText])
        categoryList2['values'] += tuple([categoryText])
        c.execute("INSERT INTO categories (name) VALUES ('"+categoryText+"')")
    if len(selected)>0:
        for i in selected:
             c.execute("UPDATE todos SET category='"+categoryText+"' WHERE key="+str(todos[i][0]))
    else:
        c.execute("UPDATE todos SET category='"+categoryText+"' WHERE key="+str(todos[index][0]))
    conn.commit()
    c.execute("SELECT * FROM categories")
    update()
 

# Called by either category box. Instantly calls categoriseThisTodo() if todos selected, or sets up todos to be clicked and waits for input
def setCategory(event,inputMethod):
    global todoWidgets
    global categoryList
    global categoryText
    global todos
    global selected
    global process
    process = "category"
    if inputMethod==1:
        if len(selected)>0:
            categoriseThisTodo(0)
        else:
            for i in range(len(todoWidgets)):
                if todos[i][2] != 2:
                    todoWidgets[i].config(bg="black",fg="white",command = lambda i=i: categoriseThisTodo(i))


# Renames categories (accessed through edit category button in toolbar)
def renameCategory(button=None):
    global editCategoryButtons
    global renameCategoryButton
    global deleteCategoryButton
    global editCategoryLabel
    global categories
    global todos
    global c
    global conn
    renameCategoryButton.config(state=DISABLED)
    deleteCategoryButton.config(state=NORMAL)
    editCategoryLabel.config(text="Rename which category?")
    # Sets up category buttons to be clicked, and if recalled asks for new name input, updates todos with category and calls update()
    for i in range(len(categories)):
        rename = categories[i][0]
        editCategoryButtons[i].config(state=ACTIVE,command=lambda rename=rename:renameCategory(rename))
        if button == rename:
            newName = simpledialog.askstring("New category name", "Enter a new name for the category:")
            if newName != None:
                editCategoryButtons[i].config(text=newName)
                c.execute("UPDATE categories SET name='"+newName+"' WHERE name='"+categories[i][0]+"'")
                for g in todos:
                    if g[7] == categories[i][0]:
                        c.execute("UPDATE todos SET category='"+newName+"' WHERE key="+str(g[0]))
    conn.commit()
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()
    categoryList['values'] = ('')
    categoryList['values'] = ('')
    for g in categories:
        categoryList['values'] += tuple(g)
        categoryList2['values'] += tuple(g)
    c.execute("SELECT * FROM todos")
    todos = c.fetchall()
    update()


# Deletes categories. Accessed through edit category button in toolbar.
def deleteCategory(button=None):
    global editCategoryButtons
    global renameCategoryButton
    global deleteCategoryButton
    global editCategoryLabel
    global categories
    global todos
    global c
    global conn
    renameCategoryButton.config(state=NORMAL)
    deleteCategoryButton.config(state=DISABLED)
    editCategoryLabel.config(text="Delete which category?")
    # Sets up category to be clicked, and if recalled ask for confirmation, delete from database, ask to delete todos or not, deletes them if so.
    for i in range(len(categories)):
        editCategoryButtons[i].config(state=ACTIVE,command=lambda a=categories[i][0]:deleteCategory(a))
        if button == categories[i][0]:
            if messagebox.askokcancel("Delete category?","Delete the category "+categories[i][0]+"?"):
                editCategoryButtons[i].destroy()
                c.execute("DELETE FROM categories WHERE name='"+categories[i][0]+"'")
                if messagebox.askyesno("Delete todos?","Delete todos in this category?"):
                    deleteTodos = 1
                else:
                    deleteTodos = 0
                for g in todos:
                    if g[7] == categories[i][0]:
                        if deleteTodos == 0:
                            c.execute("UPDATE todos SET category='' WHERE key="+str(g[0]))
                        else:
                            c.execute("DELETE FROM todos WHERE key="+str(g[0])) 
    conn.commit()
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()
    if len(categories) == 0:
        editCategories.destroy()
    categoryList['values'] = ('')
    categoryList['values'] = ('')
    for g in categories:
        categoryList['values'] += tuple(g)
        categoryList2['values'] += tuple(g)
    c.execute("SELECT * FROM todos")
    todos = c.fetchall()
    update()


# Called by edit category button. Builds edit category window.
def editCategories():
    global editCategories
    global editCategoryButtons
    global renameCategoryButton
    global deleteCategoryButton
    global editCategoryLabel
    global categories
    editCategoryButtons = list()
    editCategories = Toplevel(app)
    editCategories.title("Edit categories")
    c.execute("SELECT * FROM categories")
    categories = c.fetchall()
    topButtons = Frame(editCategories)
    topButtons.pack(side=TOP)
    renameCategoryButton = Button(topButtons, text="Rename", command=renameCategory)
    renameCategoryButton.pack(side=LEFT,padx=5,pady=15)
    deleteCategoryButton = Button(topButtons, text="Delete", command=deleteCategory)
    deleteCategoryButton.pack(side=LEFT,padx=5,pady=15)
    Separator(editCategories, orient=HORIZONTAL).pack(side=TOP,fill=X,pady=3,padx=5)
    editCategoryLabel = Label(editCategories, text="", font=("Segoe UI",12))
    editCategoryLabel.pack(side=TOP)
    for i in categories:
        editCategoryButton = Button(editCategories, text=i[0], state=DISABLED, padx=5)
        editCategoryButtons.append(editCategoryButton)
        editCategoryButton.pack(side=TOP)
    if len(categories) == 0:
        editCategoryLabel.config(text="You have no categories.")
        renameCategoryButton.config(state=DISABLED)
        deleteCategoryButton.config(state=DISABLED)


# Called by switch account button. Asks for input of account name and calls assessAccount() with new username.
def switchAccount():
    userSwitch = simpledialog.askstring("Account switch","Enter username of desired account:")
    if userSwitch != None:
        conn.close()
        global oldUsername
        global username
        oldUsername = username
        assessAccount(None,userSwitch)


# Called by log off button. Rebuilds initial log in window if the user confirms it.
def logOff():
	global username
	global initial
	if messagebox.askyesno("Log off?","Log off "+username+"?"):
		conn.close()
		app.destroy()
		initial = Toplevel(root)
		initial.title("Prioritree")
		initial.geometry("300x350")
		logo = PhotoImage(file="icons/small.gif")
		logoPack = Label(initial,image=logo)
		logoPack.image = logo
		logoPack.pack(side=TOP)
		Label(initial,text="Prioritree",font=("Segoe UI",32)).pack(side=TOP,pady=0)
		Label(initial,text="© Jerome Beckett 2016\n",font=("Segoe UI",11)).pack(side=TOP,pady=0)
		userSection = Frame(initial)
		userSection.pack(fill=X,pady=(0,5))
		Label(userSection,text="Username",width=10).pack(side=LEFT)
		global userInput
		userInput = Entry(userSection,bg="white")
		userInput.pack(fill=X,pady=5,padx=(0,5))
		userInput.focus_set()
		Button(initial,text="Create / Log in",command=lambda e=None,a=None:assessAccount(e,a)).pack(side=TOP,pady=5)
		initial.bind('<Return>', lambda e,a=None:assessAccount(e,a))

def settings():
	settings = Toplevel(app)
	settings.title("Prioritree settings")
	settings.geometry("300x500")
	Label(settings,text="Settings",font=("Segoe UI",20)).pack(side=TOP,pady=0)
	Separator(settings,orient=HORIZONTAL).pack(side=TOP,fill=X,pady=5)
	Checkbutton(settings, text="Automatically tick subtasks if parent completed (FIX) ",onvalue=0).pack(side=TOP,anchor=W)
	Checkbutton(settings, text="Archive completed tasks").pack(side=TOP,anchor=W)

def help():
    os.startfile('User manual.pdf')

# Called when reference book item edited or added.
def saveReference(index=None):
    global c
    global conn
    global nameEntry
    global locationEntry
    global timeEntry
    global descriptionEntry
    global titleEntry
    global locationEntry
    global dateEntry
    global timeEntry
    global descriptionEntry
    global urlEntry

    # If item is a contact, add to database with retrieved values if new, update old one if not. Recalls reference book build.
    if referenceType == "contacts":
        if index == None:
            c.execute("INSERT INTO contacts (name,address,phone,email) VALUES ('"+nameEntry.get()+"','"+addressEntry.get()+"','"+phoneEntry.get()+"','"+emailEntry.get()+"')")
        else:
            c.execute("UPDATE contacts SET name='"+nameEntry.get()+"',address='"+addressEntry.get()+"',phone='"+phoneEntry.get()+"',email='"+emailEntry.get()+"' WHERE key="+str(contacts[index][0]))
        conn.commit()
        reference("Contacts")

    # If item is an event, prepare date format and add event to database with retrieved values if new, update if not. Recalls reference book build.
    elif referenceType == "events":
        date1 = dateEntry.get().split("/")
        timeCheck = timeEntry.get().split(":")
        if ((re.match(r'^\d{2}\/\d{2}\/\d{2}$',dateEntry.get()) != None and int(date1[0])<32 and int(date1[1])<13) or (len(date1)==1 and date1[0]=="")) and ((re.match(r'^\d\d:\d\d$',timeEntry.get()) != None and int(timeCheck[0])<25 and int(timeCheck[1])<60) or (len(timeCheck)==1 and timeCheck[0]=="")):
            date1 = dateEntry.get().split("/")
            date2 = date1[2]+"-"+date1[1]+"-"+date1[0]
            time = timeEntry.get()+":00"
            datetime = str(date2)+" "+str(time)
            if index == None:
                c.execute("INSERT INTO events (title,location,datetime,description) VALUES ('"+titleEntry.get()+"','"+locationEntry.get()+"','"+datetime+"','"+descriptionEntry.get()+"')")
            else:
                c.execute("UPDATE events SET title='"+titleEntry.get()+"',location='"+locationEntry.get()+"',datetime='"+datetime+"',description='"+descriptionEntry.get()+"' WHERE key="+str(events[index][0]))
            conn.commit()
            reference("Events")
        else:
            messagebox.showerror("Invalid inputs","Please check your date and time inputs. They are invalid. Date must be empty or dd/mm/yy and time must be empty or hh:mm.")
    # If item is a reminder, add reminder to database with retrieved values if new, update if not. Recalls reference book build. Call updateNotifications() if reminder activated/deactivated.
    elif referenceType == "reminders":
        global active
        global previouslyActive
        setAsActive = active.get()
        if index == None:
            c.execute("INSERT INTO reminders (title,description,active) VALUES ('"+titleEntry.get()+"','"+descriptionEntry.get()+"',"+str(setAsActive)+")")
        else:
            c.execute("UPDATE reminders SET title='"+titleEntry.get()+"',description='"+descriptionEntry.get()+"',active="+str(setAsActive)+" WHERE key="+str(reminders[index][0]))
        conn.commit()
        reference("Reminders")
        if setAsActive != previouslyActive:
            updateNotifications()

    # If item is a URL, add URL to database if new, update if not. Recalls reference book build.
    elif referenceType == "urls":
        if index == None:
            c.execute("INSERT INTO urls (url) VALUES ('"+urlEntry.get()+"')")
        else:
            c.execute("UPDATE urls SET url='"+urlEntry.get()+"' WHERE key="+str(url[index][0]))
        conn.commit()
        reference("URLs")      


# Called when add or edit [reference book item] clicked. Sets up input screen.
def addReference(index=None):
    global referenceHeaderText
    global referenceType
    global referenceFrame
    global contacts
    global events
    global reminders
    global urls
    global nameEntry
    global addressEntry
    global phoneEntry
    global emailEntry
    global titleEntry
    global locationEntry
    global dateEntry
    global timeEntry
    global descriptionEntry
    global urlEntry

    # If contact, set up blank textboxes if new, load existing data if not.
    if referenceType == "contacts":
        if index == None:
            referenceHeaderText.set("New contact")
            name = ""
            address = ""
            phone = ""
            email = ""
        else:
            referenceHeaderText.set("Edit contact")
            name = contacts[index][1]
            address = contacts[index][2]
            phone = contacts[index][3]
            email = contacts[index][4]

        # Destroy previous contents in frame, rebuild and create input widgets. Set string variables to existing value if there is one.
        referenceFrame.destroy()
        referenceFrame = Frame(rightFrame,width=300)
        referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)

        nameText = StringVar()
        Label(referenceFrame, text="Name: ").grid(row=0,column=0)
        nameEntry = Entry(referenceFrame,textvariable=nameText,width=20)
        nameEntry.grid(row=0,column=1)
        nameText.set(name)
        addressText = StringVar()
        Label(referenceFrame, text="Address: ").grid(row=1,column=0)
        addressEntry = Entry(referenceFrame,textvariable=addressText,width=20)
        addressEntry.grid(row=1,column=1)
        addressText.set(address)
        phoneText = StringVar()
        Label(referenceFrame, text="Phone number: ").grid(row=2,column=0)
        phoneEntry = Entry(referenceFrame,textvariable=phoneText,width=20)
        phoneEntry.grid(row=2,column=1)
        phoneText.set(phone)
        emailText = StringVar()
        Label(referenceFrame, text="Email: ").grid(row=3,column=0)
        emailEntry = Entry(referenceFrame,textvariable=emailText,width=20)
        emailEntry.grid(row=3,column=1)
        emailText.set(email)
        Button(referenceFrame,text="Save",command=lambda i=index: saveReference(i)).grid(row=4,column=1)
        Button(referenceFrame,text="Back",command=lambda: reference("Contacts")).grid(row=4,column=0)

    # If event, set up blank textboxes if new, load existing data if not (splitting datetime value into date and time).
    elif referenceType == "events":
        if index == None:
            referenceHeaderText.set("New events")
            title = ""
            location = ""
            time = ""
            date = ""
            description = ""
        else:
            referenceHeaderText.set("Edit event")
            title = events[index][1]
            location = events[index][2]
            dateSetup = events[index][3].split(" ")[0].split("-")
            date = dateSetup[2]+"/"+dateSetup[1]+"/"+dateSetup[0]
            timeSetup = events[index][3].split(" ")[1].split(":")
            time = timeSetup[0]+":"+timeSetup[1]
            description = events[index][4]

        # Destroy previous contents in frame, rebuild and create input widgets. Set string variables to existing value if there is one.
        referenceFrame.destroy()
        referenceFrame = Frame(rightFrame,width=300)
        referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
        titleText = StringVar()
        Label(referenceFrame, text="Title: ").grid(row=0,column=0)
        titleEntry = Entry(referenceFrame,textvariable=titleText,width=20)
        titleEntry.grid(row=0,column=1)
        titleText.set(title)
        locationText = StringVar()
        Label(referenceFrame, text="Location: ").grid(row=1,column=0)
        locationEntry = Entry(referenceFrame,textvariable=locationText,width=20)
        locationEntry.grid(row=1,column=1)
        locationText.set(location)
        dateText = StringVar()
        Label(referenceFrame, text="Date: ").grid(row=2,column=0)
        dateEntry = Entry(referenceFrame,textvariable=dateText,width=20)
        dateEntry.grid(row=2,column=1)
        dateText.set(date)
        timeText = StringVar()
        Label(referenceFrame, text="Time: ").grid(row=3,column=0)
        timeEntry = Entry(referenceFrame,textvariable=timeText,width=20)
        timeEntry.grid(row=3,column=1)
        timeText.set(time)
        descriptionText = StringVar()
        Label(referenceFrame, text="Description: ").grid(row=4,column=0)
        descriptionEntry = Entry(referenceFrame,textvariable=descriptionText,width=20)
        descriptionEntry.grid(row=4,column=1)
        descriptionText.set(description)
        Button(referenceFrame,text="Save",command=lambda i=index: saveReference(i)).grid(row=5,column=1)
        Button(referenceFrame,text="Back",command=lambda: reference("Events")).grid(row=5,column=0)

    # If reminder, set up blank textboxes if new, load existing data if not.
    elif referenceType == "reminders":
        global previouslyActive
        if index == None:
            referenceHeaderText.set("New reminder")
            title = ""
            description = ""
            previouslyActive = 0
        else:
            referenceHeaderText.set("Edit contact")
            title = reminders[index][1]
            description = reminders[index][2]
            previouslyActive = reminders[index][3]

        # Destroy previous contents in frame, rebuild and create input widgets. Set string variables and checkbox value to existing value if there is one.
        referenceFrame.destroy()
        referenceFrame = Frame(rightFrame,width=300)
        referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
        titleText = StringVar()
        Label(referenceFrame, text="Title: ").grid(row=0,column=0)
        titleEntry = Entry(referenceFrame,textvariable=titleText,width=20)
        titleEntry.grid(row=0,column=1)
        titleText.set(title)
        descriptionText = StringVar()
        Label(referenceFrame, text="Description: ").grid(row=1,column=0)
        descriptionEntry = Entry(referenceFrame,textvariable=descriptionText,width=20)
        descriptionEntry.grid(row=1,column=1)
        descriptionText.set(description)
        global active
        active = IntVar()
        checkbox = Checkbutton(referenceFrame, text="Add to notifications", variable=active)
        checkbox.grid(row=2,column=1)
        if previouslyActive == 1:
            checkbox.select()
        Button(referenceFrame,text="Save",command=lambda i=index: saveReference(i)).grid(row=3,column=1)
        Button(referenceFrame,text="Back",command=lambda: reference("Reminders")).grid(row=3,column=0)

    # If URL, set up blank textbox if new, load existing data if not.
    elif referenceType == "urls":
        if index == None:
            referenceHeaderText.set("New URL")
            url = ""
        else:
            referenceHeaderText.set("Edit contact")
            url = urls[index][1] 

        # Destroy previous contents in frame, rebuild and create input widgets. Set string variable to existing value if there is one.
        referenceFrame.destroy()
        referenceFrame = Frame(rightFrame,width=300)
        referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
        urlText = StringVar()
        urlEntry = Entry(referenceFrame,textvariable=urlText,width=20)
        urlEntry.grid(row=0,column=0,columnspan=2)
        urlText.set(url)
        Button(referenceFrame,text="Save",command=lambda i=index: saveReference(i)).grid(row=1,column=1)
        Button(referenceFrame,text="Back",command=lambda: reference("URLs")).grid(row=1,column=0)

# Deletes a reference book item. Called from delete button in specific element view. Removes element from respective database and recalls reference book build.
def deleteReference(index=None):
    global c
    global conn
    if referenceType == "contacts":
        if messagebox.askokcancel("Delete contact?","Delete this contact?"):
            c.execute("DELETE FROM contacts WHERE key="+str(contacts[index][0]))
            conn.commit()
            reference("Contacts")
    elif referenceType == "events":
        if messagebox.askokcancel("Delete event?","Delete this event?"):
            c.execute("DELETE FROM events WHERE key="+str(events[index][0]))
            conn.commit()
            reference("Events")
    elif referenceType == "reminders":
        if messagebox.askokcancel("Delete reminder?","Delete this reminder?"):
            c.execute("DELETE FROM reminders WHERE key="+str(reminders[index][0]))
            conn.commit()
            reference("Reminders")        
            updateNotifications()
    elif referenceType == "urls":
        if messagebox.askokcancel("Delete URL?","Delete this URL?"):
            c.execute("DELETE FROM urls WHERE key="+str(urls[index][0]))
            conn.commit()
            reference("URLs")


# Opens view screen of specific reference book item by clicking it,
def viewReference(event,index):
    global referenceHeaderText
    global referenceType
    global contacts
    global events
    global reminders
    global urls
    global referenceFrame

    # If it is a contact, build the details using the contacts list variable
    if referenceType == "contacts":
        referenceHeaderText.set(contacts[index][1])
        referenceFrame.destroy()
        referenceFrame = Frame(rightFrame,width=300)
        referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
        
        Label(referenceFrame, text="Address: ").grid(row=0,column=0,columnspan=2,sticky=W)
        Label(referenceFrame, text=contacts[index][2]).grid(row=0,column=2,sticky=W)
        Label(referenceFrame, text="Phone number: ").grid(row=1,column=0,columnspan=2,sticky=W)
        Label(referenceFrame, text=contacts[index][4]).grid(row=1,column=2,sticky=W)
        Label(referenceFrame, text="Email: ").grid(row=2,column=0,columnspan=2,sticky=W)
        Label(referenceFrame, text=contacts[index][3]).grid(row=2,column=2,sticky=W)

        Button(referenceFrame, text="Back",command=lambda:reference("Contacts")).grid(row=3,column=0,pady=10)
        Button(referenceFrame, text="Edit",command=lambda i=index: addReference(i)).grid(row=3,column=1,pady=10)
        Button(referenceFrame, text="Delete",command=lambda i=index:deleteReference(i)).grid(row=3,column=2,pady=10)

    # If it is an event, build the details using the events list variable (splitting datetime into date and time)
    elif referenceType == "events":
        referenceHeaderText.set(events[index][1])
        referenceFrame.destroy()
        referenceFrame = Frame(rightFrame,width=300)
        referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
        
        Label(referenceFrame, text="Location: ").grid(row=0,column=0,columnspan=2,sticky=W)
        Label(referenceFrame, text=events[index][2]).grid(row=0,column=2,sticky=W)
        global dateSetup
        dateSetup = events[index][3].split(" ")[0].split("-")
        date = dateSetup[2]+"/"+dateSetup[1]+"/"+dateSetup[0]
        Label(referenceFrame, text="Date: ").grid(row=1,column=0,columnspan=2,sticky=W)
        Label(referenceFrame, text=date).grid(row=1,column=2,sticky=W)
        timeSetup = events[index][3].split(" ")[1].split(":")
        time = timeSetup[0]+":"+dateSetup[1]
        Label(referenceFrame, text="Time: ").grid(row=2,column=0,columnspan=2,sticky=W)
        Label(referenceFrame, text=time).grid(row=2,column=2,sticky=W)
        Label(referenceFrame, text="Description: ").grid(row=3,column=0,columnspan=2,sticky=W)
        Label(referenceFrame, text=events[index][4]).grid(row=3,column=2,sticky=W)

        Button(referenceFrame, text="Back",command=lambda:reference("Events")).grid(row=4,column=0,pady=10)
        Button(referenceFrame, text="Edit",command=lambda i=index: addReference(i)).grid(row=4,column=1,pady=10)
        Button(referenceFrame, text="Delete",command=lambda i=index:deleteReference(i)).grid(row=4,column=2,pady=10)

    # If it is a reminder, build the details using the reminders list variable
    elif referenceType == "reminders":
        referenceHeaderText.set(reminders[index][1])
        referenceFrame.destroy()
        referenceFrame = Frame(rightFrame,width=300)
        referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
        Label(referenceFrame, text="Description: ").grid(row=0,column=0,columnspan=2,sticky=W)
        Label(referenceFrame, text=reminders[index][2]).grid(row=0,column=2,sticky=W)
        Label(referenceFrame, text="Activated? ").grid(row=1,column=0,columnspan=2,sticky=W)
        if reminders[index][3] == 1:
            isItActive = "YES"
        else:
            isItActive = "NO"
        Label(referenceFrame, text=isItActive).grid(row=1,column=2,sticky=W)

        Button(referenceFrame, text="Back",command=lambda:reference("Reminders")).grid(row=2,column=0,pady=10)
        Button(referenceFrame, text="Edit",command=lambda i=index: addReference(i)).grid(row=2,column=1,pady=10)
        Button(referenceFrame, text="Delete",command=lambda i=index:deleteReference(i)).grid(row=2,column=2,pady=10)

    # If it is a URL, build the details using the URLs list variable
    elif referenceType == "urls":
        referenceHeaderText.set(urls[index][1])
        referenceFrame.destroy()
        referenceFrame = Frame(rightFrame,width=300)
        referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
        Button(referenceFrame, text="Back",command=lambda:reference("URLs")).pack(side=TOP)
        Button(referenceFrame, text="Edit",command=lambda i=index: addReference(i)).pack(side=TOP)
        Button(referenceFrame, text="Delete",command=lambda i=index:deleteReference(i)).pack(side=TOP)


# Called when any of the reference book buttons are clicked
def reference(called):
    global c
    global conn
    global rightFrame
    global referenceType
    global contacts
    global events
    global reminders
    global urls
    global referenceFrame
    rightFrame.pack_forget()
    rightFrame.pack(side=RIGHT,anchor=N, fill=Y)
    referenceType = called.lower()
    referenceFrame.destroy()
    referenceHeaderText.set(called)
    referenceFrame = Frame(rightFrame)
    referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
    addCircleIcon = PhotoImage(file="icons/add-circle.gif")
    addCircleButton = Button(referenceFrame, image=addCircleIcon, command=addReference)
    addCircleButton.image = addCircleIcon
    addCircleButton.grid(row=0,column=2,padx=(15,0))

    # If contacts button clicked, fetch contacts from database, and list the names of each contact alphabetically, link them to viewReference()
    if referenceType == "contacts":
        c.execute("SELECT * FROM contacts ORDER BY name ASC")
        contacts = c.fetchall()
        currentLetter = ""
        for i in range(len(contacts)):
            if currentLetter != contacts[i][1][0]:
                currentLetter = contacts[i][1][0].upper()
                Label(referenceFrame, text=currentLetter, font=("Segoe UI",12)).grid(row=i,column=0,padx=5)
            contactLabel = Label(referenceFrame, fg="blue", text=contacts[i][1])
            contactLabel.grid(row=i,column=1,sticky=W)
            contactLabel.bind("<Button-1>",lambda e,i=i:viewReference(e,i))

    # If events button clicked, fetch events from database, and list the titles of each event chronologically, link them to viewReference()
    elif referenceType == "events":
        c.execute("SELECT * FROM events ORDER BY datetime ASC")
        events = c.fetchall()
        referenceHeaderText.set("Events")
        currentDate = ""
        for i in range(len(events)):
            date = events[i][3].split(" ")[0]
            time = events[i][3].split(" ")[1]
            if currentDate != date:
                currentDate = date
                Label(referenceFrame, text=date.split("-")[2]+"/"+date.split("-")[1], font=("Segoe UI",12)).grid(row=i,column=0,padx=5)
            contactLabel = Label(referenceFrame, fg="blue", text=events[i][1])
            contactLabel.grid(row=i,column=1,sticky=W)
            contactLabel.bind("<Button-1>",lambda e,i=i:viewReference(e,i))

    # If reminders button clicked, fetch reminders from database, and list the name of each one, colouring them green if they are active. Link them to viewReference()
    elif referenceType == "reminders":
        c.execute("SELECT * FROM reminders")
        reminders = c.fetchall()
        referenceHeaderText.set("Reminders")
        for i in range(len(reminders)):
            if reminders[i][3] == 1:
                textColour = "green"
            else:
                textColour = "blue"
            reminderLabel = Label(referenceFrame, fg=textColour, text=reminders[i][1])
            reminderLabel.grid(row=i,column=0,sticky=W)
            reminderLabel.bind("<Button-1>",lambda e,i=i:viewReference(e,i))

    # If URLs button clicked, fetch URLs from database and list them, link them to viewReference()
    elif referenceType == "urls":
        c.execute("SELECT * FROM urls")
        urls = c.fetchall()
        referenceHeaderText.set("URLs")
        for i in range(len(urls)):
            urlLabel = Label(referenceFrame, fg="blue", text=urls[i][1])
            urlLabel.grid(row=i,column=0,sticky=W)
            urlLabel.bind("<Button-1>",lambda e,i=i:viewReference(e,i))


# Called by save button in plan screen, takes input from plan textbox and saves it to a text file
def savePlan():
    global planningSpace
    global username
    planSave = planningSpace.get(1.0,END)
    p = open("userdata/plans/"+username+".txt","w")
    p.write(planSave)
    p.close()


# Called by plan button, builds planning space in frame, fetches plan data from text file and inserts it into the textbox
def plan():
    global rightFrame
    rightFrame.pack_forget()
    rightFrame.pack(side=RIGHT, anchor=N, fill=Y)
    global referenceFrame
    referenceFrame.destroy()
    referenceHeaderText.set("Planning space")
    referenceFrame = Frame(rightFrame)
    referenceFrame.pack(side=RIGHT,anchor=N,fill=Y,expand=True)
    Button(referenceFrame,text="Save",font=("Segoe UI",14),command=savePlan).pack(side=BOTTOM)
    try:
        p = open("userdata/plans/"+username+".txt","r+")
    except FileNotFoundError:
        p = open("userdata/plans/"+username+".txt","w+")
    planLoad = p.read()
    p.close()
    global planningSpace
    planningSpace = Text(referenceFrame,width=25)
    planningSpace.pack(side=TOP,fill=Y,expand=True)
    planningSpace.insert(1.0,planLoad)


# Closes reference book frame
def closeReference():
    global rightFrame
    global referenceButton
    rightFrame.pack_forget()


# Called by assessAccount(), this subroutine builds the UI of the program, links it to the respective functions, defines any necessary variables before their use.
def construct():

    # Destroy log in window, build app window
    global initial
    initial.destroy()
    global app
    global username
    app = Toplevel(root)
    app.title("Prioritree - "+username)
    app.geometry("905x600")

    # Build notification bar (kept hidden for now)
    global notification
    global notificationLabel
    notification = StringVar()
    notificationLabel = Label(app, fg="red", font=("Segoe UI Bold",16), bd=1, relief=SUNKEN, textvariable=notification)
    
    # Build view selectors
    views = Frame(app, padx=10)
    views.pack(side=BOTTOM,anchor=W)
    global generalView
    global sequentialView
    global dailyView
    global weeklyView
    global categoryView
    global longtermView
    generalView = Button(views, text="General view", bg="#51bd49", relief=SUNKEN, command=general)
    sequentialView = Button(views, text="Sequential view", bg="#51bd49", relief=GROOVE, command=sequential)
    dailyView = Button(views, text="Daily view", bg="#51bd49", relief=GROOVE, command=daily)
    weeklyView = Button(views, text="Weekly view", bg="#51bd49", relief=GROOVE, command=weekly)
    categoryView = Button(views, text="Category view", bg="#51bd49", relief=GROOVE, command=category)
    longtermView = Button(views, text="Long term view", bg="#51bd49", relief=GROOVE, command=longterm)
    generalView.pack(side=LEFT)
    sequentialView.pack(side=LEFT)
    dailyView.pack(side=LEFT)
    weeklyView.pack(side=LEFT)
    categoryView.pack(side=LEFT)
    longtermView.pack(side=LEFT)

    # Build general view
    global generalFrame
    global newAccount
    generalFrame = Frame(app)
    generalFrame.pack(fill=BOTH)
    bigLogo = PhotoImage(file="icons/big.gif")
    generalLogo = Label(generalFrame, image=bigLogo)
    generalLogo.pack(side=TOP)
    generalLogo.image=bigLogo
    Label(generalFrame,text="P R I O R I T R E E",font=("Segoe UI Light",46)).pack(side=TOP)
    Separator(generalFrame,orient=HORIZONTAL).pack(side=TOP,fill=X)
    if newAccount == "no":
    	welcomeText = "Welcome back, "+username+"!"
    	welcomeButton = "Continue"
    	introduction = 0
    else:
    	welcomeText = "Welcome, "+username+"!"
    	welcomeButton = "Let's get started..."
    	introduction = 1
    Label(generalFrame,text=welcomeText,font=("Segoe UI Light",28)).pack(side=TOP)
    Button(generalFrame,text=welcomeButton,borderwidth=4,font=("Segoe UI Light",20),command=lambda a=introduction:getStarted(a)).pack(side=TOP,pady=(30,0))

    # Build the main frame (this will be the highest level frame in the window when not in general view)
    global main
    main = Frame(app)
    main.pack(side=TOP,anchor=W)
    global defaultColour
    defaultColour = main.cget("bg")

    # Build the toolbars at the top
    toolbars = Frame(main)
    toolbars.pack(side=TOP,anchor=W)

    # Main toolbar
    global leftToolbar
    leftToolbar = Frame(toolbars, padx=10, bg="#51bd49")
    leftToolbar.pack(side=LEFT,padx=10)

    # Manage section buttons, icons and text
    manageIcons = Frame(leftToolbar, bg="#51bd49")
    manageIcons.pack(side=LEFT,anchor=N)
    manageText = Label(manageIcons, text="Manage", bg="#51bd49")
    manageText.pack(side=TOP)
    addIcon = PhotoImage(file="icons/plusbox.gif")
    addButton = Button(manageIcons, image=addIcon, relief=FLAT, bg="#51bd49", command=addTodo)
    addButton.image = addIcon
    addButton.pack(side=LEFT, anchor=S)
    removeIcon = PhotoImage(file="icons/minusbox.gif")
    removeButton = Button(manageIcons, image=removeIcon, relief=FLAT, bg="#51bd49", command=removeTodo)
    removeButton.image = removeIcon
    removeButton.pack(side=LEFT, anchor=S)
    selectIcon = PhotoImage(file="icons/select.gif")
    global selectButton
    selectButton = Button(manageIcons, image=selectIcon, relief=FLAT, bg="#51bd49", command=selectTodo)
    selectButton.image = selectIcon
    selectButton.pack(side=LEFT, anchor=S)
    subtaskIcon = PhotoImage(file="icons/indent.gif")
    subtaskButton = Button(manageIcons, image=subtaskIcon, relief=FLAT, bg="#51bd49", command=subtask)
    subtaskButton.image = subtaskIcon
    subtaskButton.pack(side=LEFT, anchor=S)
    questionIcon = PhotoImage(file="icons/question.gif")
    global questionButton
    questionButton = Button(manageIcons, image=questionIcon, relief=FLAT, bg="#51bd49", command=question)
    questionButton.image = questionIcon
    questionButton.pack(side=LEFT, anchor=S)
    longtermIcon = PhotoImage(file="icons/longterm.gif")
    longtermButton = Button(manageIcons, image=longtermIcon, relief=FLAT, bg="#51bd49", command=lambda:longterm("asking"))
    longtermButton.image = longtermIcon
    longtermButton.pack(side=LEFT, anchor=S)

    separator1 = Separator(leftToolbar, orient=VERTICAL)
    separator1.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # Date section button, icon and text
    dateIcons = Frame(leftToolbar, bg="#51bd49")
    dateIcons.pack(side=LEFT,anchor=N)
    dateText = Label(dateIcons, text="Date", bg="#51bd49")
    dateText.pack(side=TOP)    
    dateIcon = PhotoImage(file="icons/date.gif")
    global dateButton
    dateButton = Button(dateIcons, image=dateIcon, relief=FLAT, bg="#51bd49", command=lambda:setDate(1))
    dateButton.image = dateIcon
    dateButton.pack(side=TOP)
    
    separator2 = Separator(leftToolbar, orient=VERTICAL)
    separator2.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # Category section buttons, icons and text
    categoryIcons = Frame(leftToolbar, bg="#51bd49")
    categoryIcons.pack(side=LEFT,anchor=N)
    global categoryInput
    global categoryList
    global categories
    categoryLabel = Label(categoryIcons, text="Category", bg="#51bd49")
    categoryLabel.pack(side=TOP)    
    categoryList = Combobox(categoryIcons, width=10)
    categoryList['values'] = ('')
    for g in categories:
        categoryList['values'] += tuple(g)
    categoryList.pack(side=LEFT,padx=2)
    categoryList.bind("<Return>",lambda e,inputMethod=1: setCategory(e,inputMethod))
    categoryList.bind("<<ComboboxSelected>>",lambda e,inputMethod=1: setCategory(e,inputMethod))
    editCategoryIcon = PhotoImage(file="icons/edit.gif")
    editCategoryButton = Button(categoryIcons, image=editCategoryIcon, relief=FLAT, bg="#51bd49",command=editCategories)
    editCategoryButton.image = editCategoryIcon
    editCategoryButton.pack(side=LEFT)
    
    separator3 = Separator(leftToolbar, orient=VERTICAL)
    separator3.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # Account section buttons, icons and text
    accountIcons = Frame(leftToolbar, bg="#51bd49")
    accountIcons.pack(side=LEFT,anchor=N)
    accountText = Label(accountIcons, text="Account", bg="#51bd49")
    accountText.pack(side=TOP)
    accountSwitchIcon = PhotoImage(file="icons/switch.gif")
    accountSwitchButton = Button(accountIcons, image=accountSwitchIcon, relief=FLAT, bg="#51bd49", command=switchAccount)
    accountSwitchButton.image = accountSwitchIcon
    accountSwitchButton.pack(side=LEFT)
    logOutIcon = PhotoImage(file="icons/logout.gif")
    logOutButton = Button(accountIcons, image=logOutIcon, relief=FLAT, bg="#51bd49",command=logOff)
    logOutButton.image = logOutIcon
    logOutButton.pack(side=LEFT)

    separator4 = Separator(leftToolbar, orient=VERTICAL)
    separator4.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # Settings section buttons, icons and text
    settingsIcons = Frame(leftToolbar, bg="#51bd49")
    settingsIcons.pack(side=LEFT,anchor=N)
    settingsText = Label(settingsIcons, text="Settings", bg="#51bd49")
    settingsText.pack(side=TOP)
    settingsIcon = PhotoImage(file="icons/settings.gif")
    settingsButton = Button(settingsIcons, image=settingsIcon, relief=FLAT, bg="#51bd49",command=settings)
    settingsButton.image = settingsIcon
    settingsButton.pack(side=TOP)

    separator5 = Separator(leftToolbar, orient=VERTICAL)
    separator5.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # Help section buttons, icons and text
    helpIcons = Frame(leftToolbar, bg="#51bd49")
    helpIcons.pack(side=LEFT,anchor=N)
    helpText = Label(helpIcons, text="Help", bg="#51bd49")
    helpText.pack(side=TOP)
    helpIcon = PhotoImage(file="icons/help.gif")
    helpButton = Button(helpIcons, image=helpIcon, relief=FLAT, bg="#51bd49", command=help)
    helpButton.image = helpIcon
    helpButton.pack(side=TOP)

    # Reference book toolbar
    global rightToolbar
    rightToolbar = Frame(toolbars, padx=10, bg="#51bd49")
    rightToolbar.pack(side=LEFT, padx=10)

    # Main reference book button
    referenceBookIcon = PhotoImage(file="icons/book.gif")
    referenceBookButton = Button(rightToolbar, image=referenceBookIcon, relief=FLAT, bg="#51bd49")
    referenceBookButton.image = referenceBookIcon
    referenceBookButton.pack(side=LEFT)

    separator6 = Separator(rightToolbar, orient=VERTICAL)
    separator6.pack(side=LEFT,fill=Y,pady=3,padx=5)

    #Contacts section button, icon and text
    contactsIcons = Frame(rightToolbar, bg="#51bd49")
    contactsIcons.pack(side=LEFT,anchor=N)
    contactsText = Label(contactsIcons, text="Contacts", bg="#51bd49")
    contactsText.pack(side=TOP)
    contactsIcon = PhotoImage(file="icons/contacts.gif")
    contactsButton = Button(contactsIcons, image=contactsIcon, relief=FLAT, bg="#51bd49", command=lambda a="Contacts":reference(a))
    contactsButton.image = contactsIcon
    contactsButton.pack(side=TOP)

    separator7 = Separator(rightToolbar, orient=VERTICAL)
    separator7.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # Events section button, icon and text
    eventsIcons = Frame(rightToolbar, bg="#51bd49")
    eventsIcons.pack(side=LEFT,anchor=N)
    eventsText = Label(eventsIcons, text="Events", bg="#51bd49")
    eventsText.pack(side=TOP)
    eventsIcon = PhotoImage(file="icons/events.gif")
    eventsButton = Button(eventsIcons, image=eventsIcon, relief=FLAT, bg="#51bd49", command=lambda a="Events":reference(a))
    eventsButton.image = eventsIcon
    eventsButton.pack(side=TOP)

    separator8 = Separator(rightToolbar, orient=VERTICAL)
    separator8.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # Reminders section button, icon and text
    remindersIcons = Frame(rightToolbar, bg="#51bd49")
    remindersIcons.pack(side=LEFT,anchor=N)
    remindersText = Label(remindersIcons, text="Reminders", bg="#51bd49")
    remindersText.pack(side=TOP)
    remindersIcon = PhotoImage(file="icons/reminder.gif")
    remindersButton = Button(remindersIcons, image=remindersIcon, relief=FLAT, bg="#51bd49", command=lambda a="Reminders":reference(a))
    remindersButton.image = remindersIcon
    remindersButton.pack(side=TOP)

    separator9 = Separator(rightToolbar, orient=VERTICAL)
    separator9.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # URLs section button, icon and text
    URLIcons = Frame(rightToolbar, bg="#51bd49")
    URLIcons.pack(side=LEFT,anchor=N)
    URLText = Label(URLIcons, text="URLs", bg="#51bd49")
    URLText.pack(side=TOP)
    URLIcon = PhotoImage(file="icons/urls.gif")
    URLButton = Button(URLIcons, image=URLIcon, relief=FLAT, bg="#51bd49", command=lambda a="URLs":reference(a))
    URLButton.image = URLIcon
    URLButton.pack(side=TOP)

    separator10 = Separator(rightToolbar, orient=VERTICAL)
    separator10.pack(side=LEFT,fill=Y,pady=3,padx=5)

    # Plan section button, icon and text
    planIcons = Frame(rightToolbar, bg="#51bd49")
    planIcons.pack(side=LEFT,anchor=N)
    planText = Label(planIcons, text="Plan", bg="#51bd49")
    planText.pack(side=TOP)
    planIcon = PhotoImage(file="icons/plan.gif")
    planButton = Button(planIcons, image=planIcon, relief=FLAT, bg="#51bd49", command=plan)
    planButton.image = planIcon
    planButton.pack(side=TOP)

    # This frame will hold all of inner UI content (not toolbars)
    innerFrame = Frame(main)
    innerFrame.pack(side=TOP, anchor=W, fill=BOTH, expand=True, padx=25)

    # This frame is exclusive to the todos and the input bar
    contentFrame = Frame(innerFrame)
    contentFrame.pack(side=LEFT, anchor=N, fill=Y)

    # Instruction frame (instructions and exit button for when removeTodo(), selectTodo() etc. called)
    global instructionFrame
    instructionFrame = Frame(contentFrame)
    instructionFrame.pack(side=TOP,anchor=W,padx=25,pady=0)
    global instructionText
    instructionText = StringVar()
    instructionDisplay = Label(instructionFrame, textvariable=instructionText, fg="red", font=("Segoe UI",16))
    instructionDisplay.pack(side=LEFT)
    global instructionButton
    instructionButton = Button(instructionFrame,text="Done", font=("Segoe UI",16), bg="blue", command=cancel)

    # This is the frame that actually holds all of the todo content
    global todoContent
    todoContent = Frame(contentFrame)
    todoContent.pack(side=TOP,anchor=W,pady=15)

    # Reference book frames
    global rightFrame
    rightFrame = Frame(innerFrame, width=300)
    global referenceButton
    global referenceFrame
    global referenceHeaderText
    referenceButton = Button(rightFrame,text="Close",command=closeReference)
    referenceButton.pack(side=LEFT,anchor=N,padx=(0,5),pady=(5,0))
    referenceFrame = Frame(rightFrame,width=300)
    referenceHeaderText = StringVar()
    referenceHeader = Label(rightFrame, text="Contacts", textvariable=referenceHeaderText, font=("Segoe UI",14)).pack(side=TOP,anchor=W,pady=(0,30))

    # Next / previous buttons, icons and text
    global arrowFrame
    global previousButton
    global nextButton
    arrowFrame = Frame(innerFrame)
    previousIcon = PhotoImage(file="icons/previous.gif")
    previousButton = Button(arrowFrame, image=previousIcon, relief=FLAT, command=previous)
    previousButton.image = previousIcon
    previousButton.pack(side=LEFT,anchor=S)
    global timePeriodText
    timePeriodText = StringVar()
    timePeriodLabel = Label(arrowFrame, textvariable=timePeriodText, font=("Segoe UI",14), pady=13)
    timePeriodText.set("Test")
    timePeriodLabel.pack(side=LEFT,anchor=S)
    nextIcon = PhotoImage(file="icons/next.gif")
    nextButton = Button(arrowFrame, image=nextIcon, relief=FLAT, command=next)
    nextButton.image = nextIcon
    nextButton.pack(side=LEFT,anchor=S)

    # Input bar
    inputFrame = Frame(contentFrame)
    inputFrame.pack(side=BOTTOM, anchor=W,padx=10,pady=25)
    global inputBar
    global inputText
    global inputButton
    inputText = StringVar()
    inputBar = Entry(inputFrame,font=("Segoe UI",14),width=40,bd=3,relief=GROOVE,textvariable=inputText)
    inputBar.pack(side=LEFT)
    inputBar.bind('<Return>', processTodo)

    # Input bar category box
    global categoryList2
    categoryList2 = Combobox(inputFrame, width=10)
    categoryList2['values'] = ('')
    for g in categories:
        categoryList2['values'] += tuple(g)
    categoryList2.pack(side=LEFT,padx=2)
    categoryList2.bind("<Return>",lambda e,inputMethod=2: setCategory(e,inputMethod))
    categoryList2.bind("<<ComboboxSelected>>",lambda e,inputMethod=2: setCategory(e,inputMethod))

    # Input bar date button
    global dateButton2
    dateButton2 = Button(inputFrame, image=dateIcon, relief=FLAT, command=lambda:setDate(2))
    dateButton2.image = dateIcon
    dateButton2.pack(side=LEFT)
    inputIcon = PhotoImage(file="icons/entry.gif")
    inputButton = Button(inputFrame, image=inputIcon, relief=FLAT, command=processTodo)
    inputButton.image = inputIcon
    inputButton.pack(side=LEFT)

    # Date user input box
    global dateInput
    global dateInputText
    dateInputText = StringVar()
    dateInput = Entry(main,width=10,bd=1,relief=SOLID,justify=CENTER,font=("Segoe UI",12),textvariable=dateInputText)

    ## Important variable definitions ##
    global selected
    selected = list()
    global questions
    questions = -1
    global subColumn
    subColumn = 0
    global dateSet
    dateSet = ""
    global sqlDate
    sqlDate = ""
    global dayToBeViewed
    dayToBeViewed = 0
    global weekToBeViewed
    weekToBeViewed = 0
    global todoWidgets
    todoWidgets = list()
    global todoFrames
    todoFrames = list()
    global categoryText
    categoryText = ""
    global categoryFrames
    categoryFrames = list()
    global todoCategories
    todoCategories = list()
    global todoProgress
    todoProgress = list()

    # Set view to general and call general()
    global currentView
    currentView = "general"
    generalView.config(relief=GROOVE)
    general()


# Called by general view button. Set view to general (forget main frame and build general frame)
def general():
    global currentView
    global generalFrame
    if currentView == "sequential":
        sequentialView.config(relief=GROOVE)
    elif currentView == "daily":
        dailyView.config(relief=GROOVE)
    elif currentView == "weekly":
        weeklyView.config(relief=GROOVE)
    elif currentView == "category":
        categoryView.config(relief=GROOVE)
    else:
        longtermView.config(relief=GROOVE)
    generalView.config(relief=SUNKEN)
    main.pack_forget()
    generalFrame.pack(fill=BOTH,expand=True)
    currentView = "general"


# Called by sequential view button. Set view to sequential.
def sequential():
    global currentView
    if currentView == "general":
        generalView.config(relief=GROOVE)
        generalFrame.pack_forget()
        main.pack(side=TOP,anchor=W,fill=Y,expand=True)
    elif currentView == "daily":
        dailyView.config(relief=GROOVE)
    elif currentView == "weekly":
        weeklyView.config(relief=GROOVE)
    elif currentView == "category":
        categoryView.config(relief=GROOVE)
    else:
        longtermView.config(relief=GROOVE)
        global inputBar
        global inputButton
        global selectButton
        global questionButton
        global dateButton
        global dateButton2
        global categoryList
        global categoryList2
        inputButton.config(command=processTodo)
        selectButton.config(state=NORMAL)
        questionButton.config(state=NORMAL)
        dateButton.config(state=NORMAL)
        dateButton2.config(state=NORMAL)
        categoryList.config(state=NORMAL)
        categoryList2.config(state=NORMAL)
        inputBar.bind('<Return>', processTodo)
    sequentialView.config(relief=SUNKEN)
    currentView = "sequential"
    arrowFrame.pack_forget()
    update()


# Called by daily view button. Set view to daily.
def daily():
    global currentView
    if currentView == "general":
        generalView.config(relief=GROOVE)
        generalFrame.pack_forget()
        main.pack(side=TOP,anchor=W,fill=Y,expand=True)
    elif currentView == "sequential":
        sequentialView.config(relief=GROOVE)
    elif currentView == "weekly":
        weeklyView.config(relief=GROOVE)
    elif currentView == "category":
        categoryView.config(relief=GROOVE)
    else:
        longtermView.config(relief=GROOVE)
        global inputBar
        global inputButton
        global selectButton
        global questionButton
        global dateButton
        global dateButton2
        global categoryList
        global categoryList2
        inputButton.config(command=processTodo)
        selectButton.config(state=NORMAL)
        questionButton.config(state=NORMAL)
        dateButton.config(state=NORMAL)
        dateButton2.config(state=NORMAL)
        categoryList.config(state=NORMAL)
        categoryList2.config(state=NORMAL)
        inputBar.bind('<Return>', processTodo)
    dailyView.config(relief=SUNKEN)
    currentView = "daily"
    arrowFrame.pack(side=BOTTOM,anchor=E)
    update()


# Called by weekly view button. Set view to weekly.
def weekly():
    global currentView
    if currentView == "general":
        generalView.config(relief=GROOVE)
        generalFrame.pack_forget()
        main.pack(side=TOP,anchor=W,fill=Y,expand=True)
    elif currentView == "sequential":
        sequentialView.config(relief=GROOVE)
    elif currentView == "daily":
        dailyView.config(relief=GROOVE)
    elif currentView == "category":
        categoryView.config(relief=GROOVE)
    else:
        longtermView.config(relief=GROOVE)
        global inputBar
        global inputButton
        global selectButton
        global questionButton
        global dateButton
        global dateButton2
        global categoryList
        global categoryList2
        inputButton.config(command=processTodo)
        selectButton.config(state=NORMAL)
        questionButton.config(state=NORMAL)
        dateButton.config(state=NORMAL)
        dateButton2.config(state=NORMAL)
        categoryList.config(state=NORMAL)
        categoryList2.config(state=NORMAL)
        inputBar.bind('<Return>', processTodo)
    weeklyView.config(relief=SUNKEN)
    currentView = "weekly"
    arrowFrame.pack(side=BOTTOM,anchor=E)
    update()


# Called by category view button. Set view to category.
def category():
    global currentView
    if currentView == "general":
        generalView.config(relief=GROOVE)
        generalFrame.pack_forget()
        main.pack(side=TOP,anchor=W,fill=Y,expand=True)
    elif currentView == "sequential":
        sequentialView.config(relief=GROOVE)
    elif currentView == "daily":
        dailyView.config(relief=GROOVE)
    elif currentView == "weekly":
        weeklyView.config(relief=GROOVE)
    else:
        longtermView.config(relief=GROOVE)
        global inputBar
        global inputButton
        global selectButton
        global questionButton
        global dateButton
        global dateButton2
        global categoryList
        global categoryList2
        inputButton.config(command=processTodo)
        selectButton.config(state=NORMAL)
        questionButton.config(state=NORMAL)
        dateButton.config(state=NORMAL)
        dateButton2.config(state=NORMAL)
        categoryList.config(state=NORMAL)
        categoryList2.config(state=NORMAL)
        inputBar.bind('<Return>', processTodo)
    categoryView.config(relief=SUNKEN)
    currentView = "category"
    arrowFrame.pack_forget()
    update()


# Called by long term button. Set view to longterm and disable buttons which cannot be used in this view.
def longterm(mode=None):
    global currentView
    global inputButton
    global inputBar
    global selectButton
    global questionButton
    global dateButton
    global dateButton2
    global categoryList
    global categoryList2
    if currentView == "general":
        generalView.config(relief=GROOVE)
        generalFrame.pack_forget()
        main.pack(side=TOP,anchor=W,fill=Y,expand=True)
    elif currentView == "sequential":
        sequentialView.config(relief=GROOVE)
    elif currentView == "daily":
        dailyView.config(relief=GROOVE)
    elif currentView == "category":
        categoryView.config(relief=GROOVE)
    else:
        weeklyView.config(relief=GROOVE)
    longtermView.config(relief=SUNKEN)
    inputButton.config(command=longtermEntered)
    selectButton.config(state=DISABLED)
    questionButton.config(state=DISABLED)
    dateButton.config(state=DISABLED)
    dateButton2.config(state=DISABLED)
    categoryList.config(state=DISABLED)
    categoryList2.config(state=DISABLED)
    inputBar.bind('<Return>', longtermEntered)
    currentView = "longterm"
    arrowFrame.pack_forget()
    update()


# Build log in window and wait for input
root = Tk()
root.withdraw()
initial = Toplevel(root)
initial.title("Prioritree")
initial.geometry("300x350")
logo = PhotoImage(file="icons/small.gif")
logoPack = Label(initial,image=logo)
logoPack.image = logo
logoPack.pack(side=TOP)
Label(initial,text="Prioritree",font=("Segoe UI",32)).pack(side=TOP,pady=0)
Label(initial,text="© Jerome Beckett 2016\n",font=("Segoe UI",11)).pack(side=TOP,pady=0)
userSection = Frame(initial)
userSection.pack(fill=X,pady=(0,5))
Label(userSection,text="Username",width=10).pack(side=LEFT)
global userInput
userInput = Entry(userSection,bg="white")
userInput.pack(fill=X,pady=5,padx=(0,5))
userInput.focus_set()
Button(initial,text="Create / Log in",command=lambda e=None,a=None:assessAccount(e,a)).pack(side=TOP,pady=5)
initial.bind('<Return>', lambda e,a=None:assessAccount(e,a))
initial.mainloop()
