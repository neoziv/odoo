# -*- coding: utf-8 -*-
# Part of neoziv. See LICENSE file for full copyright and licensing details.

import ast
import collections.abc
import importlib
import logging
import os
import pkg_resources
import re
import sys
import warnings
from os.path import join as opj

import neoziv
import neoziv.tools as tools
import neoziv.release as release
from neoziv.tools import pycompat

MANIFEST_NAMES = ('__manifest__.py', '__openerp__.py')
README = ['README.rst', 'README.md', 'README.txt']

_logger = logging.getLogger(__name__)

# addons path as a list
# ad_paths is a deprecated alias, please use neoziv.addons.__path__
@tools.lazy
def ad_paths():
    warnings.warn(
        '"neoziv.modules.module.ad_paths" is a deprecated proxy to '
        '"neoziv.addons.__path__".', DeprecationWarning, stacklevel=2)
    return neoziv.addons.__path__

# Modules already loaded
loaded = []

class AddonsHook(object):
    """ Makes modules accessible through openerp.addons.* """

    def find_module(self, name, path=None):
        if name.startswith('openerp.addons.') and name.count('.') == 2:
            warnings.warn(
                '"openerp.addons" is a deprecated alias to "neoziv.addons".',
                DeprecationWarning, stacklevel=2)
            return self

    def load_module(self, name):
        assert name not in sys.modules

        neoziv_name = re.sub(r'^openerp.addons.(\w+)$', r'neoziv.addons.\g<1>', name)

        neoziv_module = sys.modules.get(neoziv_name)
        if not neoziv_module:
            neoziv_module = importlib.import_module(neoziv_name)

        sys.modules[name] = neoziv_module

        return neoziv_module

class neozivHook(object):
    """ Makes neoziv package also available as openerp """

    def find_module(self, name, path=None):
        # openerp.addons.<identifier> should already be matched by AddonsHook,
        # only framework and subdirectories of modules should match
        if re.match(r'^openerp\b', name):
            warnings.warn(
                'openerp is a deprecated alias to neoziv.',
                DeprecationWarning, stacklevel=2)
            return self

    def load_module(self, name):
        assert name not in sys.modules

        canonical = re.sub(r'^openerp(.*)', r'neoziv\g<1>', name)

        if canonical in sys.modules:
            mod = sys.modules[canonical]
        else:
            # probable failure: canonical execution calling old naming -> corecursion
            mod = importlib.import_module(canonical)

        # just set the original module at the new location. Don't proxy,
        # it breaks *-import (unless you can find how `from a import *` lists
        # what's supposed to be imported by `*`, and manage to override it)
        sys.modules[name] = mod

        return sys.modules[name]


class UpgradeHook(object):
    """Makes the legacy `migrations` package being `neoziv.upgrade`"""

    def find_module(self, name, path=None):
        if re.match(r"^neoziv.addons.base.maintenance.migrations\b", name):
            # We can't trigger a DeprecationWarning in this case.
            # In order to be cross-versions, the multi-versions upgrade scripts (0.0.0 scripts),
            # the tests, and the common files (utility functions) still needs to import from the
            # legacy name.
            return self

    def load_module(self, name):
        assert name not in sys.modules

        canonical_upgrade = name.replace("neoziv.addons.base.maintenance.migrations", "neoziv.upgrade")

        if canonical_upgrade in sys.modules:
            mod = sys.modules[canonical_upgrade]
        else:
            mod = importlib.import_module(canonical_upgrade)

        sys.modules[name] = mod

        return sys.modules[name]


