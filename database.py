

from sqlalchemy import func

from filesystem import app, config
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime, timedelta
import hashlib
import os

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://{user}:{password}@{host}/{database}'.format(**config.localdb)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from sqlalchemy.orm import class_mapper

from sqlalchemy import and_, or_

def GetPassword(value):
    m = hashlib.md5()
    m.update(value.encode("utf-8"))
    return m.hexdigest()


db = SQLAlchemy(app)


def asdict(obj):
    return dict((col.name, getattr(obj, col.name))
                for col in class_mapper(obj.__class__).mapped_table.c)


DepartmentList = db.Table('DepartmentList',
                           db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                           db.Column('department_id', db.Integer, db.ForeignKey('department.id'))
                         )

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    userlevel = db.Column(db.Integer, default=1)
    displayname = db.Column(db.String(255))
    accountname = db.Column(db.String(255))
    phone = db.Column(db.String(255), default=None)
    organization = db.Column(db.String(255), default=None)
    firstname = db.Column(db.String(255), default=None)
    lastname = db.Column(db.String(255), default=None)
    thumbnailphoto = db.Column(db.Text, default=None)
    title = db.Column(db.String(255), default=None)
    physicaldeliveryofficename = db.Column(db.String(255), default=None)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    lastupdated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=db.func.now())
    departments = db.relationship('Department', secondary=DepartmentList,
                                  back_populates='allUsers', lazy='dynamic')

    def getSignedMessages(self):
        return [x.message for x in MessageConfirmed.query.filter_by(user=self.id).all()]

    def Simple(self):
        return {
            'id': self.id,
            'accountname': self.accountname,
            'displayname': self.displayname
        }

    def General(self):
        return {
            'id': self.id,
            'accountname': self.accountname,
            'displayname': self.displayname,
            'phone': self.phone,
            'email': self.email
        }

    def count(self):
        return db.session(func.count())

    def __repr__(self):
        return '<Users %r:%r>' % (self.id, self.userlevel)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(255))
    allUsers = db.relationship('Users', secondary=DepartmentList, back_populates='departments', lazy='dynamic')
    calendars = db.relationship('Calendar',
                                  secondary=CalendarDepartments,
                                  back_populates='departments',
                                  lazy='dynamic')

    def __init__(self, department):
        self.department = department
        if not os.path.exists(config.path + department):
            os.makedirs(config.path + department)

    def Simple(self):
        return {
            'id': self.id,
            'department': self.department
        }

    def folders(self):
        randomFolders = [".DS_Store"]
        return [x for x in os.listdir(config.path + self.department + "/") if x not in randomFolders]

    def add_folder(self, name):
        name = name.replace(".", "")
        if not os.path.exists(config.path + self.department + "/" + name):
            os.makedirs(config.path + self.department + "/" + name)
        return os.listdir(config.path + self.department + "/" + name)

    def read_folder(self, name):
        return os.listdir(config.path + self.department + "/" + name)

    def read_files(self, dir):
        if dir == "":
            return os.listdir(config.path + self.department + "/")
        else:
            for root, dirs, files in os.walk(config.path + self.department + "/" + dir, topdown=False):
                return files

    def count(self):
        return db.session(func.count())

    def __repr__(self):
        return '<Department %r:%r>' % (self.id, self.department)

if __name__ == "__main__":
    db.create_all()
    db.session.commit()