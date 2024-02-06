from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
import os
import re
import pyodata

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
db = SQLAlchemy(app)


# Define the model
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    rating = db.Column(db.Integer)
    is_vegan = db.Column(db.Boolean)
    calories = db.Column(db.Integer)
    description = db.Column(db.String(200))


@app.route('/odata/$metadata', methods=['GET'])
def odata_metadata():
    with open('metadata.xml', 'r') as file:
        metadata_xml = file.read()
    return Response(metadata_xml, mimetype='application/xml')


# POST
@app.route('/odata/MenuItems', methods=['POST'])
def create_menu_item():
    data = request.get_json()
    menu_item = MenuItem(
        name=data['Name'],
        rating=data['Rating'],
        is_vegan=data['isVegan'],
        calories=data['Calories'],
        description=data['Description']
    )
    db.session.add(menu_item)
    db.session.commit()
    response = jsonify({
        "@odata.context": request.url_root + "odata/$metadata#MenuItems/$entity",
        "Id": menu_item.id,
        "Name": menu_item.name,
        "Rating": menu_item.rating,
        "isVegan": menu_item.is_vegan,
        "Calories": menu_item.calories,
        "Description": menu_item.description
    })
    response.status_code = 201
    return response


# GET
@app.route('/odata/MenuItems', methods=['GET'])
def get_menu_items():
    filter_condition = request.args.get('$filter')
    query = MenuItem.query

    if filter_condition:
        match = re.search(r'Calories\s+gt\s+(\d+)', filter_condition)
        if match:
            calories_value = int(match.group(1))
            query = query.filter(MenuItem.calories > calories_value)

    menu_items = query.all()
    menu_items_response = {
        "@odata.context": request.url + "/$metadata#MenuItems",
        "value": [
            {
                "Id": item.id,
                "Name": item.name,
                "Rating": item.rating,
                "isVegan": item.is_vegan,
                "Calories": item.calories,
                "Description": item.description
            }
            for item in menu_items
        ]
    }
    return jsonify(menu_items_response)

# GET BY ID
@app.route('/odata/MenuItems(<int:item_id>)', methods=['GET'])
def get_menu_item(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)
    menu_item_response = {
        "@odata.context": request.url_root + "odata/$metadata#MenuItems/$entity",
        "value": {
            "Id": menu_item.id,
            "Name": menu_item.name,
            "Rating": menu_item.rating,
            "isVegan": menu_item.is_vegan,
            "Calories": menu_item.calories,
            "Description": menu_item.description
        }
    }
    return jsonify(menu_item_response)


# PUT (wedlug specyfikacji salesforce zamiast PUT powinniśmy używać POST)
@app.route('/odata/MenuItems(<int:item_id>)', methods=['POST'])
def update_menu_item(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)
    data = request.get_json()
    updated = False
    if 'Name' in data and data['Name'] != menu_item.name:
        menu_item.name = data['Name']
        updated = True
    if 'Rating' in data and data['Rating'] != menu_item.rating:
        menu_item.rating = data['Rating']
        updated = True
    if 'isVegan' in data and data['isVegan'] != menu_item.is_vegan:
        menu_item.is_vegan = data['isVegan']
        updated = True
    if 'Calories' in data and data['Calories'] != menu_item.calories:
        menu_item.calories = data['Calories']
        updated = True
    if 'Description' in data and data['Description'] != menu_item.description:
        menu_item.description = data['Description']
        updated = True

    if updated:
        db.session.commit()
        return jsonify({
            "@odata.context": request.url_root + "odata/$metadata#MenuItems/$entity",
            "Id": menu_item.id,
            "Name": menu_item.name,
            "Rating": menu_item.rating,
            "isVegan": menu_item.is_vegan,
            "Calories": menu_item.calories,
            "Description": menu_item.description
        })
    else:
        return jsonify({'message': 'No changes made to the menu item'}), 204


# DELETE
@app.route('/odata/MenuItems(<int:item_id>)', methods=['DELETE'])
def delete_menu_item(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)
    db.session.delete(menu_item)
    db.session.commit()
    return '', 204


def create_database(app):
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    create_database(app)
    app.run(port=52999)