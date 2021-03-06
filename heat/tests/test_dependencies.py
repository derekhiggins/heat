# vim: tabstop=4 shiftwidth=4 softtabstop=4

#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import testtools

from heat.engine.dependencies import Dependencies
from heat.engine.dependencies import CircularDependencyException


class dependenciesTest(testtools.TestCase):

    def _dep_test(self, func, checkorder, deps):
        nodes = set.union(*[set(e) for e in deps])

        d = Dependencies(deps)
        order = list(func(d))

        for n in nodes:
            self.assertTrue(n in order, '"%s" is not in the sequence' % n)
            self.assertEqual(order.count(n), 1)

        self.assertEqual(len(order), len(nodes))

        for l, f in deps:
            checkorder(order.index(f), order.index(l))

    def _dep_test_fwd(self, *deps):
        def assertLess(a, b):
            self.assertTrue(a < b,
                            '"%s" is not less than "%s"' % (str(a), str(b)))
        self._dep_test(iter, assertLess, deps)

    def _dep_test_rev(self, *deps):
        def assertGreater(a, b):
            self.assertTrue(a > b,
                            '"%s" is not greater than "%s"' % (str(a), str(b)))
        self._dep_test(reversed, assertGreater, deps)

    def test_repr(self):
        dp = Dependencies([('1', None), ('2', '3'), ('2', '4')])
        s = "Dependencies([('1', None), ('2', '3'), ('2', '4')])"
        self.assertEqual(repr(dp), s)

    def test_single_node(self):
        d = Dependencies([('only', None)])
        l = list(iter(d))
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0], 'only')

    def test_disjoint(self):
        d = Dependencies([('1', None), ('2', None)])
        l = list(iter(d))
        self.assertEqual(len(l), 2)
        self.assertTrue('1' in l)
        self.assertTrue('2' in l)

    def test_single_fwd(self):
        self._dep_test_fwd(('second', 'first'))

    def test_single_rev(self):
        self._dep_test_rev(('second', 'first'))

    def test_chain_fwd(self):
        self._dep_test_fwd(('third', 'second'), ('second', 'first'))

    def test_chain_rev(self):
        self._dep_test_rev(('third', 'second'), ('second', 'first'))

    def test_diamond_fwd(self):
        self._dep_test_fwd(('last', 'mid1'), ('last', 'mid2'),
                           ('mid1', 'first'), ('mid2', 'first'))

    def test_diamond_rev(self):
        self._dep_test_rev(('last', 'mid1'), ('last', 'mid2'),
                           ('mid1', 'first'), ('mid2', 'first'))

    def test_complex_fwd(self):
        self._dep_test_fwd(('last', 'mid1'), ('last', 'mid2'),
                           ('mid1', 'mid3'), ('mid1', 'first'),
                           ('mid3', 'first'), ('mid2', 'first'))

    def test_complex_rev(self):
        self._dep_test_rev(('last', 'mid1'), ('last', 'mid2'),
                           ('mid1', 'mid3'), ('mid1', 'first'),
                           ('mid3', 'first'), ('mid2', 'first'))

    def test_many_edges_fwd(self):
        self._dep_test_fwd(('last', 'e1'), ('last', 'mid1'), ('last', 'mid2'),
                           ('mid1', 'e2'), ('mid1', 'mid3'),
                           ('mid2', 'mid3'),
                           ('mid3', 'e3'))

    def test_many_edges_rev(self):
        self._dep_test_rev(('last', 'e1'), ('last', 'mid1'), ('last', 'mid2'),
                           ('mid1', 'e2'), ('mid1', 'mid3'),
                           ('mid2', 'mid3'),
                           ('mid3', 'e3'))

    def test_dbldiamond_fwd(self):
        self._dep_test_fwd(('last', 'a1'), ('last', 'a2'),
                           ('a1', 'b1'), ('a2', 'b1'), ('a2', 'b2'),
                           ('b1', 'first'), ('b2', 'first'))

    def test_dbldiamond_rev(self):
        self._dep_test_rev(('last', 'a1'), ('last', 'a2'),
                           ('a1', 'b1'), ('a2', 'b1'), ('a2', 'b2'),
                           ('b1', 'first'), ('b2', 'first'))

    def test_circular_fwd(self):
        d = Dependencies([('first', 'second'),
                          ('second', 'third'),
                          ('third', 'first')])
        self.assertRaises(CircularDependencyException, list, iter(d))

    def test_circular_rev(self):
        d = Dependencies([('first', 'second'),
                          ('second', 'third'),
                          ('third', 'first')])
        self.assertRaises(CircularDependencyException, list, reversed(d))

    def test_self_ref(self):
        d = Dependencies([('node', 'node')])
        self.assertRaises(CircularDependencyException, list, iter(d))

    def test_complex_circular_fwd(self):
        d = Dependencies([('last', 'e1'), ('last', 'mid1'), ('last', 'mid2'),
                          ('mid1', 'e2'), ('mid1', 'mid3'),
                          ('mid2', 'mid3'),
                          ('mid3', 'e3'),
                          ('e3', 'mid1')])
        self.assertRaises(CircularDependencyException, list, iter(d))

    def test_complex_circular_rev(self):
        d = Dependencies([('last', 'e1'), ('last', 'mid1'), ('last', 'mid2'),
                          ('mid1', 'e2'), ('mid1', 'mid3'),
                          ('mid2', 'mid3'),
                          ('mid3', 'e3'),
                          ('e3', 'mid1')])
        self.assertRaises(CircularDependencyException, list, reversed(d))

    def test_noexist_partial(self):
        d = Dependencies([('foo', 'bar')])
        get = lambda i: d[i]
        self.assertRaises(KeyError, get, 'baz')

    def test_single_partial(self):
        d = Dependencies([('last', 'first')])
        p = d['last']
        l = list(iter(p))
        self.assertEqual(len(l), 1)
        self.assertEqual(l[0], 'last')

    def test_simple_partial(self):
        d = Dependencies([('last', 'middle'), ('middle', 'first')])
        p = d['middle']
        order = list(iter(p))
        self.assertEqual(len(order), 2)
        for n in ('last', 'middle'):
            self.assertTrue(n in order,
                            "'%s' not found in dependency order" % n)
        self.assertTrue(order.index('last') > order.index('middle'))

    def test_simple_multilevel_partial(self):
        d = Dependencies([('last', 'middle'),
                          ('middle', 'target'),
                          ('target', 'first')])
        p = d['target']
        order = list(iter(p))
        self.assertEqual(len(order), 3)
        for n in ('last', 'middle', 'target'):
            self.assertTrue(n in order,
                            "'%s' not found in dependency order" % n)

    def test_complex_partial(self):
        d = Dependencies([('last', 'e1'), ('last', 'mid1'), ('last', 'mid2'),
                          ('mid1', 'e2'), ('mid1', 'mid3'),
                          ('mid2', 'mid3'),
                          ('mid3', 'e3')])
        p = d['mid3']
        order = list(iter(p))
        self.assertEqual(len(order), 4)
        for n in ('last', 'mid1', 'mid2', 'mid3'):
            self.assertTrue(n in order,
                            "'%s' not found in dependency order" % n)
