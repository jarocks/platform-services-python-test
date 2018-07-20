from tornado.testing import gen_test
from rewardsservice.test.runtests import BaseTestCases
from pymongo import MongoClient


class CustomersAPITestCase(BaseTestCases.APIResponseTestCase):
    _tests = {
        'get_one': {
            'params': {'email': 'customer1@test.dev'}, 'method': 'GET',
            'msg': {
                "email": "customer1@test.dev",
                "points": 480, "tier": "D",
                "nextTierProgress": 0.96,
                "nextRewardName": "25% off purchase",
                "nextTier": "E",
                "rewardName": "20% off purchase"
            }
        },
        'create_one': {
            'params': {'email': 'newcustomer@test.dev', 'total': 50}, 'method': 'POST',
            'msg': {
                "nextRewardName": "5% off purchase",
                "nextTierProgress": 0.5,
                "nextTier": "A",
                "email": "newcustomer@test.dev",
                "tier": None,
                "rewardName": None,
                "points": 50}
        },
        'update_one': {
            'params': {'email': 'customer3@test.dev', 'total': 250}, 'method': 'PUT',
            'msg': {
                "nextRewardName": "20% off purchase",
                "nextTierProgress": 0.75,
                "nextTier": "D",
                "email": "customer3@test.dev",
                "tier": "C",
                "rewardName": "15% off purchase",
                "points": 300
            }
        },
        'delete_one': {
            'params': {'email': 'customer2@test.dev'}, 'method': 'DELETE',
            'msg': {
                "email": "customer2@test.dev",
                "points": 120, "tier": "A",
                "nextTierProgress": 0.6,
                "nextRewardName": "10% off purchase",
                "rewardName": "5% off purchase",
                "nextTier": "B"
            },
        }
    }

    @gen_test
    def test_get_all(self):
        response = self.fetch()
        self.assertEqual(200, response.code)

    @gen_test
    def test_search(self):
        response = self.fetch({'s': 'customer'})
        self.assertEqual(200, response.code)

        rewards = self.fetch_body(response)
        self.assertEqual(9, len(rewards))

    def setUp(self):
        super().setUp()

        client = MongoClient("mongodb", 27017)
        db = client["Customers"]

        print("Loading customer test data in mongo")
        db.customers.insert_many([
            {
                "email": "customer1@test.dev",
                "points": 480, "tier": "D",
                "nextTierProgress": 0.96,
                "nextRewardName": "25% off purchase",
                "nextTier": "E",
                "rewardName": "20% off purchase"
            },
            {
                "email": "customer2@test.dev",
                "points": 120, "tier": "A",
                "nextTierProgress": 0.6,
                "nextRewardName": "10% off purchase",
                "rewardName": "5% off purchase",
                "nextTier": "B"
            },
            {
                "email": "customer3@test.dev",
                "points": 50,
                "tier": None,
                "nextRewardName": "5% off purchase",
                "rewardName": None,
                "nextTier": "A",
                "nextTierProgress": 0.5
            },
            {
                "email": "customer4@test.dev",
                "points": 500,
                "tier": "E",
                "nextRewardName": "30% off purchase",
                "rewardName": "25% off purchase",
                "nextTier": "F",
                "nextTierProgress": 0.8333333333333334
            },
            {
                "email": "customer5@test.dev",
                "points": 205,
                "tier": "B",
                "nextRewardName": "15% off purchase",
                "rewardName": "10% off purchase",
                "nextTier": "C",
                "nextTierProgress": 0.6833333333333333
            },
            {
                "email": "customer6@test.dev",
                "points": 1000,
                "tier": "J",
                "nextRewardName": "50% off purchase",
                "rewardName": "50% off purchase",
                "nextTier": "J",
                "nextTierProgress": 1.0
            },
            {
                "email": "customer7@test.dev",
                "points": 2000,
                "tier": "J",
                "nextRewardName": "50% off purchase",
                "rewardName": "50% off purchase",
                "nextTier": "J",
                "nextTierProgress": 2.0
            },
            {
                "email": "customer8@test.dev",
                "points": 900,
                "tier": "I",
                "nextRewardName": "50% off purchase",
                "rewardName": "45% off purchase",
                "nextTier": "J",
                "nextTierProgress": 0.9
            },
            {
                "email": "customer9@test.dev",
                "points": 350,
                "tier": "C",
                "nextRewardName": "20% off purchase",
                "rewardName": "15% off purchase",
                "nextTier": "D",
                "nextTierProgress": 0.875
            },
            {
                "email": "astandout@test.dev",
                "points": 750,
                "tier": "G",
                "nextTierProgress": 0.9375,
                "nextRewardName": "40% off purchase",
                "nextTier": "H",
                "rewardName": "35% off purchase"
            }
        ])
        print("Test customer data loaded in mongo")

        client.close()

    def tearDown(self):
        super().tearDown()

        client = MongoClient("mongodb", 27017)
        db = client["Customers"]

        db.customers.delete_many({'email': {'$regex': '.*\@test\.dev'}})


