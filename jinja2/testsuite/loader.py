# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.loader
    ~~~~~~~~~~~~~~~~~~~~~~~

    Test the loaders.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import time
import tempfile
import unittest

from jinja2.testsuite import JinjaTestCase, dict_loader, \
     package_loader, filesystem_loader, function_loader, \
     choice_loader, prefix_loader

from jinja2 import Environment, loaders
from jinja2.loaders import split_template_path
from jinja2.exceptions import TemplateNotFound


class LoaderTestCase(JinjaTestCase):

    def test_dict_loader(self):
        env = Environment(loader=dict_loader)
        tmpl = env.get_template('justdict.html')
        assert tmpl.render().strip() == 'FOO'
        self.assert_raises(TemplateNotFound, env.get_template, 'missing.html')

    def test_package_loader(self):
        env = Environment(loader=package_loader)
        tmpl = env.get_template('test.html')
        assert tmpl.render().strip() == 'BAR'
        self.assert_raises(TemplateNotFound, env.get_template, 'missing.html')

    def test_filesystem_loader(self):
        env = Environment(loader=filesystem_loader)
        tmpl = env.get_template('test.html')
        assert tmpl.render().strip() == 'BAR'
        tmpl = env.get_template('foo/test.html')
        assert tmpl.render().strip() == 'FOO'
        self.assert_raises(TemplateNotFound, env.get_template, 'missing.html')

    def test_choice_loader(self):
        env = Environment(loader=choice_loader)
        tmpl = env.get_template('justdict.html')
        assert tmpl.render().strip() == 'FOO'
        tmpl = env.get_template('test.html')
        assert tmpl.render().strip() == 'BAR'
        self.assert_raises(TemplateNotFound, env.get_template, 'missing.html')

    def test_function_loader(self):
        env = Environment(loader=function_loader)
        tmpl = env.get_template('justfunction.html')
        assert tmpl.render().strip() == 'FOO'
        self.assert_raises(TemplateNotFound, env.get_template, 'missing.html')

    def test_prefix_loader(self):
        env = Environment(loader=prefix_loader)
        tmpl = env.get_template('a/test.html')
        assert tmpl.render().strip() == 'BAR'
        tmpl = env.get_template('b/justdict.html')
        assert tmpl.render().strip() == 'FOO'
        self.assert_raises(TemplateNotFound, env.get_template, 'missing')

    def test_caching(self):
        changed = False
        class TestLoader(loaders.BaseLoader):
            def get_source(self, environment, template):
                return u'foo', None, lambda: not changed
        env = Environment(loader=TestLoader(), cache_size=-1)
        tmpl = env.get_template('template')
        assert tmpl is env.get_template('template')
        changed = True
        assert tmpl is not env.get_template('template')
        changed = False

        env = Environment(loader=TestLoader(), cache_size=0)
        assert env.get_template('template') \
               is not env.get_template('template')

        env = Environment(loader=TestLoader(), cache_size=2)
        t1 = env.get_template('one')
        t2 = env.get_template('two')
        assert t2 is env.get_template('two')
        assert t1 is env.get_template('one')
        t3 = env.get_template('three')
        assert 'one' in env.cache
        assert 'two' not in env.cache
        assert 'three' in env.cache

    def test_split_template_path(self):
        assert split_template_path('foo/bar') == ['foo', 'bar']
        assert split_template_path('./foo/bar') == ['foo', 'bar']
        self.assert_raises(TemplateNotFound, split_template_path, '../foo')


class ModuleLoaderTestCase(JinjaTestCase):
    archive = None

    def setup(self):
        super(ModuleLoaderTestCase, self).setup()
        self.reg_env = Environment(loader=prefix_loader)
        self.archive = tempfile.mkstemp(suffix='.zip')[1]
        self.reg_env.compile_templates(self.archive)
        self.mod_env = Environment(loader=loaders.ModuleLoader(self.archive))

    def teardown(self):
        super(ModuleLoaderTestCase, self).teardown()
        os.remove(self.archive)
        self.archive = None

    def test_module_loader(self):
        tmpl1 = self.reg_env.get_template('a/test.html')
        tmpl2 = self.mod_env.get_template('a/test.html')
        assert tmpl1.render() == tmpl2.render()

        tmpl1 = self.reg_env.get_template('b/justdict.html')
        tmpl2 = self.mod_env.get_template('b/justdict.html')
        assert tmpl1.render() == tmpl2.render()

    def test_weak_references(self):
        tmpl = self.mod_env.get_template('a/test.html')
        key = loaders.ModuleLoader.get_template_key('a/test.html')
        name = self.mod_env.loader.module.__name__

        assert hasattr(self.mod_env.loader.module, key)
        assert name in sys.modules

        # unset all, ensure the module is gone from sys.modules
        self.mod_env = tmpl = None

        try:
            import gc
            gc.collect()
        except:
            pass

        assert name not in sys.modules


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LoaderTestCase))
    suite.addTest(unittest.makeSuite(ModuleLoaderTestCase))
    return suite
