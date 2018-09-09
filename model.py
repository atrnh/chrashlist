from mongokat import Collection, Document
import bson
from datetime import datetime

class Tag(Document):
    use_dot_notation = True
    use_autorefs = True

    structure = {
        'name': str,
        'todos': [
            {
                'id': bson.objectid.ObjectId,
                'title': str,
                'author': str,
                'done': bool,
            }
        ],
    }

    required = ['name']

    @property
    def name(self):
        return self['name']

    @property
    def todos(self):
        return self.get('todos', [])


class Tags(Collection):
    document_class = Tag

    def add_one(self, name):
        return self.update(
            {'name': name},
            {'$setOnInsert': {'name': name}},
            upsert=True
        )

    def find_by_name(self, name):
        return self.find_one({'name': name})

    def find_all(self):
        return self.find({})


class Todo(Document):
    __collection__ = 'todos'
    __database__ = 'chrashlist'

    use_dot_notation = True
    use_autorefs = True

    structure = {
        'title': str,
        'desc': str,
        'author': str,
        'date_created': datetime,
        'done': bool,
        'tags': [str]
    }
    required = ['title', 'author', 'date_created']

    @property
    def _id(self):
        return self['_id']

    @property
    def title(self):
        return self['title']

    @title.setter
    def title(self, title):
        self['title'] = title

    @property
    def desc(self):
        return self['desc']

    @desc.setter
    def desc(self, desc):
        self['desc'] = desc

    @property
    def author(self):
        return self['author']

    @property
    def date_created(self):
        return self['date_created']

    @property
    def done(self):
        return self['done']

    @done.setter
    def done(self, done):
        self['done'] = done

    def _baby_obj(self):
        return {
            '_id': self['_id'],
            'title': self.title,
            'author': self.author,
            'done': self.done
        }


class Todos(Collection):
    document_class = Todo

    def find_by_author(self, author, json=False):
        return self.find({'author': author})

    def find_not_done(self):
        return self.find({'done': False})

    def find_done(self):
        return self.find({'done': True})

    def find_all(self):
        return self.find({})

    def add_one(self, title, author, desc=None):
        return self.insert_one({
            'title': title,
            'author': author,
            'desc': desc,
            'date_created': datetime.utcnow(),
            'done': False,
            'tags': []
        })


if __name__ == '__main__':
    from pymongo import MongoClient
    client = MongoClient()
    Todos = Todos(collection=client.chrashlist.todos)
    Tags = Tags(collection=client.chrashlist.tags)
