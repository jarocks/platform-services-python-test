import json
import math
import re

from pymongo import MongoClient, ASCENDING, DESCENDING
from tornado.gen import coroutine
from tornado.web import RequestHandler, HTTPError


class CustomersHandler(RequestHandler):
    def initialize(self):
        self.client = MongoClient("mongodb", 27017)

    def on_finish(self):
        self.client.close()

    def get_collection(self, name):
        name = name.lower()
        db = self.client.get_database(name.capitalize())

        return db.get_collection(name)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, OPTIONS')

    @coroutine
    def get(self):
        collection = self.get_collection('customers')

        email = self.get_email(False)
        search = self.get_argument('s', None)

        if email:
            customers = collection.find_one({'email': email}, {'_id': 0})

            if not customers:
                raise HTTPError(404, 'No customer found with the email %s' % email)
        elif search:
            customers = list(collection.find({'email': {'$regex': '.*%s.*' % re.escape(search)}}, {'_id': 0}))

        else:
            customers = list(collection.find({}, {'_id': 0}))

        # Force response as json
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(customers))

    @coroutine
    def delete(self):
        email = self.get_email()
        collection = self.get_collection('customers')

        customer = collection.find_one_and_delete({'email': email}, {'_id': 0})

        if not customer:
            raise HTTPError(400, 'No customer found with the email %s' % email)

        self.write(customer)

    @coroutine
    def post(self):
        customer = self._insert_or_replace(self.get_email(), self.get_points())

        self.write(customer)

    @coroutine
    def options(self):
        self.set_status(204)
        self.finish()

    @coroutine
    def put(self):
        email = self.get_email()
        collection = self.get_collection('customers')

        ''' Sum existing points with ones from query args if user exists '''
        customer = collection.find_one({'email': email}, ['points']) or {}
        points = customer.get('points', 0) + self.get_points()

        customer = self._insert_or_replace(email, points)

        self.write(customer)

    def get_email(self, required=True):
        default = self._ARG_DEFAULT if required else ''

        email = self.get_argument('email', default)

        # Check if this is a valid email address format
        matches = re.match('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email)

        if (required or email) and not matches:
            raise InvalidValueError('email')

        return email

    def get_points(self):
        try:
            total = self.get_argument('total')
            return math.floor(abs(float(total)))
        except ValueError:
            raise InvalidValueError('total')

    def write_error(self, status_code, **kwargs):
        self.set_status(status_code, kwargs.get('reason', self._reason))
        self.set_header('Content-Type', 'application/json')

        # Only show additional details for HTTP errors
        if 'exc_info' in kwargs and isinstance(kwargs['exc_info'][1], HTTPError):
            message = str(kwargs['exc_info'][1])
        else:
            message = kwargs.get('reason', self._reason)

        self.finish({'error': {'code': status_code, 'message': message}})

    def _insert_or_replace(self, email, points):
        reward_collection = self.get_collection('rewards')
        rewards = reward_collection.find({}, sort=[('points', ASCENDING)])

        """
        This could just as well be accomplished with database queries (but I don't think that's what you're looking for)

        current_reward = reward_collection.find_one({'points': {'$lte': points}}, sort=[('points', DESCENDING)])
        next_reward = reward_collection.find_one({'points': {'$gt': points}}, sort=[('points', ASCENDING)])
        """

        current_reward = {}
        next_reward = rewards.next()

        while points >= next_reward.get('points', 0):
            try:
                current_reward = next_reward
                next_reward = rewards.next()

            except StopIteration:
                """ 
                Break the loop if we get to the end of the reward tiers

                This lets the api show the highest tier as the next rewards tier for customers in the highest tier,
                the whole idea being that because there's no higher level, progress will be greater than 1.0 or 100%
                """
                break

        ''' Prepare customer object for insertion/update into the db '''
        customer = {
            'email': email,
            'points': points,
            'tier': current_reward.get('tier'),
            'rewardName': current_reward.get('rewardName'),
            'nextTier': next_reward.get('tier'),
            'nextRewardName': next_reward.get('rewardName'),
            'nextTierProgress': points / next_reward.get('points')
        }

        customer_collection = self.get_collection('customers')
        customer_collection.replace_one({'email': email}, customer, True)

        return customer


class InvalidValueError(HTTPError):
    def __init__(self, arg_name):
        super(InvalidValueError, self).__init__(
            400, 'Invalid parameter %s' % arg_name)
        self.arg_name = arg_name