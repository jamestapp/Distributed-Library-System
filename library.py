from Pyro5.api import expose, behavior, serve, Daemon
import datetime

@expose
@behavior(instance_mode="single")
class library(object):
    def __init__(self):
        self.users = {}
        # format username: number

        self.authors = {}
        # format name: genre
        
        self.books = {}
        # format booktitle: {copies: x, author: y} 
        # this seems to be ideal format as we must identify books by title (which is unique)
        
        self.loans = {}
        # this is only for active loans
        # format (username, booktitle): dateloaned
        
        self.past_loans = []
        # format {username:x, title: y, start: w, end: z}
        # must be a list due to lack of uniqueness constraint

    @staticmethod
    # method takes a list of lists with a header, and outputs a string that can be printed by the end user
    # l is the list of lists, header is a header with the same length as every list 
    def tabulate(l, header):
        l.insert(0, header)
        # insert the provided header so as to more easily measure the max width of each column including header
        rowWidths = [max([len(str(row[col])) for row in l]) for col in range(len(header))]
        # variable stores all the max widths for each row
        table = [[str(row[col]).ljust(rowWidths[col]) for col in range(len(header))] for row in l]
        # variable is the string formatted data from the list of lists in a new list of lists of justified strings
        l.pop(0)
        # remove the header from the table, otherwise this will affect the rest of the program data
        horizontalBorder = "\n+-" + "-+-".join([width*"-" for width in rowWidths]) + "-+\n"
        "-"*(sum(rowWidths) + 3*(len(rowWidths)-1) + 2) + "+\n"
        # variable stores a formatted horizontal border to be put at the top, bottom, and in between the header and table data
        tableHeader = "".join(["| " + " | ".join(table.pop(0)) + " |"])
        tableData = "\n".join(["| " + " | ".join(row) + " |" for row in table])
        return horizontalBorder + tableHeader + horizontalBorder + tableData + horizontalBorder
        # returns a formatted table of data

    # function adds a user to the users dictionary
    def add_user(self, user_name, user_number):
        self.users[user_name]=user_number

    # function returns a list of all users currently stored in the system
    def return_users(self):
        return self.tabulate([[u, self.users[u]] for u in self.users], ["USERNAME", "NUMBER"])

    # function adds an author to the authors dictionary
    def add_author(self, author_name, author_genre):
        self.authors[author_name]=author_genre

    # function returns a list of all authors stored in the system
    def return_authors(self):
        return self.tabulate([[auth, self.authors[auth]] for auth in self.authors], ["NAME", "GENRE"])
    
    # function adds a book copy to the books dictionary
    # if book already in system, increment copies field by 1, otherwise create new book
    def add_book_copy(self, author_name, book_title):        
        if book_title in self.books.keys():
            self.books[book_title]['copies'] += 1
        else:
            self.books[book_title] = {'copies': 1, 'author': author_name}
        # in this dictionary copies is the number of books currently available to loan, not those already out on loan

    # function returns a list of all books currently not on loan, with the number of copies available
    # provided the number of copies is greater than 1
    def return_books_not_loan(self):
        return self.tabulate([[b, self.books[b]['author'], self.books[b]['copies']] for b in self.books.keys() if self.books[b]['copies'] > 0], ["TITLE", "AUTHOR", "COPIES"])

    # function loans a book to a user, adding an entry to the loans dictionary
    def loan_book(self, user_name, book_title, year, month, day):
        if book_title in self.books.keys() and self.books[book_title]['copies'] > 0:
            self.loans[(user_name, book_title)] = datetime.datetime(year, month, day)
            self.books[book_title]["copies"] -= 1
            return 1
        else:
            return 0
        
    # function returns a list of which books are currently out on loan
    def return_books_loan(self):
        return self.tabulate([[loan[1], self.books[loan[1]]["author"]] for loan in self.loans.keys()], ["TITLE", "AUTHOR"])

    # function returns a book from a loan, adds a past loans record to the past_loans list, and deletes the loan dictionary entry
    def end_book_loan(self, user_name, book_title, year, month, day):
        self.books[book_title]["copies"] += 1
        self.past_loans.append({"username": user_name, "title": book_title, "start": self.loans[(user_name, book_title)], "end": datetime.datetime(year, month, day)})
        del self.loans[(user_name, book_title)]

    # function removes all unloaned copies of a book from the books dictionary
    # if there are copies of the book out on loan we set the number of copies to 0, otherwise we delete from the dictionary
    def delete_book(self, book_title):
        if book_title in [loan[1] for loan in self.loans.keys()]:
            self.books[book_title]["copies"] = 0
        else:
            del self.books[book_title]

    # delete a user from the users dictionary, so long as they have no active or past loans
    def delete_user(self, user_name):
        if user_name not in [loan[0] for loan in self.loans.keys()] and user_name not in [loan["username"] for loan in self.past_loans]:
            del self.users[user_name]
            return 1
        else:
            return 0

    # return a list of book titles that a specified user has loaned between a specified loan start and return date
    def user_loans_date(self, user_name, start_year, start_month, start_day, end_year, end_month, end_day):
        startDate = datetime.datetime(start_year, start_month, start_day)
        endDate = datetime.datetime(end_year, end_month, end_day)
        return self.tabulate([[loan["title"]] for loan in self.past_loans if loan["start"] >= startDate and loan["end"] <= endDate and loan["username"] == user_name],["TITLE"])

daemon = Daemon()
serve({library: "example.library"}, daemon=daemon, use_ns=True)

# references 
# Dictionary.keys(): W3 Schools. 2023. Python - List Comprehension. Available at: https://www.w3schools.com/python/ref_dictionary_keys.asp [Accessed 24 March 2023]
# List comprehension: W3 Schools. 2023. Python - List Comprehension. Available at: https://www.w3schools.com/python/python_lists_comprehension.asp [Accessed 27 March 2023]
# Pyro5: Corcoran, P. 2023. Remote Objects Practical, warehouse. [Python]. Available at: https://learningcentral.cf.ac.uk/bbcswebdav/pid-6975358-dt-content-rid-31117202_2/xid-31117202_2. [Accessed: 24 March 2023]