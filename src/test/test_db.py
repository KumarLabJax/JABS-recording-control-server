"""
Tests related to database availability, creation, and interaction
"""

# This next line disables checking that instance of 'scoped_session'
# has no 'commit' or 'bulk_save_objects' members, The members are there,
# pylint just can't tell
#pylint: disable=E1101

import unittest
from src.test import BaseDBTestCase
from src.app.model.hello_world_model import Hello, HelloSchema


class DbConnectionTest(BaseDBTestCase):
    """ Is the database available ? """

    def test_db(self):
        """ Smoke test """
        with self.engine.connect() as conn:
            self.assertFalse(conn.closed)


class SqlalchemyHelloModelTest(BaseDBTestCase):
    """ Test interacting with the provided sqlalchemy definitions """

    def setUp(self):
        self.common_names = ("Liam", "Noah", "William", "James", "Logan")
        hellos = [Hello(who=name) for name in self.common_names]
        self.session.bulk_save_objects(hellos)
        self.session.commit()

    def test_get_hellos(self):
        """ Test getting back all entries """
        hellos = Hello.query.all()
        self.assertTrue(len(hellos) == 5)
        for hello in hellos:
            serialized = HelloSchema().dump(hello)
            self.assertTrue(serialized.data['who'] in self.common_names)

    def test_get_hello_by_name(self):
        """ Test getting an entry by name """
        hello = Hello.query.filter_by(who=self.common_names[0]).first()
        self.assertTrue(hello is not None)
        self.assertEqual(hello.who, self.common_names[0])

    def test_query_nonexistant_hello(self):
        """ Test that getting by non-existant name has no result """
        hello = Hello.query.filter_by(who="John").first()
        self.assertEqual(hello, None)

    def test_update_hello(self):
        """ Test that an entry change is successful """
        hello = Hello.query.filter_by(who=self.common_names[2]).first()
        hello.who = "Bill"
        self.session.commit()
        hello_bill = Hello.query.filter_by(who="Bill").first()
        self.assertEqual(hello_bill.who, "Bill")

    def test_delete_model(self):
        """ Test that the entry can be deleted """
        Hello.query.delete()
        self.session.commit()
        hellos = Hello.query.all()
        self.assertEqual(len(hellos), 0)

    def tearDown(self):
        Hello.query.delete()
        self.session.commit()
        self.session.remove()


if __name__ == '__main__':
    unittest.main()