def initialize_sys_path():
    """
    Setup the addons path ``neoziv.addons.__path__`` with various defaults
    and explicit directories.
    """
    # hook neoziv.addons on data dir
    dd = os.path.normcase(tools.config.addons_data_dir)
    if os.access(dd, os.R_OK) and dd not in neoziv.addons.__path__:
        neoziv.addons.__path__.append(dd)

    # hook neoziv.addons on addons paths
    for ad in tools.config['addons_path'].split(','):
        ad = os.path.normcase(os.path.abspath(tools.ustr(ad.strip())))
        if ad not in neoziv.addons.__path__:
            neoziv.addons.__path__.append(ad)

    # hook neoziv.addons on base module path
    base_path = os.path.normcase(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'addons')))
    if base_path not in neoziv.addons.__path__ and os.path.isdir(base_path):
        neoziv.addons.__path__.append(base_path)

    # hook neoziv.upgrade on upgrade-path
    from neoziv import upgrade
    legacy_upgrade_path = os.path.join(base_path, 'base', 'maintenance', 'migrations')
    for up in (tools.config['upgrade_path'] or legacy_upgrade_path).split(','):
        up = os.path.normcase(os.path.abspath(tools.ustr(up.strip())))
        if up not in upgrade.__path__:
            upgrade.__path__.append(up)

    # create decrecated module alias from neoziv.addons.base.maintenance.migrations to neoziv.upgrade
    spec = importlib.machinery.ModuleSpec("neoziv.addons.base.maintenance", None, is_package=True)
    maintenance_pkg = importlib.util.module_from_spec(spec)
    maintenance_pkg.migrations = upgrade
    sys.modules["neoziv.addons.base.maintenance"] = maintenance_pkg
    sys.modules["neoziv.addons.base.maintenance.migrations"] = upgrade

    # hook deprecated module alias from openerp to neoziv and "crm"-like to neoziv.addons
    if not getattr(initialize_sys_path, 'called', False): # only initialize once
        sys.meta_path.insert(0, UpgradeHook())
        sys.meta_path.insert(0, neozivHook())
        sys.meta_path.insert(0, AddonsHook())
        initialize_sys_path.called = True


def get_module_path(module, downloaded=False, display_warning=True):
    """Return the path of the given module.

    Search the addons paths and return the first path where the given
    module is found. If downloaded is True, return the default addons
    path if nothing else is found.

    """
    for adp in neoziv.addons.__path__:
        files = [opj(adp, module, manifest) for manifest in MANIFEST_NAMES] +\
                [opj(adp, module + '.zip')]
        if any(os.path.exists(f) for f in files):
            return opj(adp, module)

    if downloaded:
        return opj(tools.config.addons_data_dir, module)
    if display_warning:
        _logger.warning('module %s: module not found', module)
    return False

def get_module_filetree(module, dir='.'):
    path = get_module_path(module)
    if not path:
        return False

    dir = os.path.normpath(dir)
    if dir == '.':
        dir = ''
    if dir.startswith('..') or (dir and dir[0] == '/'):
        raise Exception('Cannot access file outside the module')

    files = neoziv.tools.osutil.listdir(path, True)

    tree = {}
    for f in files:
        if not f.startswith(dir):
            continue

        if dir:
            f = f[len(dir)+int(not dir.endswith('/')):]
        lst = f.split(os.sep)
        current = tree
        while len(lst) != 1:
            current = current.setdefault(lst.pop(0), {})
        current[lst.pop(0)] = None

    return tree

def get_resource_path(module, *args):
    """Return the full path of a resource of the given module.

    :param module: module name
    :param list(str) args: resource path components within module

    :rtype: str
    :return: absolute path to the resource

    TODO make it available inside on osv object (self.get_resource_path)
    """
    mod_path = get_module_path(module)
    if not mod_path: return False
    resource_path = opj(mod_path, *args)
    if os.path.isdir(mod_path):
        # the module is a directory - ignore zip behavior
        if os.path.exists(resource_path):
            return resource_path
    return False

# backwards compatibility
get_module_resource = get_resource_path

def get_resource_from_path(path):
    """Tries to extract the module name and the resource's relative path
    out of an absolute resource path.

    If operation is successfull, returns a tuple containing the module name, the relative path
    to the resource using '/' as filesystem seperator[1] and the same relative path using
    os.path.sep seperators.

    [1] same convention as the resource path declaration in manifests

    :param path: absolute resource path

    :rtype: tuple
    :return: tuple(module_name, relative_path, os_relative_path) if possible, else None
    """
    resource = False
    for adpath in neoziv.addons.__path__:
        # force trailing separator
        adpath = os.path.join(adpath, "")
        if os.path.commonprefix([adpath, path]) == adpath:
            resource = path.replace(adpath, "", 1)
            break

    if resource:
        relative = resource.split(os.path.sep)
        if not relative[0]:
            relative.pop(0)
        module = relative.pop(0)
        return (module, '/'.join(relative), os.path.sep.join(relative))
    return None

def get_module_icon(module):
    iconpath = ['static', 'description', 'icon.png']
    if get_module_resource(module, *iconpath):
        return ('/' + module + '/') + '/'.join(iconpath)
    return '/base/'  + '/'.join(iconpath)

def module_manifest(path):
    """Returns path to module manifest if one can be found under `path`, else `None`."""
    if not path:
        return None
    for manifest_name in MANIFEST_NAMES:
        if os.path.isfile(opj(path, manifest_name)):
            return opj(path, manifest_name)

