from flask import Flask, request, jsonify, render_template
from flask_pymongo import PyMongo
from model import Tag, Tags, Todo, Todos
from bson.objectid import ObjectId
from datetime import datetime

DATETIME_FORMAT = '%a %b %d, %Y'

app = Flask(__name__)
app.config.from_object(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/chrashlist"
mongo = PyMongo(app)
client = mongo.cx

Todos = Todos(collection=client.chrashlist.todos)
Tags = Tags(collection=client.chrashlist.tags)

# ENJOY ALL THESE UTILITY FUNCTIONS HAHAHA

def stringify_id(doc):
    """Stringify ObjectId because flask.jsonify can't handle them."""
    doc['_id'] = str(doc['_id'])
    return doc


def stringify_ids(collection):
    """Stringify a bunch of ObjectIds."""
    return [stringify_id(doc) for doc in collection]


def stringify_datetime(doc):
    time_str = doc.date_created.strftime(DATETIME_FORMAT)
    doc['dateCreated'] = time_str
    return doc


def stringify_datetimes(collection):
    return [stringify_datetime(doc) for doc in collection]


def add_tag_todo(tag, todo):
    """Add todo to tag.todos."""
    mongo.db.tags.find_one_and_update(
        {'name': tag},
        {
            '$addToSet': {'todos':
                {
                    '_id': todo['_id'],
                    'title': todo.title,
                    'author': todo.author,
                    'done': todo.done
                }
            }
        },
        upsert=True
    )


def add_todo_tags(tags, todo):
    """Add tag names to todo.tags"""
    old_tags = todo.get('tags', [])
    todo['tags'] = list(set(old_tags + tags))


@app.route('/')
def index():
    return render_template('Henlo!')

@app.route('/api/todos')
def get_todos():
    """All todos"""
    return jsonify(
        stringify_datetimes(
            stringify_ids(
                Todos.find({})
            )
        )
    )

@app.route('/api/todos/by/<author>')
def get_todos_by_author(author):
    """All todos by author."""
    return jsonify(
        stringify_datetimes(
            stringify_ids(Todos.find_by_author(author))
        )
    )

@app.route('/api/todos/not/done')
def get_todos_not_done():
    return jsonify(
        stringify_datetimes(
            stringify_ids(Todos.find_not_done())
        )
    )


@app.route('/api/todos/done')
def get_todos_done():
    return jsonify(
        stringify_datetimes(
            stringify_ids(Todos.find_done())
        )
    )


@app.route('/api/todo/<ObjectId:id>', methods=['GET', 'POST'])
def get_todo(id):
    """Return a todo."""
    todo = Todos.get_from_id(id)

    if request.method == 'POST':
        data = request.get_json()
        new_title = data.get('title')
        new_desc = data.get('desc')
        done = data.get('done')
        tags = set(data.get('tags'))

        if new_title:
            todo.title = new_title
        if new_desc:
            todo.desc = new_desc
        if done:
            todo.done = not todo.done
        if tags:
            for tag in tags:
                add_tag_todo(tag, todo)
            todo['tags'] = todo['tags'] + tags

        todo.save_partial()
        todo.reload()

    return jsonify(
        stringify_datetime(
            stringify_id(todo)
        )
    )


@app.route('/api/tags')
def get_tags():
    tags = list(Tags.find_all())
    for i, tag in enumerate(tags):
        tag['todos'] = stringify_datetime(stringify_ids(tag.todos))

        tags[i] = stringify_id(tag)

    return jsonify(tags)


@app.route('/api/tag/<name>')
def get_tag(name):
    tag = Tags.find_by_name(name)

    tag['todos'] = stringify_datetimes(stringify_ids(tag.todos))

    return jsonify(stringify_id(tag))


@app.route('/api/add/todo', methods=['POST'])
def add_todo():
    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        author = data.get('author')
        desc = data.get('desc')
        tags = data.get('tags', [])

        if tags:
            id = Todos.add_one(title, author, desc).inserted_id
            todo = Todos.find_by_id(id)
            for tag in tags:
                add_tag_todo(tag, todo)

            add_todo_tags(tags, todo)
            todo.save_partial()
            todo.reload()

        return jsonify(stringify_datetime(stringify_id(todo)))


if __name__ == '__main__':
    app.run(debug=True)

