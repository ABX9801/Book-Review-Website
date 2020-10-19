#import necessary libraries
import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session,sessionmaker

engine = create_engine('postgres://imowektmwpmarg:863ced98e8498885468ae8318f7765f4ba688fb808dc095be6d6487ba9744d5c@ec2-52-0-155-79.compute-1.amazonaws.com:5432/d9rhdrliov37cm')
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author,year in reader:
        db.execute("INSERT INTO books (isbn, title, author,year) VALUES (:isbn, :title, :author, :year)",{"isbn":isbn,"title":title,"author":author, 'year':year})
        print('Added ',isbn,' : ',title,' by ',author,' published in ',year,'.')
    db.commit()


if __name__=='__main__':
    main()
