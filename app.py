from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
import time
import logging
from flask_cors import CORS, cross_origin

import flask_cors

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret' # change this is real life
#app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
#app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
#app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'c592f1021c00b6'
app.config['MAIL_PASSWORD'] = 'bc33173641277e'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)
CORS(app)
cors= CORS(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass= 3.258e23,
                     radius=1516,
                     distance=35.98e6,
                     image='https://solarsystem.nasa.gov/resources/2266/mercurys-caloris-basin/?category=planets_mercury'
                     )
    venus = Planet(planet_name='Venus',
                     planet_type='Class K',
                     home_star='Sol',
                     mass=4.867e24,
                     radius=3760,
                     distance=67.24e6,
                     image='https://upload.wikimedia.org/wikipedia/commons/0/08/Venus_from_Mariner_10.jpg')
    earth = Planet(planet_name='Earth',
                     planet_type='Class M',
                     home_star='Sol',
                     mass=5.672e24,
                     radius=3959,
                     distance=92.96e6,
                     image='https://www.google.com/search?q=image+of+earth+planet&rlz=1C1VDKB_enIE948IE948&tbm=isch&source=iu&ictx=1&fir=87JUKbprWQ1F_M%252CEPjTXK9YhRjo5M%252C_&vet=1&usg=AI4_-kR7DiNUmAjN0q0Wa7y-mV1xC4QNYg&sa=X&ved=2ahUKEwj0557D063xAhWIOcAKHTVFAZcQ9QF6BAgIEAE#imgrc=87JUKbprWQ1F_M')
    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='James',
                     last_name='Ahern',
                     email='test@test.com',
                     password='password')
    db.session.add(test_user)
    db.session.commit()
    print('Database seeded')


@app.route('/')
def hello_world():
    return 'Hello from the Home Page!!!!!'


@app.route('/super_simple')
def super_simple():
    return jsonify(message='hello from the planetary API')


@app.route('/not_found')
def not_found():
    return jsonify(message="That resource was not found"), 404


@app.route('/parameters')
def parameters():
    name = request.args.get("name")
    age = int(request.args.get("age"))
    if age < 18:
        return jsonify(message="Sorry " + name + " you are not old enough"), 401
    else:
        return jsonify(message="Welcome " + name + " you are old enough")


@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if age < 18:
        return jsonify(message="Sorry " + name + " you are not old enough"), 401
    else:
        return jsonify(message="Welcome " + name + " you are old enough")


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)


@app.route('/users', methods=['GET'])
def users():
    user_list = User.query.all()
    result = users_schema.dump(user_list)
    return jsonify(result)


@app.route('/register', methods=['POST','OPTIONS'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
#@cross_origin(allow_headers=['Content-Type', 'Authorization'])
def register(self):
    self.set_header("Allow-Control-Allow-Origin", "*")
    print(f"Served successfully")
    email = request.form['email']
    print("whats in email:" + email)
    check_email_exists = User.query.filter_by(email=email).first()
    if check_email_exists:
        return jsonify(message='That email already exists. '), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        print("What is being caught " + email, first_name, last_name, password)
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        logging.info("What error is being captured here")
        return jsonify(message=first_name + ' was created successfully as a new User. '), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded!.', access_token=access_token)
    else:
        return jsonify(message='Incorrect email address or password'), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('your planetary Api password is ' + user.password,
                      sender='admin@plantery-api.com',
                      recipients=[email])
        mail.send(msg)
        return jsonify(message='Password sent to ' + email)
    else:
        return jsonify(message="That email doesn't exist"), 401


@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify(message="That planet does not exist"), 404


@app.route('/add_planet', methods=['POST'])
#@jwt_required()
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify(message="There is already a planet by that name "), 409
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])
        image = request.form['image']

        new_planet = Planet(planet_name=planet_name,
                            planet_type=planet_type,
                            home_star=home_star,
                            mass=mass,
                            radius=radius,
                            distance=distance,
                            image=image)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message="You have added a new planet"), 201


@app.route('/update_planet', methods=['PUT'])
#@jwt_required()
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star = request.form['home_star']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        planet.image = request.form['image']
        db.session.commit()
        return jsonify(message="You updated a planet"), 202
    else:
        return jsonify(message="That planet does not exist "), 404


@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
#@jwt_required()
def remove_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="You have deleted a planet  "), 202
    else:
        return jsonify(message="That planet does not exist."), 404


@app.route('/remove_user/<int:id>', methods=['DELETE'])
#@jwt_required()
def remove_user(id: int):
    user = User.query.filter_by(id=id).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(message="You have deleted a user  "), 202
    else:
        return jsonify(message="That user does not exist."), 404


@app.route('/time')
def get_current_time():
    return {'time': time.time()}

# database models


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)
    image = Column(String)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass','radius', 'distance', 'image')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.run()
