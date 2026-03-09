# -*- coding: utf-8 -*-

import os
import tempfile
import shutil
import unittest
from unittest.case import SkipTest

import pytest

from src.whatthepatch import apply_diff, apply_patch, exceptions, parse_patch
from src.whatthepatch.snippets import which


def _apply(src, diff_text, reverse=False, use_patch=False):
    diff = next(parse_patch(diff_text))
    return apply_diff(diff, src, reverse, use_patch)


def _apply_r(src, diff_text, reverse=True, use_patch=False):
    return _apply(src, diff_text, reverse, use_patch)


class ApplyTestSuite(unittest.TestCase):
    """Basic test cases."""

    def setUp(self):
        with open("tests/casefiles/lao") as f:
            self.lao = f.read().splitlines()

        with open("tests/casefiles/tzu") as f:
            self.tzu = f.read().splitlines()

        with open("tests/casefiles/abc") as f:
            self.abc = f.read().splitlines()

        with open("tests/casefiles/efg") as f:
            self.efg = f.read().splitlines()

    def test_truth(self):
        self.assertEqual(type(self.lao), list)
        self.assertEqual(type(self.tzu), list)
        self.assertEqual(len(self.lao), 11)
        self.assertEqual(len(self.tzu), 13)

    def test_diff_default(self):
        with open("tests/casefiles/diff-default.diff") as f:
            diff_text = f.read()

        self.assertEqual(_apply(self.lao, diff_text), self.tzu)
        self.assertEqual(_apply_r(self.tzu, diff_text), self.lao)

    def test_diff_context(self):
        with open("tests/casefiles/diff-context.diff") as f:
            diff_text = f.read()

        self.assertEqual(_apply(self.lao, diff_text), self.tzu)
        self.assertEqual(_apply_r(self.tzu, diff_text), self.lao)

    def test_diff_unified(self):
        with open("tests/casefiles/diff-unified.diff") as f:
            diff_text = f.read()

        self.assertEqual(_apply(self.lao, diff_text), self.tzu)
        self.assertEqual(_apply_r(self.tzu, diff_text), self.lao)

    def test_diff_unified2(self):
        with open("tests/casefiles/diff-unified2.diff") as f:
            diff_text = f.read()

        self.assertEqual(_apply(self.abc, diff_text), self.efg)
        self.assertEqual(_apply_r(self.efg, diff_text), self.abc)

    def test_diff_unified_bad(self):
        with open("tests/casefiles/diff-unified-bad.diff") as f:
            diff_text = f.read()

        with pytest.raises(exceptions.ApplyException) as ec:
            _apply(self.lao, diff_text)

        e = ec.value
        e_str = str(e)
        assert "line 4" in e_str
        assert "The Named is the mother of all tings." in e_str
        assert "The Named is the mother of all things." in e_str
        assert e.hunk == 1

    def test_diff_unified_bad2(self):
        with open("tests/casefiles/diff-unified-bad2.diff") as f:
            diff_text = f.read()

        with pytest.raises(exceptions.ApplyException) as ec:
            _apply(self.lao, diff_text)

        e = ec.value
        e_str = str(e)
        assert "line 9" in e_str
        assert "The two are te same," in e_str
        assert "The two are the same," in e_str
        assert e.hunk == 2

    def test_diff_unified_bad_backward(self):
        with open("tests/casefiles/diff-unified-bad2.diff") as f:
            diff_text = f.read()

        with pytest.raises(exceptions.ApplyException) as ec:
            _apply(self.tzu, diff_text)

        e = ec.value
        e_str = str(e)
        assert "line 1" in e_str
        assert "The Way that can be told of is not the eternal Way;" in e_str
        assert "The Nameless is the origin of Heaven and Earth;" in e_str
        assert e.hunk == 1

    def test_diff_unified_bad_empty_source(self):
        with open("tests/casefiles/diff-unified-bad2.diff") as f:
            diff_text = f.read()

        with pytest.raises(exceptions.ApplyException) as ec:
            _apply("", diff_text)

        e = ec.value
        e_str = str(e)
        assert "line 1" in e_str
        assert "The Way that can be told of is not the eternal Way;" in e_str
        assert "does not exist in source"
        assert e.hunk == 1

    def test_diff_unified_patchutil(self):
        with open("tests/casefiles/diff-unified.diff") as f:
            diff_text = f.read()

        if not which("patch"):
            raise SkipTest()

        self.assertEqual(_apply(self.lao, diff_text, use_patch=True), (self.tzu, None))
        self.assertEqual(
            _apply_r(self.tzu, diff_text, use_patch=True), (self.lao, None)
        )

        new_text = _apply(self.lao, diff_text, use_patch=True)
        self.assertEqual(new_text, (self.tzu, None))

        with pytest.raises(exceptions.ApplyException):
            _apply([""] + self.lao, diff_text, use_patch=True)

    def test_diff_unified2_patchutil(self):
        with open("tests/casefiles/diff-unified2.diff") as f:
            diff_text = f.read()

        if not which("patch"):
            raise SkipTest()

        self.assertEqual(_apply(self.abc, diff_text, use_patch=True), (self.efg, None))
        self.assertEqual(
            _apply(self.abc, diff_text, use_patch=True),
            (_apply(self.abc, diff_text), None),
        )
        self.assertEqual(
            _apply_r(self.efg, diff_text, use_patch=True), (self.abc, None)
        )
        self.assertEqual(
            _apply_r(self.efg, diff_text, use_patch=True),
            (_apply_r(self.efg, diff_text), None),
        )

    def test_diff_rcs(self):
        with open("tests/casefiles/diff-rcs.diff") as f:
            diff_text = f.read()

        new_text = _apply(self.lao, diff_text)

        self.assertEqual(new_text, self.tzu)

    def test_diff_ed(self):
        with open("tests/casefiles/diff-ed.diff") as f:
            diff_text = f.read()

        new_text = _apply(self.lao, diff_text)
        self.assertEqual(self.tzu, new_text)

    def _subtest_git_oneline_add(self, use_patch):
        with open('tests/casefiles/git-oneline-add.diff') as f:
            diff_text = f.read()

        actual = _apply([], diff_text, use_patch=use_patch)
        if use_patch:
            new_text, rejlines = actual
            self.assertIsNone(rejlines)
        else:
            new_text = actual
        self.assertEqual(['Adding a one-line file.'], new_text)

    def _subtest_git_oneline_change(self, use_patch):
        with open('tests/casefiles/git-oneline-change.diff') as f:
            diff_text = f.read()

        actual = _apply(['Adding a one-line file.'], diff_text,
                        use_patch=use_patch)
        if use_patch:
            new_text, rejlines = actual
            self.assertIsNone(rejlines)
        else:
            new_text = actual
        self.assertEqual(['Changed a one-line file.'], new_text)

    def _subtest_git_oneline_rm(self, use_patch):
        with open('tests/casefiles/git-oneline-rm.diff') as f:
            diff_text = f.read()

        actual = _apply(['Changed a one-line file.'], diff_text,
                        use_patch=use_patch)
        if use_patch:
            new_text, rejlines = actual
            self.assertIsNone(rejlines)
        else:
            new_text = actual
        self.assertEqual([], new_text)


    def test_git(self):
        for use_patch in (False, True):
            with self.subTest('git-oneline-add', use_patch=use_patch):
                self._subtest_git_oneline_add(use_patch)
            with self.subTest('git-oneline-change', use_patch=use_patch):
                self._subtest_git_oneline_change(use_patch)
            with self.subTest('git-oneline-rm', use_patch=use_patch):
                self._subtest_git_oneline_rm(use_patch)


