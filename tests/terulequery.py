# Copyright 2014, Tresys Technology, LLC
#
# This file is part of SETools.
#
# SETools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# SETools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SETools.  If not, see <http://www.gnu.org/licenses/>.
#
import unittest

from libapol import SELinuxPolicy
from libapol.terulequery import TERuleQuery
from libapol.policyrep.rule import RuleNotConditional


class TERuleQueryTest(unittest.TestCase):

    def setUp(self):
        self.p = SELinuxPolicy("tests/terulequery.conf")

    def test_000_unset(self):
        """TE rule query with no criteria."""
        # query with no parameters gets all TE rules.
        for numrules, r in enumerate(self.p.terules(), start=1):
            pass

        q = TERuleQuery(self.p)
        for q_numrules, r in enumerate(q.results(), start=1):
            pass

        self.assertEqual(numrules, q_numrules)

    def test_001_source_direct(self):
        """TE rule query with exact, direct, source match."""
        q = TERuleQuery(
            self.p, source="test1a", source_indirect=False, source_regex=False)

        # manually consume the generator:
        rules = q.results()
        r = rules.next()

        self.assertEqual(r.ruletype, "allow")
        self.assertEqual(r.source, "test1a")
        self.assertEqual(r.target, "test1t")
        self.assertEqual(r.tclass, "infoflow")
        self.assertSetEqual(set(["hi_w"]), r.perms)
        self.assertRaises(RuleNotConditional, getattr, r, "conditional")

        self.assertRaises(StopIteration, rules.next)

    def test_002_source_indirect(self):
        """TE rule query with exact, indirect, source match."""
        q = TERuleQuery(
            self.p, source="test2s", source_indirect=True, source_regex=False)

        # manually consume the generator:
        rules = q.results()
        r = rules.next()

        self.assertEqual(r.ruletype, "allow")
        self.assertEqual(r.source, "test2a")
        self.assertEqual(r.target, "test2t")
        self.assertEqual(r.tclass, "infoflow")
        self.assertSetEqual(set(["hi_w"]), r.perms)
        self.assertRaises(RuleNotConditional, getattr, r, "conditional")

        self.assertRaises(StopIteration, rules.next)

    def test_003_source_direct_regex(self):
        """TE rule query with regex, direct, source match."""
        q = TERuleQuery(
            self.p, source="test3a.*", source_indirect=False, source_regex=True)

        # manually consume the generator:
        rules = q.results()
        r = rules.next()

        self.assertEqual(r.ruletype, "allow")
        self.assertEqual(r.source, "test3aS")
        self.assertEqual(r.target, "test3t")
        self.assertEqual(r.tclass, "infoflow")
        self.assertSetEqual(set(["low_r"]), r.perms)
        self.assertRaises(RuleNotConditional, getattr, r, "conditional")

        self.assertRaises(StopIteration, rules.next)

    def test_004_source_indirect_regex(self):
        """TE rule query with regex, indirect, source match."""
        q = TERuleQuery(
            self.p, source="test4(s|t)", source_indirect=True, source_regex=True)

        # manually consume the generator:
        r = sorted(q.results())
        self.assertEqual(len(r), 2)

        # verify first rule
        self.assertEqual(r[0].ruletype, "allow")
        self.assertEqual(r[0].source, "test4a1")
        self.assertEqual(r[0].target, "test4a1")
        self.assertEqual(r[0].tclass, "infoflow")
        self.assertSetEqual(set(["hi_w"]), r[0].perms)
        self.assertRaises(RuleNotConditional, getattr, r[0], "conditional")

        # verify second rule
        self.assertEqual(r[1].ruletype, "allow")
        self.assertEqual(r[1].source, "test4a2")
        self.assertEqual(r[1].target, "test4a2")
        self.assertEqual(r[1].tclass, "infoflow")
        self.assertSetEqual(set(["low_r"]), r[1].perms)
        self.assertRaises(RuleNotConditional, getattr, r[1], "conditional")

    def test_005_target_direct(self):
        """TE rule query with exact, direct, target match."""
        q = TERuleQuery(
            self.p, target="test5a", target_indirect=False, target_regex=False)

        # manually consume the generator:
        rules = q.results()
        r = rules.next()

        self.assertEqual(r.ruletype, "allow")
        self.assertEqual(r.source, "test5s")
        self.assertEqual(r.target, "test5a")
        self.assertEqual(r.tclass, "infoflow")
        self.assertSetEqual(set(["hi_w"]), r.perms)
        self.assertRaises(RuleNotConditional, getattr, r, "conditional")

        self.assertRaises(StopIteration, rules.next)

    def test_006_target_indirect(self):
        """TE rule query with exact, indirect, target match."""
        q = TERuleQuery(
            self.p, target="test6t", target_indirect=True, target_regex=False)

        # manually consume the generator:
        r = sorted(q.results())
        self.assertEqual(len(r), 2)

        # verify first rule
        self.assertEqual(r[0].ruletype, "allow")
        self.assertEqual(r[0].source, "test6s")
        self.assertEqual(r[0].target, "test6a")
        self.assertEqual(r[0].tclass, "infoflow")
        self.assertSetEqual(set(["hi_w"]), r[0].perms)
        self.assertRaises(RuleNotConditional, getattr, r[0], "conditional")

        # verify second rule
        self.assertEqual(r[1].ruletype, "allow")
        self.assertEqual(r[1].source, "test6s")
        self.assertEqual(r[1].target, "test6t")
        self.assertEqual(r[1].tclass, "infoflow")
        self.assertSetEqual(set(["low_r"]), r[1].perms)
        self.assertRaises(RuleNotConditional, getattr, r[1], "conditional")

    def test_007_target_direct_regex(self):
        """TE rule query with regex, direct, target match."""
        q = TERuleQuery(
            self.p, target="test7a.*", target_indirect=False, target_regex=True)

        # manually consume the generator:
        rules = q.results()
        r = rules.next()

        self.assertEqual(r.ruletype, "allow")
        self.assertEqual(r.source, "test7s")
        self.assertEqual(r.target, "test7aPASS")
        self.assertEqual(r.tclass, "infoflow")
        self.assertSetEqual(set(["low_r"]), r.perms)
        self.assertRaises(RuleNotConditional, getattr, r, "conditional")

        self.assertRaises(StopIteration, rules.next)

    def test_008_target_indirect_regex(self):
        """TE rule query with regex, indirect, target match."""
        q = TERuleQuery(
            self.p, target="test8(s|t)", target_indirect=True, target_regex=True)

        # manually consume the generator:
        r = sorted(q.results())
        self.assertEqual(len(r), 2)

        # verify first rule
        self.assertEqual(r[0].ruletype, "allow")
        self.assertEqual(r[0].source, "test8a1")
        self.assertEqual(r[0].target, "test8a1")
        self.assertEqual(r[0].tclass, "infoflow")
        self.assertSetEqual(set(["hi_w"]), r[0].perms)
        self.assertRaises(RuleNotConditional, getattr, r[0], "conditional")

        # verify second rule
        self.assertEqual(r[1].ruletype, "allow")
        self.assertEqual(r[1].source, "test8a2")
        self.assertEqual(r[1].target, "test8a2")
        self.assertEqual(r[1].tclass, "infoflow")
        self.assertSetEqual(set(["low_r"]), r[1].perms)
        self.assertRaises(RuleNotConditional, getattr, r[1], "conditional")

    def test_009_class(self):
        """TE rule query with exact object class match."""
        q = TERuleQuery(self.p, tclass="infoflow2", tclass_regex=False)

        # manually consume the generator:
        rules = q.results()
        r = rules.next()

        self.assertEqual(r.ruletype, "allow")
        self.assertEqual(r.source, "test9")
        self.assertEqual(r.target, "test9")
        self.assertEqual(r.tclass, "infoflow2")
        self.assertSetEqual(set(["super_w"]), r.perms)
        self.assertRaises(RuleNotConditional, getattr, r, "conditional")

        self.assertRaises(StopIteration, rules.next)

    def test_010_class_list(self):
        """TE rule query with object class list match."""
        q = TERuleQuery(
            self.p, tclass=["infoflow3", "infoflow4"], tclass_regex=False)

        # manually consume the generator:
        r = sorted(q.results())
        self.assertEqual(len(r), 2)

        # verify first rule
        self.assertEqual(r[0].ruletype, "allow")
        self.assertEqual(r[0].source, "test10")
        self.assertEqual(r[0].target, "test10")
        self.assertEqual(r[0].tclass, "infoflow3")
        self.assertSetEqual(set(["null"]), r[0].perms)
        self.assertRaises(RuleNotConditional, getattr, r[0], "conditional")

        # verify second rule
        self.assertEqual(r[1].ruletype, "allow")
        self.assertEqual(r[1].source, "test10")
        self.assertEqual(r[1].target, "test10")
        self.assertEqual(r[1].tclass, "infoflow4")
        self.assertSetEqual(set(["hi_w"]), r[1].perms)
        self.assertRaises(RuleNotConditional, getattr, r[1], "conditional")

    def test_011_class_regex(self):
        """TE rule query with object class regex match."""
        q = TERuleQuery(self.p, tclass="infoflow(5|6)", tclass_regex=True)

        # manually consume the generator:
        r = sorted(q.results())
        self.assertEqual(len(r), 2)

        # verify first rule
        self.assertEqual(r[0].ruletype, "allow")
        self.assertEqual(r[0].source, "test11")
        self.assertEqual(r[0].target, "test11")
        self.assertEqual(r[0].tclass, "infoflow5")
        self.assertSetEqual(set(["low_w"]), r[0].perms)
        self.assertRaises(RuleNotConditional, getattr, r[0], "conditional")

        # verify second rule
        self.assertEqual(r[1].ruletype, "allow")
        self.assertEqual(r[1].source, "test11")
        self.assertEqual(r[1].target, "test11")
        self.assertEqual(r[1].tclass, "infoflow6")
        self.assertSetEqual(set(["med_r"]), r[1].perms)
        self.assertRaises(RuleNotConditional, getattr, r[1], "conditional")

    def test_012_perms_any(self):
        """TE rule query with permission set intersection."""
        q = TERuleQuery(self.p, perms=["super_r"], perms_equal=False)

        # manually consume the generator:
        r = sorted(q.results())
        self.assertEqual(len(r), 2)

        # verify first rule
        self.assertEqual(r[0].ruletype, "allow")
        self.assertEqual(r[0].source, "test12a")
        self.assertEqual(r[0].target, "test12a")
        self.assertEqual(r[0].tclass, "infoflow7")
        self.assertSetEqual(set(["super_r"]), r[0].perms)
        self.assertRaises(RuleNotConditional, getattr, r[0], "conditional")

        # verify second rule
        self.assertEqual(r[1].ruletype, "allow")
        self.assertEqual(r[1].source, "test12b")
        self.assertEqual(r[1].target, "test12b")
        self.assertEqual(r[1].tclass, "infoflow7")
        self.assertSetEqual(set(["super_r", "super_none"]), r[1].perms)
        self.assertRaises(RuleNotConditional, getattr, r[1], "conditional")

    def test_013_perms_equal(self):
        """TE rule query with permission set equality."""
        q = TERuleQuery(
            self.p, perms=["super_w", "super_none", "super_both"], perms_equal=True)

        # manually consume the generator:
        rules = q.results()
        r = rules.next()

        self.assertEqual(r.ruletype, "allow")
        self.assertEqual(r.source, "test13c")
        self.assertEqual(r.target, "test13c")
        self.assertEqual(r.tclass, "infoflow7")
        self.assertSetEqual(
            set(["super_w", "super_none", "super_both"]), r.perms)
        self.assertRaises(RuleNotConditional, getattr, r, "conditional")

        self.assertRaises(StopIteration, rules.next)

    def test_014_ruletype(self):
        """TE rule query with rule type match."""
        q = TERuleQuery(self.p, ruletype=["auditallow", "dontaudit"])

        # manually consume the generator:
        r = sorted(q.results())
        self.assertEqual(len(r), 2)

        # verify first rule
        self.assertEqual(r[0].ruletype, "auditallow")
        self.assertEqual(r[0].source, "test14")
        self.assertEqual(r[0].target, "test14")
        self.assertEqual(r[0].tclass, "infoflow7")
        self.assertSetEqual(set(["super_both"]), r[0].perms)
        self.assertRaises(RuleNotConditional, getattr, r[0], "conditional")

        # verify second rule
        self.assertEqual(r[1].ruletype, "dontaudit")
        self.assertEqual(r[1].source, "test14")
        self.assertEqual(r[1].target, "test14")
        self.assertEqual(r[1].tclass, "infoflow7")
        self.assertSetEqual(set(["super_unmapped"]), r[1].perms)
        self.assertRaises(RuleNotConditional, getattr, r[1], "conditional")

    def test_100_default(self):
        """TE rule query with default type exact match."""
        q = TERuleQuery(self.p, default="test100d", default_regex=False)

        # manually consume the generator:
        rules = q.results()
        r = rules.next()

        self.assertEqual(r.ruletype, "type_transition")
        self.assertEqual(r.source, "test100")
        self.assertEqual(r.target, "test100")
        self.assertEqual(r.tclass, "infoflow7")
        self.assertEqual(r.default, "test100d")
        self.assertRaises(RuleNotConditional, getattr, r, "conditional")

        self.assertRaises(StopIteration, rules.next)

    def test_101_default_regex(self):
        """TE rule query with default type regex match."""
        q = TERuleQuery(self.p, default="test101.", default_regex=True)

        # manually consume the generator:
        r = sorted(q.results())
        self.assertEqual(len(r), 2)

        # verify first rule
        self.assertEqual(r[0].ruletype, "type_transition")
        self.assertEqual(r[0].source, "test101")
        self.assertEqual(r[0].target, "test101d")
        self.assertEqual(r[0].tclass, "infoflow7")
        self.assertEqual(r[0].default, "test101e")
        self.assertRaises(RuleNotConditional, getattr, r[0], "conditional")

        # verify second rule
        self.assertEqual(r[1].ruletype, "type_transition")
        self.assertEqual(r[1].source, "test101")
        self.assertEqual(r[1].target, "test101e")
        self.assertEqual(r[1].tclass, "infoflow7")
        self.assertEqual(r[1].default, "test101d")
        self.assertRaises(RuleNotConditional, getattr, r[1], "conditional")