class CustomersAPIErrorTestCase(BaseTestCases.APIErrorTestCase):
    _tests = {
        'customer_not_found': {
            'params': {'email': 'not.a.customer@test.dev'}, 'method': 'GET',
            'code': 404, 'msg': 'No customer found with the email {email}'
        },
        'nothing_to_delete': {
            'params': {'email': 'not.a.customer@test.dev'}, 'method': 'DELETE',
            'code': 400, 'msg': 'No customer found with the email {email}'
        },
        'invalid_email_address': {
            'params': {'email': 'invalid@email'}, 'method': 'GET',
            'code': 400, 'msg': 'Invalid parameter email'
        },
        'invalid_total_amount': {
            'params': {'email': 'invalid@email'}, 'method': 'GET',
            'code': 400, 'msg': 'Invalid parameter email'
        },
    }


class CustomersRewardsTestCase(BaseTestCases.APIResponseTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tests = {}

        responses = [
            {"nextTier": "A", "rewardName": None, "points": 0, "nextTierProgress": 0.0,
             "nextRewardName": "5% off purchase", "email": "newcustomer@test.dev", "tier": None},
            {"email": "newcustomer@test.dev", "rewardName": "5% off purchase", "nextRewardName": "10% off purchase",
             "tier": "A", "points": 100, "nextTierProgress": 0.5, "nextTier": "B"},
            {"email": "newcustomer@test.dev", "rewardName": "10% off purchase", "nextRewardName": "15% off purchase",
             "tier": "B", "points": 200, "nextTierProgress": 0.6666666666666666, "nextTier": "C"},
            {"email": "newcustomer@test.dev", "rewardName": "15% off purchase", "nextRewardName": "20% off purchase",
             "tier": "C", "points": 300, "nextTierProgress": 0.75, "nextTier": "D"},
            {"email": "newcustomer@test.dev", "rewardName": "20% off purchase", "nextRewardName": "25% off purchase",
             "tier": "D", "points": 400, "nextTierProgress": 0.8, "nextTier": "E"},
            {"email": "newcustomer@test.dev", "rewardName": "25% off purchase", "nextRewardName": "30% off purchase",
             "tier": "E", "points": 500, "nextTierProgress": 0.8333333333333334, "nextTier": "F"},
            {"email": "newcustomer@test.dev", "rewardName": "30% off purchase", "nextRewardName": "35% off purchase",
             "tier": "F", "points": 600, "nextTierProgress": 0.8571428571428571, "nextTier": "G"},
            {"email": "newcustomer@test.dev", "rewardName": "35% off purchase", "nextRewardName": "40% off purchase",
             "tier": "G", "points": 700, "nextTierProgress": 0.875, "nextTier": "H"},
            {"email": "newcustomer@test.dev", "rewardName": "40% off purchase", "nextRewardName": "45% off purchase",
             "tier": "H", "points": 800, "nextTierProgress": 0.8888888888888888, "nextTier": "I"},
            {"email": "newcustomer@test.dev", "rewardName": "45% off purchase", "nextRewardName": "50% off purchase",
             "tier": "I", "points": 900, "nextTierProgress": 0.9, "nextTier": "J"},
            {"email": "newcustomer@test.dev", "rewardName": "50% off purchase", "nextRewardName": "50% off purchase",
             "tier": "J", "points": 1000, "nextTierProgress": 1.0, "nextTier": "J"},
        ]

        for i in responses:
            test_code = 'reward_tier_%s' % str(i['tier']).lower()
            tests[test_code] = {'params': {'email': i['email'], 'total': i['points']}, 'method': 'POST', 'msg': i}

        self._tests = tests

    def tearDown(self):
        super().tearDown()

        client = MongoClient("mongodb", 27017)
        db = client["Customers"]

        db.customers.delete_many({'email': {'$regex': '.*\@test\.dev'}})