class ApplyPatchTestSuite(unittest.TestCase):
    def setUp(self):
        with open("tests/casefiles/git.patch") as f:
            self.git_patch = parse_patch(f.read())
        with open("tests/casefiles/git-oneline-add.diff") as f:
            self.git_oneline_add = parse_patch(f.read())
        with open("tests/casefiles/git-oneline-change.diff") as f:
            self.git_oneline_chg = parse_patch(f.read())
        self.old_cwd = os.getcwd()
        self.new_cwd = tempfile.mkdtemp()
        os.chdir(self.new_cwd)
        return super().setUp()

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.new_cwd)
        return super().tearDown()

    def test_no_diffs(self):
        with self.subTest(""):
            apply_patch([])

        with self.subTest(""):
            apply_patch([], reverse=True)

        with self.subTest(""):
            apply_patch([], use_patch=True)

        with self.subTest(""):
            apply_patch([], strip=4)

        with self.subTest(""):
            apply_patch([], strip=4, use_patch=True)

        with self.subTest(""):
            apply_patch([], reverse=True, strip=4, use_patch=True)

    def _subtest_git_oneline_add(self, use_patch=False):
        path = os.path.join(self.new_cwd, "oneline.txt")
        expected = "Adding a one-line file."

        if os.path.exists(path):
            os.remove(path)

        apply_patch(self.git_oneline_add, directory=self.new_cwd,
                    use_patch=use_patch)

        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            actual = f.read()
        self.assertEqual(expected, actual)

    def test_git_oneline_add(self):
        with self.subTest("w/o patch"):
            self._subtest_git_oneline_add()

        # fails with:
        ## The next patch would create the file /tmp/wtp-...
        ## which already exists!  Skipping patch.
        ## patch unexpectedly ends in middle of line
        ## patch: **** malformed patch at line 6:
        # with self.subTest("w/ patch"):
        #     self._subtest_git_oneline_add(use_patch=True)

    def _subtest_git_oneline_chg(self, use_patch=False):
        path = os.path.join(self.new_cwd, "oneline.txt")
        expected = "Changed a one-line file."

        if os.path.exists(path):
            os.remove(path)
        with open(path, "w") as f:
            f.write("Adding a one-line file.")

        apply_patch(self.git_oneline_chg, directory=self.new_cwd,
                    use_patch=use_patch)

        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            actual = f.read()
        self.assertEqual(expected, actual)

    def test_git_oneline_chg(self):
        with self.subTest("w/o patch"):
            self._subtest_git_oneline_chg()

        # fails with:
        ## TODO: investigate
        # with self.subTest("w/ patch"):
        #     self._subtest_git_oneline_chg(use_patch=True)


if __name__ == "__main__":
    unittest.main()