def get_module_root(path):
    """
    Get closest module's root beginning from path

        # Given:
        # /foo/bar/module_dir/static/src/...

        get_module_root('/foo/bar/module_dir/static/')
        # returns '/foo/bar/module_dir'

        get_module_root('/foo/bar/module_dir/')
        # returns '/foo/bar/module_dir'

        get_module_root('/foo/bar')
        # returns None

    @param path: Path from which the lookup should start

    @return:  Module root path or None if not found
    """
    while not module_manifest(path):
        new_path = os.path.abspath(opj(path, os.pardir))
        if path == new_path:
            return None
        path = new_path
    return path

def load_information_from_description_file(module, mod_path=None):
    """
    :param module: The name of the module (sale, purchase, ...)
    :param mod_path: Physical path of module, if not providedThe name of the module (sale, purchase, ...)
    """
    if not mod_path:
        mod_path = get_module_path(module, downloaded=True)
    manifest_file = module_manifest(mod_path)
    if manifest_file:
        # default values for descriptor
        info = {
            'application': False,
            'author': 'neoziv S.A.',
            'auto_install': False,
            'category': 'Uncategorized',
            'depends': [],
            'description': '',
            'icon': get_module_icon(module),
            'installable': True,
            'license': 'LGPL-3',
            'post_load': None,
            'version': '1.0',
            'web': False,
            'sequence': 100,
            'summary': '',
            'website': '',
        }
        info.update(zip(
            'depends data demo test init_xml update_xml demo_xml'.split(),
            iter(list, None)))

        f = tools.file_open(manifest_file, mode='rb')
        try:
            info.update(ast.literal_eval(pycompat.to_text(f.read())))
        finally:
            f.close()

        if not info.get('description'):
            readme_path = [opj(mod_path, x) for x in README
                           if os.path.isfile(opj(mod_path, x))]
            if readme_path:
                with tools.file_open(readme_path[0]) as fd:
                    info['description'] = fd.read()

        # auto_install is set to `False` if disabled, and a set of
        # auto_install dependencies otherwise. That way, we can set
        # auto_install: [] to always auto_install a module regardless of its
        # dependencies
        auto_install = info.get('auto_install', info.get('active', False))
        if isinstance(auto_install, collections.abc.Iterable):
            info['auto_install'] = set(auto_install)
            non_dependencies = info['auto_install'].difference(info['depends'])
            assert not non_dependencies,\
                "auto_install triggers must be dependencies, found " \
                "non-dependencies [%s] for module %s" % (
                    ', '.join(non_dependencies), module
                )
        elif auto_install:
            info['auto_install'] = set(info['depends'])
        else:
            info['auto_install'] = False

        info['version'] = adapt_version(info['version'])
        return info

    _logger.debug('module %s: no manifest file found %s', module, MANIFEST_NAMES)
    return {}

def load_openerp_module(module_name):
    """ Load an OpenERP module, if not already loaded.

    This loads the module and register all of its models, thanks to either
    the MetaModel metaclass, or the explicit instantiation of the model.
    This is also used to load server-wide module (i.e. it is also used
    when there is no model to register).
    """
    global loaded
    if module_name in loaded:
        return

    try:
        __import__('neoziv.addons.' + module_name)

        # Call the module's post-load hook. This can done before any model or
        # data has been initialized. This is ok as the post-load hook is for
        # server-wide (instead of registry-specific) functionalities.
        info = load_information_from_description_file(module_name)
        if info['post_load']:
            getattr(sys.modules['neoziv.addons.' + module_name], info['post_load'])()

    except Exception as e:
        msg = "Couldn't load module %s" % (module_name)
        _logger.critical(msg)
        _logger.critical(e)
        raise
    else:
        loaded.append(module_name)

def get_modules():
    """Returns the list of module names
    """
    def listdir(dir):
        def clean(name):
            name = os.path.basename(name)
            if name[-4:] == '.zip':
                name = name[:-4]
            return name

        def is_really_module(name):
            for mname in MANIFEST_NAMES:
                if os.path.isfile(opj(dir, name, mname)):
                    return True
        return [
            clean(it)
            for it in os.listdir(dir)
            if is_really_module(it)
        ]

    plist = []
    for ad in neoziv.addons.__path__:
        plist.extend(listdir(ad))
    return list(set(plist))

def get_modules_with_version():
    modules = get_modules()
    res = dict.fromkeys(modules, adapt_version('1.0'))
    for module in modules:
        try:
            info = load_information_from_description_file(module)
            res[module] = info['version']
        except Exception:
            continue
    return res

def adapt_version(version):
    serie = release.major_version
    if version == serie or not version.startswith(serie + '.'):
        version = '%s.%s' % (serie, version)
    return version

current_test = None
